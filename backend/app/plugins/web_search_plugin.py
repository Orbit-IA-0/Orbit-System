"""Plugin de busca na internet, usado pela IA para responder com informacoes atuais."""
import httpx

from app.config import get_settings
from app.plugins.base import Plugin

settings = get_settings()


class WebSearchPlugin(Plugin):
    name = "web_search"
    description = "Pesquisa na internet por informacoes atuais e retorna os resultados mais relevantes."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Termo de busca"},
        },
        "required": ["query"],
    }

    async def run(self, arguments: dict) -> dict:
        query = arguments.get("query", "")
        if settings.WEB_SEARCH_PROVIDER == "tavily" and settings.WEB_SEARCH_API_KEY:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={"api_key": settings.WEB_SEARCH_API_KEY, "query": query, "max_results": 5},
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "results": [
                        {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content")}
                        for r in data.get("results", [])
                    ]
                }
        return {"results": [], "note": "Provedor de busca nao configurado (defina WEB_SEARCH_API_KEY)."}


class GetDateTimePlugin(Plugin):
    name = "get_current_datetime"
    description = "Retorna a data e hora atuais em UTC."
    parameters = {"type": "object", "properties": {}}

    async def run(self, arguments: dict) -> dict:
        from datetime import datetime, timezone
        return {"datetime_utc": datetime.now(timezone.utc).isoformat()}


class CalculatorPlugin(Plugin):
    name = "calculator"
    description = "Avalia uma expressao matematica simples (soma, subtracao, multiplicacao, divisao, potencia)."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Expressao matematica, ex: (2 + 3) * 4"},
        },
        "required": ["expression"],
    }

    async def run(self, arguments: dict) -> dict:
        import ast
        import operator

        allowed_ops = {
            ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
            ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
        }

        def _eval(node):
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.BinOp) and type(node.op) in allowed_ops:
                return allowed_ops[type(node.op)](_eval(node.left), _eval(node.right))
            if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_ops:
                return allowed_ops[type(node.op)](_eval(node.operand))
            raise ValueError("Expressao nao suportada")

        try:
            tree = ast.parse(arguments.get("expression", ""), mode="eval")
            result = _eval(tree.body)
            return {"result": result}
        except Exception as exc:
            return {"error": str(exc)}
