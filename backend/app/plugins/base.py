"""
Arquitetura de plugins (tools/function calling) da Orbit IA.
Cada plugin declara seu schema no formato de "tools" da API de chat
(compativel com function calling estilo OpenAI) e implementa um metodo
`run` assincrono. Novos plugins bastam herdar de Plugin e se registrar
no PluginRegistry — a IA passa a poder chama-los automaticamente.
"""
from abc import ABC, abstractmethod
from typing import Any


class Plugin(ABC):
    name: str
    description: str
    parameters: dict  # JSON Schema dos argumentos aceitos

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @abstractmethod
    async def run(self, arguments: dict) -> Any:
        """Executa o plugin com os argumentos fornecidos pelo modelo e retorna o resultado."""
        raise NotImplementedError


class PluginRegistry:
    def __init__(self):
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin):
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> Plugin | None:
        return self._plugins.get(name)

    def all(self) -> list[Plugin]:
        return list(self._plugins.values())

    def tool_schemas(self) -> list[dict]:
        return [p.schema() for p in self._plugins.values()]


registry = PluginRegistry()
