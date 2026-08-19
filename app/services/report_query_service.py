import json
import uuid

from redis.asyncio import Redis

from app.tasks.reports import generate_report


class ReportService:
    REPORT_CACHE_KEY = "report:aggregated:data"
    REPORT_LOCK_KEY = "report:analysis:lock"

    def __init__(self, redis: Redis):
        self.redis = redis

    async def get_report(self):
        report = await self.redis.get(self.REPORT_CACHE_KEY)

        if report:
            return json.loads(report)

        lock_id = uuid.uuid4().hex

        lock = await self.redis.set(self.REPORT_LOCK_KEY, lock_id, nx=True, ex=600)

        if lock:
            generate_report.send(lock_id, self.REPORT_LOCK_KEY)

        return {"status": "generating"}
