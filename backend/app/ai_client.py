"""
Cliente de IA da Orbit IA.

Este e o UNICO ponto do sistema que fala com o "cerebro" do modelo de linguagem.
Ele e 100% configuravel via variaveis de ambiente e funciona tanto com:
  - Qualquer API compativel com OpenAI (OpenAI, Groq, Together, OpenRouter, etc.)
  - Um servidor Ollama local expondo modelos open-source (Llama 3, Mistral, Qwen2.5),
    que tambem expoe uma interface compativel com /v1/chat/completions.

O restante da aplicacao (rotas, memoria, plugins, frontend) nunca conhece o provedor
real: apenas chama os metodos abaixo. Trocar de provedor = mudar AI_BASE_URL/AI_API_KEY.
"""
import json
from typing import AsyncGenerator

import httpx

from app.config import get_settings

settings = get_settings()

# Tabela de custo aproximado por 1K tokens (USD), usada apenas para o painel admin.
# Ajustavel conforme o provedor configurado.
MODEL_PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "llama3": {"input": 0.0, "output": 0.0},       # modelo local via Ollama: custo zero
    "mistral": {"input": 0.0, "output": 0.0},
    "qwen2.5": {"input": 0.0, "output": 0.0},
}


def estimate_cost(model: str, tokens_input: int, tokens_output: int) -> float:
    pricing = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
    return round(
        (tokens_input / 1000) * pricing["input"] + (tokens_output / 1000) * pricing["output"], 6
    )


class AIClient:
    def __init__(self):
        self.base_url = settings.AI_BASE_URL.rstrip("/")
        self.api_key = settings.AI_API_KEY

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def stream_chat(
        self,
        messages: list[dict],
        model: str | None = None,
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[dict, None]:
        """
        Faz uma chamada de chat com streaming (SSE) ao provedor configurado.
        Retorna um gerador assincrono de eventos parseados:
          {"type": "delta", "content": "..."}       -> pedaco de texto
          {"type": "tool_call", "tool_calls": [...]} -> a IA quer usar um plugin
          {"type": "done", "usage": {...}}           -> fim do stream com contagem de tokens
        """
        payload = {
            "model": model or settings.AI_CHAT_MODEL,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        url = f"{self.base_url}/chat/completions"
        accumulated_tool_calls: dict[int, dict] = {}

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, headers=self._headers(), json=payload) as response:
                if response.status_code >= 400:
                    body = await response.aread()
                    yield {"type": "error", "message": f"Erro do provedor de IA ({response.status_code}): {body.decode(errors='ignore')}"}
                    return

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data_str = line[len("data:"):].strip()
                    if data_str == "[DONE]":
                        if accumulated_tool_calls:
                            yield {"type": "tool_call", "tool_calls": list(accumulated_tool_calls.values())}
                        yield {"type": "done", "usage": {}}
                        return
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choice = (chunk.get("choices") or [{}])[0]
                    delta = choice.get("delta", {})

                    if delta.get("content"):
                        yield {"type": "delta", "content": delta["content"]}

                    for tc in delta.get("tool_calls") or []:
                        idx = tc.get("index", 0)
                        entry = accumulated_tool_calls.setdefault(
                            idx, {"id": tc.get("id"), "type": "function",
                                  "function": {"name": "", "arguments": ""}}
                        )
                        fn = tc.get("function", {})
                        if fn.get("name"):
                            entry["function"]["name"] += fn["name"]
                        if fn.get("arguments"):
                            entry["function"]["arguments"] += fn["arguments"]

                    if choice.get("finish_reason") == "stop":
                        yield {"type": "done", "usage": chunk.get("usage", {})}
                        return

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        """Gera embeddings para uma lista de textos (usado no RAG de documentos e memoria)."""
        url = f"{self.base_url}/embeddings"
        payload = {"model": model or settings.AI_EMBEDDING_MODEL, "input": texts}
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]


ai_client = AIClient()
