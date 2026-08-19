from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import get_report_query_service
from app.services.report_query_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/analysis", status_code=status.HTTP_200_OK)
async def get_analytics(service: Annotated[ReportService, Depends(get_report_query_service)]):
    return await service.get_report()
