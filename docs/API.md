# Manual da Orbit AI API

Toda a comunicação do frontend passa exclusivamente por esta API. Documentação
interativa completa (OpenAPI/Swagger) disponível em `/docs` e o schema bruto em
`/openapi.json` quando o backend está rodando.

Base URL padrão: `http://localhost:8000`

## Autenticação
Todas as rotas (exceto `/api/auth/register`, `/api/auth/login`, `/api/auth/refresh`,
`/api/status` e `/api/version`) exigem o header:
```
Authorization: Bearer <access_token>
```

### POST /api/auth/register
Cria um usuário. Body: `{"email": "...", "password": "...", "full_name": "..."}`
Retorna `{"access_token", "refresh_token", "token_type"}`.

### POST /api/auth/login
Body: `{"email": "...", "password": "..."}`. Mesmo retorno acima.

### POST /api/auth/refresh
Body: `{"refresh_token": "..."}`. Rotaciona o refresh token e emite novo access token.

### GET /api/auth/oauth/{provider}/login
`provider` = `google` ou `github`. Redireciona para o provedor OAuth2.

### GET /api/auth/me
Retorna o perfil do usuário autenticado.

## Chat

### POST /api/chat
Endpoint principal. Envia uma mensagem e recebe a resposta via **Server-Sent
Events (SSE)** — `Content-Type: text/event-stream`.

Body:
```json
{
  "message": "Explique o que é RAG",
  "conversation_id": "uuid-opcional",
  "model": "llama3",
  "use_web_search": true
}
```

Eventos emitidos (um por linha `data: {...}`):
| type | Significado |
|---|---|
| `conversation` | ID da conversa (nova ou existente) |
| `status` | Mensagem de status, ex. "Orbit IA está pensando..." |
| `delta` | Pedaço de texto da resposta (streaming) |
| `tool_start` | A IA começou a executar um plugin |
| `tool_result` | Resultado retornado pelo plugin |
| `done` | Fim do stream, com contagem de tokens e custo estimado |
| `error` | Erro do provedor de IA ou da aplicação |

## Memória

### GET /api/memory
Lista os fatos/preferências salvos do usuário autenticado.

### POST /api/memory
Body: `{"key": "...", "value": "..."}`. Cria ou atualiza um fato.

### DELETE /api/memory/{key}
Remove um fato específico.

## Busca na web

### POST /api/search
Body: `{"query": "..."}`. Usa o mesmo plugin `web_search` do chat, mas fora do
fluxo de conversa (útil para integrações externas).

## Arquivos

### POST /api/files/upload
`multipart/form-data` com campo `file` (PDF, DOCX, TXT ou imagem) e query
opcional `conversation_id`. O processamento (extração de texto + indexação
vetorial) roda em background; consulte `GET /api/files/{id}/status`.

## Conversas

### GET /api/conversations?q=termo
Lista conversas do usuário, com busca opcional por título ou conteúdo.

### GET /api/conversations/{id}
Detalha uma conversa com todas as mensagens.

### PATCH /api/conversations/{id}
Body: `{"title": "..."}`. Renomeia a conversa.

### DELETE /api/conversations/{id}
Remove a conversa e suas mensagens.

### GET /api/conversations/{id}/export?format=markdown|pdf
Exporta a conversa como arquivo para download.

## Perfil e configurações

### PATCH /api/users/me
Body (todos os campos opcionais): `{"full_name", "theme", "language", "preferred_model"}`.

## Sistema

### GET /api/status
Healthcheck simples da API.

### GET /api/version
Versão atual e changelog (sistema de atualização automática do app).

## Painel administrativo (requer usuário admin)

### GET /api/admin/users
Lista todos os usuários.

### PATCH /api/admin/users/{id}/toggle-active
Ativa/desativa um usuário.

### GET /api/admin/usage/summary?days=30
Resumo de uso e custo por modelo no período.

### GET /api/admin/logs/plugins?limit=100
Logs recentes de execução de plugins/tools.
