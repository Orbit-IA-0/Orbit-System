# Manual de Deploy — Orbit IA

## Deploy simples com Docker Compose (recomendado para MVP)

1. Provisione uma VM (2 vCPU / 8 GB RAM mínimo; 16 GB+ se for rodar Llama 3 localmente).
2. Instale Docker e Docker Compose.
3. Copie o projeto para o servidor.
4. Configure `backend/.env` com segredos de produção:
   - `JWT_SECRET_KEY`: gere uma chave forte, ex. `openssl rand -hex 32`
   - `ENVIRONMENT=production` (desativa a semente automática de admin)
   - `DATABASE_URL` / `SYNC_DATABASE_URL` apontando para o Postgres real
   - `CORS_ORIGINS` com o domínio real do frontend
   - Credenciais OAuth com URLs de callback do domínio de produção
5. Configure `frontend/.env` com `NEXT_PUBLIC_API_URL` apontando para a URL pública da API.
6. Suba com:
   ```bash
   docker compose -f docker/docker-compose.yml up -d --build
   ```
7. Coloque um proxy reverso (Nginx, Caddy ou Traefik) na frente dos serviços
   `frontend` (porta 3000) e `backend` (porta 8000), com TLS via Let's Encrypt.

## Exemplo de configuração Nginx (resumido)
```nginx
server {
    listen 443 ssl;
    server_name orbit.seudominio.com;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_buffering off; # necessário para o streaming SSE do chat
    }

    location / {
        proxy_pass http://localhost:3000;
    }
}
```

**Importante:** `proxy_buffering off` (ou equivalente no seu proxy) é essencial
para que o streaming de resposta do chat (SSE) funcione corretamente atrás de
um proxy reverso.

## Segurança em produção
- Nunca deixe `DEBUG=true` nem exponha `admin@orbit.ia` com a senha padrão.
- Restrinja o acesso à porta 5432 (Postgres) e 6379 (Redis) apenas à rede interna.
- Faça backup periódico do banco (ver `BANCO_DE_DADOS.md`).
- Rotacione `JWT_SECRET_KEY` apenas com uma estratégia de invalidação de sessões,
  pois isso invalida todos os tokens emitidos anteriormente.

## Escalonamento (opcional, além do MVP)
- Múltiplas réplicas do `backend` atrás de um load balancer (a API é stateless
  além do banco/Redis, então escala horizontalmente sem problemas).
- Kubernetes é opcional: os mesmos Dockerfiles podem virar Deployments/Services
  com um Ingress cuidando do TLS e do roteamento.
- Redis pode ser usado para cache de respostas de busca na web e rate limiting
  (não implementado no MVP, mas a infraestrutura já está disponível via `REDIS_URL`).
