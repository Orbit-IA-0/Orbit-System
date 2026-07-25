"""Testes do fluxo de autenticacao: cadastro, login e acesso a rota protegida."""
import uuid

import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    email = f"user_{uuid.uuid4().hex[:8]}@teste.com"
    password = "SenhaForte123!"

    register_resp = await client.post("/api/auth/register", json={"email": email, "password": password})
    assert register_resp.status_code == 201
    tokens = register_resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    login_resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_resp.status_code == 200

    me_resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email


@pytest.mark.asyncio
async def test_login_with_wrong_password(client):
    email = f"user_{uuid.uuid4().hex[:8]}@teste.com"
    await client.post("/api/auth/register", json={"email": email, "password": "SenhaCorreta123"})

    resp = await client.post("/api/auth/login", json={"email": email, "password": "SenhaErrada"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_access_without_token_is_rejected(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401
