from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import UserStatusEnum
from database import get_async_session
from schemas.users import (
    RequestUserModel,
    RequestUserUpdateModel,
    ResponseUserBalanceModel,
    ResponseUserModel,
    UserModel,
)
from services.users_service import UserService
from services.user_errors import (
    UserAlreadyActiveError,
    UserAlreadyBlockedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[ResponseUserModel], status_code=status.HTTP_200_OK)
async def get_all_users_and_their_balances(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user_id: Annotated[int | None, Query(description="Filter by user_id", gt=0)] = None,
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
    try:
        return await user_service.create_user_and_balances(new_user_data.email)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.patch("/{user_id}", response_model=UserModel)
async def update_user_status(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user_id: Annotated[int, Path(gt=0)],
    user: RequestUserUpdateModel,
):
    user_service = UserService(session)
    try:
        return await user_service.update_user_status(user_id=user_id, new_status=user.status)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except (UserAlreadyBlockedError, UserAlreadyActiveError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
