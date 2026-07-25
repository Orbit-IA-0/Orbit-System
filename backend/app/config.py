"""
Configuracoes centrais da Orbit AI API.
Todas as variaveis sensiveis e de infraestrutura sao lidas do ambiente (.env),
permitindo trocar o "cerebro" da IA (provedor OpenAI-compatible ou Ollama local)
sem alterar nenhuma linha de codigo.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Aplicacao
    APP_NAME: str = "Orbit AI API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Seguranca / JWT
    JWT_SECRET_KEY: str = "change-this-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # OAuth2 (Google / GitHub)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_BASE_URL: str = "http://localhost:8000"

    # Banco de dados
    DATABASE_URL: str = "postgresql+asyncpg://orbit:orbit@postgres:5432/orbit_ia"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://orbit:orbit@postgres:5432/orbit_ia"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Provedor de IA (modelo real via API compativel OpenAI, ou Ollama local)
    # Exemplos:
    #   OpenAI/compatível:  AI_BASE_URL=https://api.openai.com/v1  AI_API_KEY=sk-...
    #   Ollama local:       AI_BASE_URL=http://ollama:11434/v1     AI_API_KEY=ollama
    AI_BASE_URL: str = "http://ollama:11434/v1"
    AI_API_KEY: str = "ollama"
    AI_CHAT_MODEL: str = "llama3"
    AI_EMBEDDING_MODEL: str = "nomic-embed-text"
    AI_EMBEDDING_DIM: int = 768

    # Busca na internet (tool). Configuravel para qualquer provedor compativel.
    WEB_SEARCH_PROVIDER: str = "tavily"  # tavily | serpapi | none
    WEB_SEARCH_API_KEY: str = ""

    # Uploads
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_MB: int = 25

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
