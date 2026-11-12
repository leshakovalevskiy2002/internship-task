from operator import attrgetter
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.enums import UserStatusEnum
from app.dependencies import UserServiceDep, get_user_repo
from app.repositories.users import UserRepository
from app.schemas.balances import UserBalanceResponse
from app.schemas.users import (
    UpdateUserStatusRequest,
    UserRegistrationRequest,
    UserResponse,
    UserWithBalancesResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def registration(user_data: UserRegistrationRequest, user_service: UserServiceDep):
    return await user_service.create_user_and_balances(user_data.email)


@router.get("", response_model=list[UserWithBalancesResponse], status_code=status.HTTP_200_OK)
async def get_users_with_balances(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    user_id: Annotated[UUID | None, Query(description="Filter by user_id")] = None,
    email: Annotated[str | None, Query(description="Filter by email")] = None,
    user_status: Annotated[UserStatusEnum | None, Query(description="Filter by user status")] = None,
):
    users_with_balances = await user_repo.get_users_with_balances(user_id=user_id, email=email, user_status=user_status)
    return [
        UserWithBalancesResponse(
            id=user.id,
            email=user.email,
            status=user.status,
            created=user.created,
            updated=user.updated,
            balances=[
                UserBalanceResponse.model_validate(balance)
                for balance in sorted(user.user_balances, key=attrgetter("amount"))
            ],
        )
        for user in users_with_balances
    ]


@router.patch("/{user_id}", response_model=UserResponse)
async def change_user_status(user_service: UserServiceDep, user_id: UUID, user: UpdateUserStatusRequest):
    return await user_service.change_user_status(user_id=user_id, new_status=user.status)
