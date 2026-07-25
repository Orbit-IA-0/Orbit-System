"""Endpoints de perfil e configuracoes do usuario (tema, idioma, modelo preferido)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/api/users", tags=["users"])


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    theme: str | None = None            # "dark" | "light"
    language: str | None = None         # ex: "pt-BR", "en-US"
    preferred_model: str | None = None


@router.patch("/me")
async def update_profile(payload: UpdateProfileRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.theme is not None:
        user.theme = payload.theme
    if payload.language is not None:
        user.language = payload.language
    if payload.preferred_model is not None:
        user.preferred_model = payload.preferred_model
    await db.commit()
    await db.refresh(user)
    return {
        "id": user.id, "full_name": user.full_name, "theme": user.theme,
        "language": user.language, "preferred_model": user.preferred_model,
    }
