import json
from unittest.mock import patch

from app.services.report_query_service import ReportService


class TestReportService:
    async def test_get_report_returns_cached_report(self, mocker):
        redis = mocker.AsyncMock()

        report = {"registered_users": {"2026-08-03": 100}}
        redis.get.return_value = json.dumps(report)

        service = ReportService(redis)

        with patch("app.services.report_query_service.generate_report.send") as send:
            result = await service.get_report()

        assert result == report

        redis.get.assert_called_once_with(ReportService.REPORT_CACHE_KEY)
        redis.set.assert_not_awaited()
        send.assert_not_called()

    async def test_get_report_starts_generation_when_cache_is_missing(self, mocker):
        redis = mocker.AsyncMock()

        redis.get.return_value = None
        redis.set.return_value = True

        service = ReportService(redis)

        with patch("app.services.report_query_service.generate_report.send") as send:
            result = await service.get_report()

        assert result == {"status": "generating"}

        send.assert_called_once()
        lock_id, lock_key = send.call_args.args

        assert isinstance(lock_id, str)
        assert len(lock_id) == 32
        assert lock_key == ReportService.REPORT_LOCK_KEY

        redis.set.assert_awaited_once_with(ReportService.REPORT_LOCK_KEY, lock_id, nx=True, ex=600)

    async def test_get_report_does_not_start_generation_when_lock_exists(self, mocker):
        redis = mocker.AsyncMock()

        redis.get.return_value = None
        redis.set.return_value = None

        service = ReportService(redis)

        with patch("app.services.report_query_service.generate_report.send") as send:
            result = await service.get_report()

        assert result == {"status": "generating"}
        redis.set.assert_awaited_once()
        send.assert_not_called()
