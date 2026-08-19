import dramatiq

from app.config.database import create_session_maker, engine
from app.config.redis import create_redis
from app.repositories.reports import ReportRepository
from app.services.report_generation_service import ReportGenerationService


@dramatiq.actor
async def generate_report(lock_id: str | None = None, lock_key: str | None = None):
    redis = create_redis()

    try:
        async_session_maker = create_session_maker(engine)

        async with async_session_maker() as session:
            repo = ReportRepository(session=session)
            service = ReportGenerationService(report_repo=repo, redis=redis)

            await service.generate_year_report()
    finally:
        if lock_id and lock_key:
            current_lock = await redis.get(lock_key)

            if current_lock == lock_id:
                await redis.delete(lock_key)

        await redis.aclose()
