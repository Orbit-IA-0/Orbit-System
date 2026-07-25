# Manual de Instalação — Orbit IA

## Pré-requisitos
- Docker e Docker Compose (v2+)
- 8 GB de RAM livres (para rodar um modelo local via Ollama, ex. Llama 3 8B)
- (Opcional) Chave de API de um provedor compatível com OpenAI, se preferir não usar modelo local

## Passo a passo

### 1. Clonar/posicionar o projeto
Garanta que a estrutura de pastas esteja assim:
```
orbit-ia/
  backend/
  frontend/
  docker/
  database/
  docs/
  tests/
```

### 2. Configurar variáveis de ambiente
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edite `backend/.env` e escolha o "cérebro" da IA:

**Opção A — Modelo local via Ollama (padrão, sem custo):**
```
AI_BASE_URL=http://ollama:11434/v1
AI_API_KEY=ollama
AI_CHAT_MODEL=llama3
AI_EMBEDDING_MODEL=nomic-embed-text
```

**Opção B — API compatível com OpenAI:**
```
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=sk-sua-chave-aqui
AI_CHAT_MODEL=gpt-4o-mini
AI_EMBEDDING_MODEL=text-embedding-3-small
AI_EMBEDDING_DIM=1536
```

### 3. Subir todo o ambiente
```bash
docker compose -f docker/docker-compose.yml up --build
```

Isso sobe: PostgreSQL (com pgvector), Redis, Ollama (modelo local), backend (FastAPI) e frontend (Next.js).

### 4. Baixar o modelo local (se estiver usando Ollama)
Em outro terminal, com os containers já rodando:
```bash
docker exec -it orbit_ollama ollama pull llama3
docker exec -it orbit_ollama ollama pull nomic-embed-text
```

### 5. Acessar a aplicação
- Frontend: http://localhost:3000
- API (docs interativas Swagger): http://localhost:8000/docs
- API (OpenAPI JSON): http://localhost:8000/openapi.json

### 6. Login inicial
Em ambiente de desenvolvimento, um usuário administrador é criado automaticamente:
- E-mail: `admin@orbit.ia`
- Senha: `OrbitAdmin123!`

**Troque essa senha imediatamente em produção** (ou remova a semente de dados em `app/main.py`).

## OAuth Google/GitHub (opcional)
1. Crie credenciais OAuth2 no Google Cloud Console e no GitHub Developer Settings.
2. Configure as URLs de callback:
   - Google: `http://localhost:8000/api/auth/oauth/google/callback`
   - GitHub: `http://localhost:8000/api/auth/oauth/github/callback`
3. Preencha `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` no `.env`.

## Rodando sem Docker (desenvolvimento local)

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
