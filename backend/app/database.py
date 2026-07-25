"""
Camada de acesso ao banco de dados.
Usa SQLAlchemy assincrono (asyncpg) para as rotas da API e expõe uma sessão
sincrona para tarefas administrativas simples (scripts, migracoes manuais).
A extensao pgvector e habilitada automaticamente na inicializacao.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()


async def get_db():
    """Dependency do FastAPI: entrega uma sessao assincrona por requisicao."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Cria a extensao pgvector (se ainda nao existir) e todas as tabelas
    declaradas nos models. Chamado uma vez na inicializacao da API.
    """
    # Importa os models para que fiquem registrados no Base.metadata
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
