"""
Ponto de entrada da Orbit AI API (FastAPI).
Registra todos os routers, middlewares (CORS, sessao para OAuth) e cuida
da inicializacao do banco de dados e da semente de dados (primeira versao,
primeiro usuario admin) ao subir a aplicacao.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api import admin, chat, conversations, files, memory, search, system, users
from app.auth import routes as auth_routes
from app.config import get_settings
from app.database import AsyncSessionLocal, init_db
from app.plugins.registry_setup import setup_plugins

settings = get_settings()


async def _seed_initial_data():
    """Garante que exista ao menos uma versao registrada e um admin padrao em dev."""
    from sqlalchemy import select
    from app.auth.security import hash_password
    from app.models import AppVersion, User

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AppVersion))
        if not result.scalars().first():
            db.add(AppVersion(
                version=settings.APP_VERSION,
                changelog="Lancamento inicial da Orbit IA: chat com streaming, memoria, "
                          "plugins, upload de documentos, busca na web e painel administrativo.",
            ))

        if settings.ENVIRONMENT == "development":
            admin_result = await db.execute(select(User).where(User.email == "admin@orbit.ia"))
            if not admin_result.scalar_one_or_none():
                db.add(User(
                    email="admin@orbit.ia",
                    hashed_password=hash_password("OrbitAdmin123!"),
                    full_name="Administrador Orbit IA",
                    is_admin=True,
                ))
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    setup_plugins()
    await _seed_initial_data()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API propria da Orbit IA: autenticacao, chat com streaming, memoria persistente, "
        "plugins/tools, upload e indexacao de documentos (RAG), busca na web e painel "
        "administrativo. Todo o front-end se comunica exclusivamente atraves desta API."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)

app.include_router(auth_routes.router)
app.include_router(chat.router)
app.include_router(memory.router)
app.include_router(search.router)
app.include_router(files.router)
app.include_router(conversations.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(system.router)
