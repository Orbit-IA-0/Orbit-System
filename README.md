# 🛰️ Orbit IA

Plataforma de chat com inteligência artificial de nível profissional, com
identidade visual e produto 100% próprios: frontend, backend, banco de dados,
autenticação, memória, plugins e painel administrativo autorais.

O "cérebro" da IA é plugável: qualquer modelo real via API compatível com
OpenAI, ou um modelo open-source local (Llama 3, Mistral, Qwen2.5) servido via
Ollama — configurável por variável de ambiente, sem alterar código.

## ✨ Funcionalidades
- Login/cadastro com e-mail+senha e OAuth2 (Google/GitHub)
- Chat em tempo real com streaming de resposta (SSE) e indicador "Orbit IA está pensando..."
- Markdown com blocos de código destacados e botão de copiar
- Histórico de conversas com busca
- Exportação de conversas em PDF ou Markdown
- Upload de arquivos (PDF, DOCX, TXT, imagens) para contexto via RAG (pgvector)
- Busca na internet integrada (tool/function calling)
- Memória persistente por usuário entre sessões
- Perfil e configurações (tema claro/escuro, idioma, modelo preferido)
- Arquitetura de plugins extensível (function calling)
- Painel administrativo (usuários, uso, custo por modelo, logs de plugins)
- Sistema de versão/changelog

## 🎨 Identidade visual
Tema futurista em preto, azul e roxo, com glassmorphism sutil, microanimações
e suporte completo a dark/light mode — 100% responsivo (mobile-first).

## 🏗️ Arquitetura

```
/frontend          Next.js 14 + React + TypeScript + Tailwind
/backend            FastAPI (Python) — a "Orbit AI API"
/backend/app/auth        Autenticação JWT + OAuth2
/backend/app/api         Rotas: chat, memory, search, files, conversations, admin
/backend/app/plugins     Sistema de plugins/tools (function calling)
/backend/app/vector_database   RAG com pgvector
/backend/app/memory      Memória persistente por usuário
/database           Script de inicialização do PostgreSQL
/docker             docker-compose.yml (sobe tudo com um comando)
/docs               Manuais de instalação, API, deploy e banco de dados
/tests              Testes automatizados (pytest)
```

## 🚀 Início rápido

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose -f docker/docker-compose.yml up --build
```

Depois, baixe o modelo local (se estiver usando Ollama):
```bash
docker exec -it orbit_ollama ollama pull llama3
docker exec -it orbit_ollama ollama pull nomic-embed-text
```

Acesse:
- Frontend: http://localhost:3000
- Documentação interativa da API (Swagger): http://localhost:8000/docs

Login inicial de administrador (apenas em desenvolvimento):
`admin@orbit.ia` / `OrbitAdmin123!`

## 📚 Documentação completa
- [Manual de instalação](docs/INSTALACAO.md)
- [Manual da Orbit AI API](docs/API.md)
- [Manual de deploy](docs/DEPLOY.md)
- [Manual do banco de dados](docs/BANCO_DE_DADOS.md)

## 🧪 Testes
```bash
cd backend
pip install -r requirements.txt -r ../tests/backend/requirements-test.txt
TEST_DATABASE_URL=postgresql+asyncpg://orbit:orbit@localhost:5432/orbit_ia_test \
  pytest ../tests/backend -v
```

## 🔌 Trocando o "cérebro" da IA
Todo o comportamento do modelo é isolado em `backend/app/ai_client.py` e
controlado por variáveis de ambiente — o resto do sistema (auth, memória,
plugins, frontend) nunca muda:

```bash
# Ollama local (padrão)
AI_BASE_URL=http://ollama:11434/v1
AI_API_KEY=ollama
AI_CHAT_MODEL=llama3

# Qualquer API compatível com OpenAI
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=sk-...
AI_CHAT_MODEL=gpt-4o-mini
```

## Licença
Projeto de demonstração/base para evolução — ajuste a licença conforme sua necessidade.
