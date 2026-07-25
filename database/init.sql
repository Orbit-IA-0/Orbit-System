-- Script de inicializacao do banco Orbit IA.
-- A extensao pgvector e habilitada aqui e tambem de forma idempotente pelo
-- backend (app/database.py) na subida da API, garantindo que o RAG funcione
-- mesmo se o backend subir antes deste script rodar em outro ambiente.
CREATE EXTENSION IF NOT EXISTS vector;
