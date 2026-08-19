import json
from datetime import date, datetime, timezone
from decimal import Decimal

from freezegun import freeze_time

from app.repositories.reports import WeeklyStatistics
from app.schemas.reports import WeeklyReport
from app.services.report_generation_service import ReportGenerationService


class TestReportGenerationService:
    async def test_build_report(self):
        stats = WeeklyStatistics(
            registered_users={
                date(2026, 8, 3): 100,
                date(2026, 7, 27): 90,
            },
            deposit_users={
                date(2026, 8, 3): 50,
            },
            deposit_amount={
                date(2026, 8, 3): Decimal("1000.00"),
            },
            withdraw_amount={
                date(2026, 8, 3): Decimal("300.50"),
            },
            transactions={
                date(2026, 8, 3): 200,
            },
            not_roll_backed_transactions={
                date(2026, 8, 3): 180,
            },
        )

        result = ReportGenerationService._build_report(stats, last_date=date(2026, 8, 3), weeks=2)

        assert result == [
            WeeklyReport(
                start_date=date(2026, 8, 3),
                end_date=date(2026, 8, 9),
                registered_users_count=100,
                deposit_users_count=50,
                not_roll_backed_deposit_amount=Decimal("1000.00"),
                not_roll_backed_withdraw_amount=Decimal("300.50"),
                transactions_count=200,
                not_roll_backed_transactions_count=180,
            ),
            WeeklyReport(
                start_date=date(2026, 7, 27),
                end_date=date(2026, 8, 2),
                registered_users_count=90,
                deposit_users_count=0,
                not_roll_backed_deposit_amount=Decimal("0.00"),
                not_roll_backed_withdraw_amount=Decimal("0.00"),
                transactions_count=0,
                not_roll_backed_transactions_count=0,
            ),
        ]

    async def test_save_report_to_cache(self, mocker):
        report = [
            WeeklyReport(
                start_date=date(2026, 8, 3),
                end_date=date(2026, 8, 9),
                registered_users_count=100,
                deposit_users_count=50,
                not_roll_backed_deposit_amount=Decimal("1000.00"),
                not_roll_backed_withdraw_amount=Decimal("300.50"),
                transactions_count=200,
                not_roll_backed_transactions_count=180,
            )
        ]

        report_repo = mocker.AsyncMock()
        redis = mocker.AsyncMock()
        service = ReportGenerationService(report_repo, redis)

        await service.save_report_to_cache(report)

        redis.set.assert_awaited_once()
        key, payload = redis.set.await_args.args

        assert key == service.REPORT_CACHE_KEY

        data = json.loads(payload)

        assert data["data"] == [
            {
                "start_date": "2026-08-03",
                "end_date": "2026-08-09",
                "registered_users_count": 100,
                "deposit_users_count": 50,
                "not_roll_backed_deposit_amount": "1000.00",
                "not_roll_backed_withdraw_amount": "300.50",
                "transactions_count": 200,
                "not_roll_backed_transactions_count": 180,
            }
        ]

        generated_at = datetime.fromisoformat(data["generated_at"])
        assert generated_at.tzinfo == timezone.utc

    @freeze_time("2026-08-15")
    async def test_generate_year_report(self, mocker):
        report_repo = mocker.AsyncMock()
        redis = mocker.AsyncMock()
        service = ReportGenerationService(report_repo, redis)

        save_report_mock = mocker.AsyncMock()

        stats = WeeklyStatistics(
            registered_users={
                date(2026, 8, 3): 100,
            },
            deposit_users={
                date(2026, 8, 3): 50,
            },
            deposit_amount={
                date(2026, 8, 3): Decimal("1000.00"),
            },
            withdraw_amount={
                date(2026, 8, 3): Decimal("300.00"),
            },
            transactions={
                date(2026, 8, 3): 200,
            },
            not_roll_backed_transactions={
                date(2026, 8, 3): 180,
            },
        )

        report_repo.get_weekly_statistics.return_value = stats
        service.save_report_to_cache = save_report_mock

        await service.generate_year_report()

        report_repo.get_weekly_statistics.assert_awaited_once_with(
            date(2025, 8, 11),
            date(2026, 8, 10),
        )

        save_report_mock.assert_awaited_once()

        report = save_report_mock.await_args.args[0]

        assert report[0] == WeeklyReport(
            start_date=date(2026, 8, 3),
            end_date=date(2026, 8, 9),
            registered_users_count=100,
            deposit_users_count=50,
            not_roll_backed_deposit_amount=Decimal("1000.00"),
            not_roll_backed_withdraw_amount=Decimal("300.00"),
            transactions_count=200,
            not_roll_backed_transactions_count=180,
        )
