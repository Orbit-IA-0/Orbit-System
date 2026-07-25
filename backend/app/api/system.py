"""Endpoints de status e versao/changelog (sistema de atualizacao automatica do app)."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import AppVersion

router = APIRouter(prefix="/api", tags=["system"])
settings = get_settings()


@router.get("/status")
async def status():
    return {"status": "ok", "environment": settings.ENVIRONMENT, "app": settings.APP_NAME}


@router.get("/version")
async def version(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AppVersion).order_by(AppVersion.released_at.desc()))
    versions = result.scalars().all()
    return {
        "current_version": settings.APP_VERSION,
        "changelog": [
            {"version": v.version, "changelog": v.changelog, "released_at": v.released_at}
            for v in versions
        ],
    }
