import asyncio

from app.scheduler.reports import scheduler, start_scheduler


async def main():
    start_scheduler()

    try:
        await asyncio.Event().wait()
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
