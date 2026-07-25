"""Endpoints REST de memoria: POST /api/memory (ler/gravar) e DELETE por chave."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.database import get_db
from app.memory.service import delete_fact, list_facts, upsert_fact
from app.models import User

router = APIRouter(prefix="/api/memory", tags=["memory"])


class MemoryWriteRequest(BaseModel):
    key: str
    value: str


@router.get("")
async def get_memory(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    facts = await list_facts(db, user.id)
    return {"facts": [{"key": f.key, "value": f.value, "updated_at": f.updated_at} for f in facts]}


@router.post("")
async def write_memory(
    payload: MemoryWriteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fact = await upsert_fact(db, user.id, payload.key, payload.value, source="api")
    return {"key": fact.key, "value": fact.value}


@router.delete("/{key}")
async def remove_memory(key: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    deleted = await delete_fact(db, user.id, key)
    return {"deleted": deleted}
