from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.tasks.reports import generate_report

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        generate_report.send,
        "interval",
        minutes=10,
        id="transaction_report",
        replace_existing=True,
    )

    scheduler.start()
