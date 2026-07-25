"""
Camada de vetorizacao (RAG) usando pgvector.
Responsavel por: dividir documentos em chunks, gerar embeddings via ai_client
e buscar os trechos mais relevantes semanticamente para uma pergunta do usuario.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_client import ai_client
from app.models import Document, DocumentChunk


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Divide o texto em pedacos com sobreposicao, preservando contexto entre chunks."""
    chunks = []
    start = 0
    text = text.strip()
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0:
            start = 0
        if end >= len(text):
            break
    return [c for c in chunks if c.strip()]


async def index_document(db: AsyncSession, document: Document, full_text: str):
    """Gera embeddings para os chunks do documento e persiste no pgvector."""
    pieces = chunk_text(full_text)
    if not pieces:
        document.status = "error"
        await db.commit()
        return

    embeddings = await ai_client.embed(pieces)
    for idx, (piece, embedding) in enumerate(zip(pieces, embeddings)):
        db.add(DocumentChunk(document_id=document.id, chunk_index=idx, content=piece, embedding=embedding))

    document.status = "ready"
    await db.commit()


async def search_similar_chunks(db: AsyncSession, user_id: str, query: str, top_k: int = 5) -> list[str]:
    """Retorna os trechos de documentos do usuario mais similares semanticamente a pergunta."""
    [query_embedding] = await ai_client.embed([query])

    result = await db.execute(
        select(DocumentChunk.content)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.user_id == user_id, Document.status == "ready")
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    return [row[0] for row in result.all()]
