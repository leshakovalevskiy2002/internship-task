from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_async_session
from app.core.enums import UserStatusEnum
from app.schemas.users import (
    RequestUserModel,
    RequestUserUpdateModel,
    ResponseUserBalanceModel,
    ResponseUserModel,
    UserModel,
)
from app.services.users_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[ResponseUserModel], status_code=status.HTTP_200_OK)
async def get_all_users_and_their_balances(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user_id: Annotated[UUID | None, Query(description="Filter by user_id")] = None,
    email: Annotated[str | None, Query(description="Filter by email")] = None,
    user_status: Annotated[UserStatusEnum | None, Query(description="Filter by user status")] = None,
) -> list[ResponseUserModel]:
    user_service = UserService(session)
    users = await user_service.get_users_with_balances(user_id=user_id, email=email, user_status=user_status)
    return [
        ResponseUserModel(
            id=user.id,
            email=user.email,
            status=user.status,
            created=user.created,
            balances=sorted(
                (ResponseUserBalanceModel(currency=b.currency, amount=b.amount) for b in user.user_balances),
                key=lambda x: x.amount,
            ),
        )
        for user in users
    ]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserModel)
async def create_user_and_his_balances(
    new_user_data: RequestUserModel, session: Annotated[AsyncSession, Depends(get_async_session)]
):
    user_service = UserService(session)
    return await user_service.create_user_and_balances(new_user_data.email)


@router.patch("/{user_id}", response_model=UserModel)
async def update_user_status(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user_id: UUID,
    user: RequestUserUpdateModel,
):
    user_service = UserService(session)
    return await user_service.update_user_status(user_id=user_id, new_status=user.status)
