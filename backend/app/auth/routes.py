"""
Rotas de autenticacao: cadastro, login (email+senha), refresh de token,
logout e login social (Google/GitHub).
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.oauth import oauth
from app.auth.security import (
    create_access_token, generate_refresh_token, hash_password,
    hash_refresh_token, refresh_token_expiry, verify_password,
)
from app.config import get_settings
from app.database import get_db
from app.models import OAuthAccount, RefreshToken, User

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


async def _issue_tokens(db: AsyncSession, user: User) -> TokenResponse:
    access_token = create_access_token(user.id, user.is_admin)
    raw_refresh = generate_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=refresh_token_expiry(),
    ))
    await db.commit()
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ja existe uma conta com este e-mail")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return await _issue_tokens(db, user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Conta desativada")
    return await _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()
    if not stored or stored.revoked or stored.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token invalido ou expirado")

    stored.revoked = True  # rotacao de refresh token

    user_result = await db.execute(select(User).where(User.id == stored.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario invalido")

    await db.commit()
    return await _issue_tokens(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()
    if stored:
        stored.revoked = True
        await db.commit()


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "is_admin": user.is_admin,
        "theme": user.theme,
        "language": user.language,
        "preferred_model": user.preferred_model,
    }


# ---------------------------------------------------------------------------
# OAuth2 social login (Google / GitHub)
# ---------------------------------------------------------------------------

@router.get("/oauth/{provider}/login")
async def oauth_login(provider: str, request: Request):
    if provider not in ("google", "github"):
        raise HTTPException(status_code=404, detail="Provedor OAuth desconhecido")
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE_URL}/api/auth/oauth/{provider}/callback"
    client = oauth.create_client(provider)
    return await client.authorize_redirect(request, redirect_uri)


async def _get_or_create_oauth_user(db: AsyncSession, provider: str, provider_account_id: str,
                                     email: str, full_name: str | None, avatar_url: str | None) -> User:
    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_account_id == provider_account_id,
        )
    )
    oauth_account = result.scalar_one_or_none()
    if oauth_account:
        user_result = await db.execute(select(User).where(User.id == oauth_account.user_id))
        return user_result.scalar_one()

    # Tenta associar a um usuario existente com o mesmo e-mail
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    if not user:
        user = User(email=email, full_name=full_name, avatar_url=avatar_url, hashed_password=None)
        db.add(user)
        await db.flush()

    db.add(OAuthAccount(user_id=user.id, provider=provider, provider_account_id=provider_account_id))
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/oauth/google/callback")
async def oauth_google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    client = oauth.create_client("google")
    token = await client.authorize_access_token(request)
    userinfo = token.get("userinfo") or await client.userinfo(token=token)

    user = await _get_or_create_oauth_user(
        db, "google", userinfo["sub"], userinfo["email"],
        userinfo.get("name"), userinfo.get("picture"),
    )
    tokens = await _issue_tokens(db, user)
    frontend_url = settings.OAUTH_REDIRECT_BASE_URL.replace(":8000", ":3000")
    return RedirectResponse(
        f"{frontend_url}/oauth/callback?access_token={tokens.access_token}&refresh_token={tokens.refresh_token}"
    )


@router.get("/oauth/github/callback")
async def oauth_github_callback(request: Request, db: AsyncSession = Depends(get_db)):
    client = oauth.create_client("github")
    token = await client.authorize_access_token(request)
    profile = (await client.get("user", token=token)).json()
    emails = (await client.get("user/emails", token=token)).json()
    primary_email = next((e["email"] for e in emails if e.get("primary")), profile.get("email"))

    user = await _get_or_create_oauth_user(
        db, "github", str(profile["id"]), primary_email,
        profile.get("name") or profile.get("login"), profile.get("avatar_url"),
    )
    tokens = await _issue_tokens(db, user)
    frontend_url = settings.OAUTH_REDIRECT_BASE_URL.replace(":8000", ":3000")
    return RedirectResponse(
        f"{frontend_url}/oauth/callback?access_token={tokens.access_token}&refresh_token={tokens.refresh_token}"
    )
