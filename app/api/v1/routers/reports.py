from textwrap import dedent
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import get_report_query_service
from app.services.report_query_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get(
    "/analysis",
    description=dedent(
        """
        Returns an aggregated analytics report for the last 52 completed weeks.

        The report is generated asynchronously and cached in Redis.

        **Behavior:**
        - If a cached report exists, it is returned immediately (`report_ready`).
        - Otherwise, generation starts in the background and the endpoint returns
          a generation status (`report_generating`).

        **Report Generation:**
        - Covers 52 **completed** weeks; the current incomplete week is excluded.
        - The period starts with the completed week immediately preceding the current week
          and goes back 52 weeks.
        - Each weekly entry contains aggregated user and transaction statistics.

        **Caching & Concurrency:**
        - Generated reports are stored in Redis.
        - If a report is already cached, no new generation task is started.
        - If the cache is empty, a Redis lock is acquired before starting generation,
          preventing duplicate concurrent tasks.
        - The generation lock expires after **600 seconds**.
        - When generation completes, the lock is removed and the report is cached.
        """
    ),
    status_code=status.HTTP_200_OK,
    summary="Get analytics report",
)
async def get_analytics(service: Annotated[ReportService, Depends(get_report_query_service)]):
    return await service.get_report()
