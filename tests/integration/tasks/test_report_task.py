import asyncio
import json

import pytest

from app.services.report_query_service import ReportService
from app.tasks.reports import generate_report


@pytest.mark.asyncio
async def test_generate_report_task(dramatiq_worker, dramatiq_broker, redis, monkeypatch, session_maker):
    lock_id = "redis-lock"
    lock_key = ReportService.REPORT_LOCK_KEY
    cache_key = ReportService.REPORT_CACHE_KEY

    await redis.set(lock_key, lock_id, nx=True, ex=600)

    message = generate_report.send(lock_id, lock_key)

    assert message.message_id

    report = lock = None

    for _ in range(30):
        report = await redis.get(cache_key)
        lock = await redis.get(lock_key)

        if report is not None and lock is None:
            break

        await asyncio.sleep(0.5)
    else:
        pytest.fail("Report was not generated within 15 seconds")

    assert report is not None
    assert lock is None

    report_data = json.loads(report)

    assert "generated_at" in report_data
    assert "data" in report_data
    assert type(report_data["data"]) == list
