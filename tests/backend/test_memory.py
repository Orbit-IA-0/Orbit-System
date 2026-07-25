"""Testes do endpoint de memoria persistente do usuario."""
import uuid

import pytest


async def _register_and_get_token(client) -> str:
    email = f"user_{uuid.uuid4().hex[:8]}@teste.com"
    resp = await client.post("/api/auth/register", json={"email": email, "password": "SenhaForte123!"})
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_write_and_read_memory(client):
    token = await _register_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    write_resp = await client.post("/api/memory", json={"key": "linguagem_preferida", "value": "Python"}, headers=headers)
    assert write_resp.status_code == 200

    read_resp = await client.get("/api/memory", headers=headers)
    facts = read_resp.json()["facts"]
    assert any(f["key"] == "linguagem_preferida" and f["value"] == "Python" for f in facts)


@pytest.mark.asyncio
async def test_delete_memory(client):
    token = await _register_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/api/memory", json={"key": "cor_favorita", "value": "roxo"}, headers=headers)

    delete_resp = await client.delete("/api/memory/cor_favorita", headers=headers)
    assert delete_resp.json()["deleted"] is True
