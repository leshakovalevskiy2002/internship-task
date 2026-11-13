import dramatiq
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.config.database import create_engine, create_session_maker
from app.config.redis import create_redis
from app.services.report_generation_service import ReportGenerationService
from app.uow import UnitOfWork

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker | None = None
_redis: Redis | None = None


def _get_session_maker() -> async_sessionmaker:
    global _engine, _session_maker
    if _session_maker is None:
        _engine = create_engine()
        _session_maker = create_session_maker(_engine)
    return _session_maker


def _get_redis():
    global _redis
    if _redis is None:
        _redis = create_redis()
    return _redis


@dramatiq.actor(queue_name="reports")
async def generate_report(lock_id: str | None = None, lock_key: str | None = None):
    redis = _get_redis()

    try:
        async with UnitOfWork(_get_session_maker()) as uow:
            service = ReportGenerationService(uow=uow, redis=redis)
            await service.generate_year_report()
    finally:
        if lock_id and lock_key:
            current_lock = await redis.get(lock_key)

            if current_lock == lock_id:
                await redis.delete(lock_key)
