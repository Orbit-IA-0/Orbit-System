"""
Endpoint principal da Orbit AI API: POST /api/chat.
Recebe a mensagem do usuario, monta o contexto (memoria + RAG de documentos),
transmite a resposta da IA via Server-Sent Events (SSE) e executa plugins
(function calling) quando o modelo solicita, devolvendo o resultado ao modelo
para que ele finalize a resposta.
"""
import json
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_client import ai_client, estimate_cost
from app.auth.deps import get_current_user
from app.database import AsyncSessionLocal, get_db
from app.memory.service import build_memory_prompt, list_facts
from app.models import Conversation, Message, PluginLog, UsageLog, User
from app.plugins.base import registry
from app.vector_database.store import search_similar_chunks

router = APIRouter(prefix="/api/chat", tags=["chat"])

SYSTEM_PROMPT = (
    "Voce e a Orbit IA, uma assistente de inteligencia artificial profissional, "
    "objetiva e prestativa. Responda em markdown quando fizer sentido (listas, "
    "codigo, tabelas). Use as ferramentas disponiveis quando precisar de dados "
    "atuais ou calculos precisos."
)


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    model: str | None = None
    use_web_search: bool = True


async def _get_or_create_conversation(db: AsyncSession, user: User, conversation_id: str | None, model: str) -> Conversation:
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversa nao encontrada")
        return conversation

    conversation = Conversation(user_id=user.id, model=model, title="Nova conversa")
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def _build_messages(db: AsyncSession, user: User, conversation: Conversation, user_message: str) -> list[dict]:
    facts = await list_facts(db, user.id)
    memory_block = build_memory_prompt(facts)

    relevant_chunks = await search_similar_chunks(db, user.id, user_message, top_k=4)
    context_block = ""
    if relevant_chunks:
        context_block = "Trechos relevantes de documentos enviados pelo usuario:\n" + "\n---\n".join(relevant_chunks)

    system_content = SYSTEM_PROMPT
    if memory_block:
        system_content += "\n\n" + memory_block
    if context_block:
        system_content += "\n\n" + context_block

    history_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at)
    )
    history = history_result.scalars().all()

    messages = [{"role": "system", "content": system_content}]
    for m in history:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": user_message})
    return messages


async def _stream_response(user: User, payload: ChatRequest):
    """Gerador SSE consumido pelo frontend. Cada linha e um evento `data: {...}`."""
    async with AsyncSessionLocal() as db:
        model = payload.model or user.preferred_model
        conversation = await _get_or_create_conversation(db, user, payload.conversation_id, model)

        # Persiste a mensagem do usuario imediatamente
        user_msg = Message(conversation_id=conversation.id, role="user", content=payload.message)
        db.add(user_msg)

        # Define titulo automatico na primeira mensagem
        if conversation.title == "Nova conversa":
            conversation.title = payload.message[:60]

        await db.commit()

        yield f"data: {json.dumps({'type': 'conversation', 'conversation_id': conversation.id})}\n\n"
        yield f"data: {json.dumps({'type': 'status', 'message': 'Orbit IA esta pensando...'})}\n\n"

        messages = await _build_messages(db, user, conversation, payload.message)
        tools = registry.tool_schemas() if payload.use_web_search else None

        full_response = ""
        start_time = time.time()
        tool_calls_made = []

        async for event in ai_client.stream_chat(messages, model=model, tools=tools):
            if event["type"] == "delta":
                full_response += event["content"]
                yield f"data: {json.dumps({'type': 'delta', 'content': event['content']})}\n\n"

            elif event["type"] == "tool_call":
                for call in event["tool_calls"]:
                    fn_name = call["function"]["name"]
                    try:
                        args = json.loads(call["function"]["arguments"] or "{}")
                    except json.JSONDecodeError:
                        args = {}

                    plugin = registry.get(fn_name)
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool': fn_name})}\n\n"

                    if plugin:
                        result = await plugin.run(args)
                    else:
                        result = {"error": f"Plugin '{fn_name}' nao encontrado"}

                    db.add(PluginLog(user_id=user.id, plugin_name=fn_name, input_payload=args,
                                      output_payload=result if isinstance(result, dict) else {"value": str(result)}))
                    tool_calls_made.append({"name": fn_name, "arguments": args, "result": result})

                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': fn_name, 'result': result})}\n\n"

                    messages.append({"role": "assistant", "tool_calls": [call]})
                    messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": json.dumps(result)})

                await db.commit()

                # Reenvia ao modelo com os resultados das tools para gerar a resposta final
                async for follow_event in ai_client.stream_chat(messages, model=model, tools=None):
                    if follow_event["type"] == "delta":
                        full_response += follow_event["content"]
                        yield f"data: {json.dumps({'type': 'delta', 'content': follow_event['content']})}\n\n"
                    elif follow_event["type"] == "error":
                        yield f"data: {json.dumps(follow_event)}\n\n"

            elif event["type"] == "error":
                yield f"data: {json.dumps(event)}\n\n"
                return

        latency_ms = int((time.time() - start_time) * 1000)
        tokens_input = sum(len(m.get("content", "").split()) for m in messages if isinstance(m.get("content"), str))
        tokens_output = len(full_response.split())
        cost = estimate_cost(model, tokens_input, tokens_output)

        assistant_msg = Message(
            conversation_id=conversation.id, role="assistant", content=full_response,
            tool_calls=tool_calls_made or None,
            tokens_input=tokens_input, tokens_output=tokens_output, cost_usd=cost,
        )
        db.add(assistant_msg)
        db.add(UsageLog(
            user_id=user.id, conversation_id=conversation.id, model=model,
            tokens_input=tokens_input, tokens_output=tokens_output, cost_usd=cost,
            latency_ms=latency_ms, endpoint="/api/chat", status="success",
        ))
        await db.commit()

        yield f"data: {json.dumps({'type': 'done', 'conversation_id': conversation.id, 'usage': {'tokens_input': tokens_input, 'tokens_output': tokens_output, 'cost_usd': float(cost)}})}\n\n"


@router.post("")
async def chat(payload: ChatRequest, user: User = Depends(get_current_user)):
    return StreamingResponse(
        _stream_response(user, payload),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
