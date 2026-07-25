"""Endpoint REST de busca na web, reutilizando o plugin web_search diretamente (fora do chat)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.deps import get_current_user
from app.models import User
from app.plugins.web_search_plugin import WebSearchPlugin

router = APIRouter(prefix="/api/search", tags=["search"])
_plugin = WebSearchPlugin()


class SearchRequest(BaseModel):
    query: str


@router.post("")
async def search(payload: SearchRequest, user: User = Depends(get_current_user)):
    result = await _plugin.run({"query": payload.query})
    return result
