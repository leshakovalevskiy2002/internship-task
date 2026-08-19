import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from redis.asyncio import Redis

from app.repositories.reports import ReportRepository, WeeklyStatistics
from app.schemas.reports import WeeklyReport


class ReportGenerationService:
    REPORT_CACHE_KEY = "report:aggregated:data"

    def __init__(self, report_repo: ReportRepository, redis: Redis):
        self.report_repo = report_repo
        self.redis = redis

    async def generate_year_report(self) -> None:
        today = datetime.now(timezone.utc).date()
        current_week = today - timedelta(days=today.weekday())
        last_completed_week = current_week - timedelta(weeks=1)

        start_date = last_completed_week - timedelta(weeks=51)
        end_date = current_week

        stats = await self.report_repo.get_weekly_statistics(start_date, end_date)
        report = self._build_report(stats, last_date=last_completed_week)
        await self.save_report_to_cache(report)

    @staticmethod
    def _build_report(stats: WeeklyStatistics, last_date: date, weeks: int = 52) -> list[WeeklyReport]:
        report: list[WeeklyReport] = []

        for _ in range(weeks):
            week_start = last_date
            week_end = week_start + timedelta(days=6)

            one_week_report = WeeklyReport(
                start_date=week_start,
                end_date=week_end,
                registered_users_count=stats.registered_users.get(last_date, 0),
                deposit_users_count=stats.deposit_users.get(last_date, 0),
                not_roll_backed_deposit_amount=stats.deposit_amount.get(last_date, Decimal("0.00")),
                not_roll_backed_withdraw_amount=stats.withdraw_amount.get(last_date, Decimal("0.00")),
                transactions_count=stats.transactions.get(last_date, 0),
                not_roll_backed_transactions_count=stats.not_roll_backed_transactions.get(last_date, 0),
            )

            report.append(one_week_report)
            last_date = last_date - timedelta(weeks=1)

        return report

    async def save_report_to_cache(self, report: list[WeeklyReport]) -> None:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data": [item.model_dump(mode="json") for item in report],
        }

        await self.redis.set(self.REPORT_CACHE_KEY, json.dumps(payload))
