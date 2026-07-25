"""Endpoints de historico de conversas: listar, buscar, ver mensagens, renomear, apagar, exportar."""
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.database import get_db
from app.models import Conversation, Message, User

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


class RenameRequest(BaseModel):
    title: str


@router.get("")
async def list_conversations(
    q: str | None = Query(default=None, description="Busca por titulo ou conteudo das mensagens"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Conversation).where(Conversation.user_id == user.id)
    if q:
        subquery = select(Message.conversation_id).where(Message.content.ilike(f"%{q}%"))
        query = query.where(or_(Conversation.title.ilike(f"%{q}%"), Conversation.id.in_(subquery)))
    query = query.order_by(Conversation.updated_at.desc())

    result = await db.execute(query)
    conversations = result.scalars().all()
    return [
        {"id": c.id, "title": c.title, "model": c.model, "updated_at": c.updated_at, "created_at": c.created_at}
        for c in conversations
    ]


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa nao encontrada")

    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()
    return {
        "id": conversation.id,
        "title": conversation.title,
        "model": conversation.model,
        "messages": [
            {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}
            for m in messages
        ],
    }


@router.patch("/{conversation_id}")
async def rename_conversation(conversation_id: str, payload: RenameRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa nao encontrada")
    conversation.title = payload.title
    await db.commit()
    return {"id": conversation.id, "title": conversation.title}


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa nao encontrada")
    await db.delete(conversation)
    await db.commit()


@router.get("/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    format: str = Query(default="markdown", pattern="^(markdown|pdf)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversa nao encontrada")

    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    md_lines = [f"# {conversation.title}", ""]
    for m in messages:
        author = "**Voce**" if m.role == "user" else "**Orbit IA**"
        md_lines.append(f"{author}:\n\n{m.content}\n")
    markdown_text = "\n".join(md_lines)

    if format == "markdown":
        buffer = io.BytesIO(markdown_text.encode("utf-8"))
        return StreamingResponse(
            buffer, media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{conversation.title[:40]}.md"'},
        )

    # Exportacao em PDF usando reportlab (gerado sob demanda, sem dependencias externas pesadas)
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import simpleSplit

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 2 * cm
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(2 * cm, y, conversation.title[:80])
    y -= 1 * cm
    pdf.setFont("Helvetica", 10)

    for m in messages:
        author = "Voce" if m.role == "user" else "Orbit IA"
        block = f"{author}: {m.content}"
        for line in simpleSplit(block, "Helvetica", 10, width - 4 * cm):
            if y < 2 * cm:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 2 * cm
            pdf.drawString(2 * cm, y, line)
            y -= 0.5 * cm
        y -= 0.3 * cm

    pdf.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{conversation.title[:40]}.pdf"'},
    )
