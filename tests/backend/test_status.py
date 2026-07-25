"""Testes basicos dos endpoints de status e versao (sem necessidade de autenticacao)."""
import pytest


@pytest.mark.asyncio
async def test_status_endpoint(client):
    resp = await client.get("/api/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_version_endpoint(client):
    resp = await client.get("/api/version")
    assert resp.status_code == 200
    assert "current_version" in resp.json()
