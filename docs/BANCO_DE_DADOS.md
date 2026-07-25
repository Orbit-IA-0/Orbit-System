# Manual do Banco de Dados — Orbit IA

## Visão geral
- **PostgreSQL 16** com a extensão **pgvector** (imagem `pgvector/pgvector:pg16`),
  usado tanto como banco relacional quanto como banco vetorial (RAG), evitando
  a necessidade de um segundo serviço (Qdrant é uma alternativa, ver abaixo).
- As tabelas são criadas automaticamente pela API na inicialização
  (`app/database.py::init_db`), a partir dos models em `app/models.py`.

## Tabelas principais

| Tabela | Descrição |
|---|---|
| `users` | Contas de usuário, preferências (tema, idioma, modelo) |
| `oauth_accounts` | Vínculo entre usuário e provedor OAuth (Google/GitHub) |
| `refresh_tokens` | Tokens de refresh (hash SHA-256, com expiração e revogação) |
| `conversations` | Conversas de chat por usuário |
| `messages` | Mensagens de cada conversa (com tokens e custo estimado) |
| `memory_facts` | Memória persistente por usuário (chave/valor) |
| `documents` | Metadados de arquivos enviados para contexto |
| `document_chunks` | Pedaços de texto dos documentos + embedding (pgvector) |
| `usage_logs` | Log de uso para o painel admin (tokens, custo, latência) |
| `plugin_logs` | Auditoria de execução de plugins/tools |
| `app_versions` | Histórico de versões/changelog |

## Busca vetorial (RAG)
A coluna `document_chunks.embedding` usa o tipo `vector(N)` do pgvector, onde
`N` é definido por `AI_EMBEDDING_DIM` (padrão 768, compatível com o modelo
`nomic-embed-text` do Ollama; ajuste para 1536 se usar `text-embedding-3-small`
da OpenAI, por exemplo).

A busca por similaridade usa distância de cosseno:
```python
DocumentChunk.embedding.cosine_distance(query_embedding)
```

## Alternativa: Qdrant
Se preferir um banco vetorial dedicado em vez do pgvector, basta:
1. Adicionar o serviço `qdrant/qdrant` ao `docker-compose.yml`.
2. Substituir as funções de `app/vector_database/store.py` para usar o
   cliente `qdrant-client` em vez de SQLAlchemy/pgvector.
3. Manter a mesma assinatura de `index_document` e `search_similar_chunks`
   para não impactar o restante da aplicação.

## Migrações
O projeto usa `Base.metadata.create_all` na inicialização para simplicidade
do MVP. Para produção, recomenda-se adotar **Alembic**:
```bash
cd backend
alembic init alembic
# configurar alembic.ini e env.py apontando para SYNC_DATABASE_URL e Base.metadata
alembic revision --autogenerate -m "schema inicial"
alembic upgrade head
```

## Backup
```bash
docker exec orbit_postgres pg_dump -U orbit orbit_ia > backup.sql
```

## Restauração
```bash
cat backup.sql | docker exec -i orbit_postgres psql -U orbit -d orbit_ia
```
