"""
Servico de memoria persistente por usuario.
Guarda fatos e preferencias (ex.: "linguagem_preferida = Python") que sao
recuperados a cada nova conversa e injetados no prompt do sistema, dando
a sensacao de continuidade entre sessoes — sem depender do provedor de IA.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MemoryFact


async def upsert_fact(db: AsyncSession, user_id: str, key: str, value: str, source: str = "chat") -> MemoryFact:
    result = await db.execute(
        select(MemoryFact).where(MemoryFact.user_id == user_id, MemoryFact.key == key)
    )
    fact = result.scalar_one_or_none()
    if fact:
        fact.value = value
        fact.source = source
    else:
        fact = MemoryFact(user_id=user_id, key=key, value=value, source=source)
        db.add(fact)
    await db.commit()
    await db.refresh(fact)
    return fact


async def list_facts(db: AsyncSession, user_id: str) -> list[MemoryFact]:
    result = await db.execute(select(MemoryFact).where(MemoryFact.user_id == user_id).order_by(MemoryFact.key))
    return list(result.scalars().all())


async def delete_fact(db: AsyncSession, user_id: str, key: str) -> bool:
    result = await db.execute(select(MemoryFact).where(MemoryFact.user_id == user_id, MemoryFact.key == key))
    fact = result.scalar_one_or_none()
    if not fact:
        return False
    await db.delete(fact)
    await db.commit()
    return True


def build_memory_prompt(facts: list[MemoryFact]) -> str:
    """Monta um bloco de texto com os fatos conhecidos, para incluir no system prompt."""
    if not facts:
        return ""
    lines = "\n".join(f"- {f.key}: {f.value}" for f in facts)
    return (
        "Fatos e preferencias conhecidas sobre este usuario (use quando relevante, "
        "nao repita desnecessariamente):\n" + lines
    )
