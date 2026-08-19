import json

from app.tasks.reports import generate_report

prefix = "/api/v1/reports"


class TestGetAnalytics:
    async def test_returns_cached_report(self, client_with_redis, redis):
        report = {
            "generated_at": "2026-08-15T10:00:00+00:00",
            "data": [
                {
                    "start_date": "2026-08-03",
                    "end_date": "2026-08-09",
                    "registered_users_count": 10,
                }
            ],
        }

        await redis.set("report:aggregated:data", json.dumps(report))

        response = await client_with_redis.get(f"{prefix}/analysis")

        assert response.status_code == 200
        assert response.json() == report

    async def test_starts_report_generation_when_cache_is_empty(self, client_with_redis, redis, mocker):
        send_mock = mocker.patch.object(generate_report, "send")

        response = await client_with_redis.get(f"{prefix}/analysis")

        assert response.status_code == 200
        assert response.json() == {"status": "generating"}

        lock_id = await redis.get("report:analysis:lock")

        assert lock_id is not None

        send_mock.assert_called_once_with(lock_id, "report:analysis:lock")

    async def test_does_not_start_generation_when_lock_exists(self, client_with_redis, redis, mocker):
        send_mock = mocker.patch.object(generate_report, "send")
        existing_lock_id = "already-running"

        await redis.set("report:analysis:lock", existing_lock_id, ex=600)

        response = await client_with_redis.get(f"{prefix}/analysis")

        assert response.status_code == 200
        assert response.json() == {"status": "generating"}

        send_mock.assert_not_called()

        assert await redis.get("report:analysis:lock") == existing_lock_id
