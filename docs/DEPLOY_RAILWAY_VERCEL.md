# Deploy — Railway (backend + IA + bancos) + Vercel (frontend)

Esta é a divisão recomendada quando você quer sua própria IA rodando (Ollama,
sem depender de OpenAI/Groq) e ainda assim ter o site acessível na internet:

- **Vercel**: só o `frontend` (Next.js). Serverless, rápido, grátis no plano hobby.
- **Supabase**: banco Postgres com pgvector (projeto `orbit-ia`, já criado e com a extensão habilitada).
- **Railway**: `backend` (FastAPI) + `ollama` (o modelo) + `redis`.
  Precisa ser um servidor sempre ligado — por isso não pode ser a Vercel.

```
[ usuário ]
     │
     ▼
[ Vercel — frontend Next.js ]
     │  fetch para NEXT_PUBLIC_API_URL
     ▼
[ Railway — backend FastAPI ] ──► [ Supabase — Postgres (pgvector) ]
     │        │                  └► [ Railway — Redis ]
     │        └────────────────────► [ Railway — Ollama (modelo local) ]
     ▼
resposta em streaming (SSE)
```

## 0. Banco de dados (Supabase) — já feito

O projeto `orbit-ia` já está criado no Supabase com a extensão `vector` habilitada.
As tabelas são criadas sozinhas pelo backend na primeira subida (`init_db()`).
Falta só uma coisa que o Supabase não expõe por API por segurança: **a senha do banco**.

1. Acesse supabase.com → projeto `orbit-ia` → **Settings → Database**
2. Em "Connection string", copie a senha (ou clique em "Reset database password" se não souber a atual)
3. Cole no lugar de `<SENHA_DO_BANCO>` em `DATABASE_URL` e `SYNC_DATABASE_URL` no `.env` do backend

## 1. Criar os serviços no Railway

Crie um projeto novo no Railway e adicione 2 serviços (Postgres não entra mais aqui — já está no Supabase):

### 1.1 Redis
- "New Service" → "Empty Service" → "Deploy from Docker Image"
- Imagem: `redis:7-alpine`
- Sem porta pública necessária

### 1.2 Ollama (a IA local)
- "New Service" → "Empty Service" → "Deploy from Docker Image"
- Imagem: `ollama/ollama:latest`
- Adicione um **Volume** em `/root/.ollama` (senão o modelo baixado some a cada deploy)
- Depois do primeiro deploy, abra o terminal do serviço (Railway → Service → "Shell") e rode:
  ```
  ollama pull llama3.2:3b
  ```
  (troque pelo modelo que seu servidor aguenta — veja tabela de RAM abaixo)
- Sem porta pública necessária (só o backend fala com ele)

### 1.3 Backend (FastAPI)
- "New Service" → "Deploy from GitHub repo" → selecione este repositório
- Em **Settings → Root Directory**, coloque `backend`
- O Railway detecta o `Dockerfile` e o `railway.toml` automaticamente
- Ative **Networking → Public Domain** (essa é a única URL pública dos 4 serviços)
- Variáveis de ambiente (Settings → Variables):
  ```
  ENVIRONMENT=production
  DEBUG=false
  JWT_SECRET_KEY=<gere com: openssl rand -hex 32>

  DATABASE_URL=postgresql+asyncpg://postgres.dnnbctrbiwcfadjfhwev:<SENHA_DO_BANCO>@aws-0-us-east-1.pooler.supabase.com:6543/postgres
  SYNC_DATABASE_URL=postgresql+psycopg2://postgres.dnnbctrbiwcfadjfhwev:<SENHA_DO_BANCO>@aws-0-us-east-1.pooler.supabase.com:6543/postgres
  REDIS_URL=redis://redis.railway.internal:6379/0

  AI_BASE_URL=http://ollama.railway.internal:11434/v1
  AI_API_KEY=ollama
  AI_CHAT_MODEL=llama3.2:3b

  CORS_ORIGINS=https://seu-projeto.vercel.app
  OAUTH_REDIRECT_BASE_URL=https://seu-backend.up.railway.app
  ```
  Troque `redis` e `ollama` pelos nomes reais que você deu aos serviços no
  Railway — o `.railway.internal` só funciona com o nome exato do serviço.
  A `DATABASE_URL` do Supabase acima já está com o projeto `orbit-ia` certo,
  só falta trocar `<SENHA_DO_BANCO>`.

## 2. Deploy do frontend na Vercel

1. Importe o repositório na Vercel, com **Root Directory** = `frontend`
2. Framework preset: Next.js (detecta sozinho)
3. Variável de ambiente:
   ```
   NEXT_PUBLIC_API_URL=https://seu-backend.up.railway.app
   ```
4. Deploy. Depois, volte no Railway e atualize `CORS_ORIGINS` do backend com a
   URL final que a Vercel gerou (e refaça o deploy do backend).

## 3. Escolhendo o modelo pelo tamanho do servidor Railway

| Servidor (RAM) | Modelo recomendado |
|---|---|
| 2 GB | `llama3.2:1b` |
| 4–8 GB | `llama3.2:3b` ou `qwen2.5:3b` |
| 16 GB+ | `llama3.1:8b` ou `qwen2.5:7b` |

Railway cobra por uso de CPU/RAM do plano — quanto maior o modelo, maior o
custo do serviço do Ollama rodando 24h. Sem GPU no Railway, modelos acima de
8b ficam lentos para chat em tempo real.

## 4. Checklist pós-deploy
- [ ] `https://seu-backend.up.railway.app/api/status` responde `{"status":"ok"}`
- [ ] Login/cadastro funcionando no frontend da Vercel
- [ ] Enviar uma mensagem no chat e ver a resposta chegar em streaming
- [ ] `CORS_ORIGINS` no backend igual ao domínio final da Vercel (sem barra no final)
- [ ] `JWT_SECRET_KEY` trocado do valor padrão do `.env.example`
