"""Ponto unico de registro de todos os plugins disponiveis na Orbit IA."""
from app.plugins.base import registry
from app.plugins.web_search_plugin import CalculatorPlugin, GetDateTimePlugin, WebSearchPlugin


def setup_plugins():
    registry.register(WebSearchPlugin())
    registry.register(GetDateTimePlugin())
    registry.register(CalculatorPlugin())
