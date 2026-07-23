from fastapi import APIRouter

from app.api.v1.routers import transactions, users

router = APIRouter(prefix="/v1")

router.include_router(users.router)
router.include_router(transactions.router)

__all__ = ["router"]
