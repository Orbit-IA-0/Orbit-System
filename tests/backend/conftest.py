"""
Configuracao do pytest para os testes da Orbit AI API.
Usa um banco Postgres de teste (definido via variavel de ambiente TEST_DATABASE_URL)
e cria/derruba as tabelas a cada sessao de testes, garantindo isolamento.
"""
import asyncio
import os
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://orbit:orbit@localhost:5432/orbit_ia_test"),
)


@pytest_asyncio.fixture
async def client():
    from app.database import init_db
    from app.main import app

    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
