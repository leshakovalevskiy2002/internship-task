from redis.asyncio import Redis

from app.config.settings import get_redis_settings


def create_redis() -> Redis:
    redis_settings = get_redis_settings()
    return Redis.from_url(redis_settings.url, decode_responses=True)
