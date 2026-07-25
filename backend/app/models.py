"""
Modelos ORM (SQLAlchemy) da Orbit IA.
Cobre usuarios, autenticacao OAuth, conversas/mensagens, memoria do usuario,
documentos indexados (RAG via pgvector), logs de uso/custo e plugins.
"""
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.config import get_settings

settings = get_settings()


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # nulo se so usa OAuth
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Preferencias de perfil
    theme = Column(String(20), default="dark", nullable=False)       # dark | light
    language = Column(String(10), default="pt-BR", nullable=False)
    preferred_model = Column(String(100), default="llama3", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("MemoryFact", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    provider = Column(String(50), nullable=False)          # google | github
    provider_account_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="oauth_accounts")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), default="Nova conversa", nullable=False)
    model = Column(String(100), nullable=False, default="llama3")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan",
                             order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    conversation_id = Column(UUID(as_uuid=False), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)     # user | assistant | system | tool
    content = Column(Text, nullable=False)
    tool_calls = Column(JSON, nullable=True)       # registro de chamadas de plugins/tools
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost_usd = Column(Numeric(10, 6), default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


class MemoryFact(Base):
    """Memoria persistente por usuario: fatos e preferencias extraidos das conversas."""
    __tablename__ = "memory_facts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    key = Column(String(120), nullable=False)      # ex: "linguagem_preferida"
    value = Column(Text, nullable=False)           # ex: "Python"
    source = Column(String(50), default="chat", nullable=False)  # chat | api | admin
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="memories")


class Document(Base):
    """Documento enviado pelo usuario (PDF, imagem, docx) para contexto/RAG."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=False), ForeignKey("conversations.id"), nullable=True)
    filename = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    status = Column(String(20), default="processing", nullable=False)  # processing | ready | error
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Pedaco de texto do documento com seu embedding (pgvector) para busca semantica."""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(settings.AI_EMBEDDING_DIM), nullable=True)

    document = relationship("Document", back_populates="chunks")


class UsageLog(Base):
    """Log de uso para o painel administrativo: custo por modelo, tokens, latencia."""
    __tablename__ = "usage_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=False), nullable=True)
    model = Column(String(100), nullable=False)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost_usd = Column(Numeric(10, 6), default=0)
    latency_ms = Column(Integer, default=0)
    endpoint = Column(String(100), nullable=False)
    status = Column(String(20), default="success", nullable=False)  # success | error
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PluginLog(Base):
    """Log de execucao de plugins/tools (function calling) para auditoria no admin."""
    __tablename__ = "plugin_logs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    plugin_name = Column(String(100), nullable=False)
    input_payload = Column(JSON, nullable=True)
    output_payload = Column(JSON, nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AppVersion(Base):
    """Historico de versoes/changelog exibido no sistema de atualizacao automatica."""
    __tablename__ = "app_versions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    version = Column(String(20), nullable=False, unique=True)
    changelog = Column(Text, nullable=False)
    released_at = Column(DateTime, default=datetime.utcnow, nullable=False)
