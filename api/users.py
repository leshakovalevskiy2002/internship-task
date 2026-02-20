from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import CurrencyEnum, UserStatusEnum
from database import get_async_session
from exceptions.common_exceptions import BadRequestDataException
from exceptions.user_exceptions import (
    UserAlreadyActiveException,
    UserAlreadyBlockedException,
    UserAlreadyExistsException,
    UserNotExistsException,
)
from models.balance import UserBalance
from models.user import User
from schemas.users import RequestUserModel, RequestUserUpdateModel, ResponseUserModel, UserModel

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[ResponseUserModel] | None, status_code=status.HTTP_200_OK)
async def get_users(
    user_id: int | None = None,
    email: str | None = None,
    user_status: str | None = None,
    session: AsyncSession = Depends(get_async_session),
) -> list[ResponseUserModel]:
    q = select(User).order_by(User.created.desc())
    if user_id is not None:
        q = q.where(User.id == user_id)
    if email is not None:
        q = q.where(User.email == email)
    if user_status is not None:
        q = q.where(User.status == user_status)
    users = await session.execute(q)
    users = users.scalars()
    results = []
    for user in users:
        result = ResponseUserModel(
            id=user.id, email=user.email, status=UserStatusEnum(user.status), created=user.created
        )
        balances = await session.execute(select(UserBalance).where(UserBalance.user_id == user.id))
        balances = balances.scalars()
        balances = sorted([{"currency": b.currency, "amount": b.amount} for b in balances], key=lambda x: x["amount"])
        result.balances = balances
        results.append(result)
    return sorted(results, key=lambda x: x.created)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserModel)
async def create_user_and_his_balances(
    new_user_data: RequestUserModel, session: Annotated[AsyncSession, Depends(get_async_session)]
):
    email = new_user_data.email

    result = await session.execute(select(User).where(User.email == email))
    db_user = result.scalar()

    if db_user is not None:
        raise UserAlreadyExistsException(
            status_code=status.HTTP_409_CONFLICT, detail=f"User with email=`{email}` already exists"
        )

    new_user = User(email=email)
    session.add(new_user)
    await session.commit()

    for currency in CurrencyEnum:
        user_balance = UserBalance(user_id=new_user.id, currency=currency)
        session.add(user_balance)

    await session.commit()
    await session.refresh(new_user)
    return new_user


@router.patch("/{user_id}", response_model=UserModel)
async def update_user_status(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user_id: int,
    user: RequestUserUpdateModel,
):
    if user_id < 0:
        raise BadRequestDataException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unprocessable data in request"
        )

    result = await session.execute(select(User).where(User.id == user_id))
    db_user = result.scalar()
    if db_user is None:
        raise UserNotExistsException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id=`{user_id}` does not exist"
        )

    if db_user.status == user.status:
        if db_user.status == UserStatusEnum.BLOCKED:
            raise UserAlreadyBlockedException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with id=`{user_id}` is already blocked"
            )
        elif db_user.status == UserStatusEnum.ACTIVE:
            raise UserAlreadyActiveException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"User with id=`{user_id}` is already active"
            )
    else:
        db_user.status = user.status
        await session.commit()
        await session.refresh(db_user)
        return db_user
