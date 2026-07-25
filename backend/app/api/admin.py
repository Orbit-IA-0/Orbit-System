"""
Endpoints do painel administrativo: usuarios, uso/custo por modelo, logs de plugins.
Protegidos por get_current_admin (apenas usuarios com is_admin=True).
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_admin
from app.database import get_db
from app.models import PluginLog, UsageLog, User

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
async def list_users(admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": u.id, "email": u.email, "full_name": u.full_name,
            "is_admin": u.is_admin, "is_active": u.is_active,
            "preferred_model": u.preferred_model, "created_at": u.created_at,
        }
        for u in users
    ]


@router.patch("/users/{user_id}/toggle-active")
async def toggle_user_active(user_id: str, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.is_active = not user.is_active
        await db.commit()
    return {"id": user_id, "is_active": user.is_active if user else None}


@router.get("/usage/summary")
async def usage_summary(days: int = 30, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)

    by_model = await db.execute(
        select(
            UsageLog.model,
            func.count(UsageLog.id).label("requests"),
            func.sum(UsageLog.tokens_input).label("tokens_input"),
            func.sum(UsageLog.tokens_output).label("tokens_output"),
            func.sum(UsageLog.cost_usd).label("cost_usd"),
            func.avg(UsageLog.latency_ms).label("avg_latency_ms"),
        )
        .where(UsageLog.created_at >= since)
        .group_by(UsageLog.model)
    )

    totals = await db.execute(
        select(
            func.count(UsageLog.id),
            func.coalesce(func.sum(UsageLog.cost_usd), 0),
        ).where(UsageLog.created_at >= since)
    )
    total_requests, total_cost = totals.one()

    return {
        "period_days": days,
        "total_requests": total_requests,
        "total_cost_usd": float(total_cost),
        "by_model": [
            {
                "model": row.model,
                "requests": row.requests,
                "tokens_input": row.tokens_input or 0,
                "tokens_output": row.tokens_output or 0,
                "cost_usd": float(row.cost_usd or 0),
                "avg_latency_ms": float(row.avg_latency_ms or 0),
            }
            for row in by_model
        ],
    }


@router.get("/logs/plugins")
async def plugin_logs(limit: int = 100, admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PluginLog).order_by(PluginLog.created_at.desc()).limit(limit))
    logs = result.scalars().all()
    return [
        {
            "id": log.id, "plugin_name": log.plugin_name, "success": log.success,
            "input_payload": log.input_payload, "output_payload": log.output_payload,
            "created_at": log.created_at,
        }
        for log in logs
    ]
