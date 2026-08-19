from fastapi import APIRouter

from app.api.v1.routers import reports, transactions, users

router = APIRouter(prefix="/v1")

router.include_router(users.router)
router.include_router(transactions.router)
router.include_router(reports.router)

__all__ = ["router"]
