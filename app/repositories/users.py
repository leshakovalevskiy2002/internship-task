from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import UserStatusEnum
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_user_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.session.scalars(query)
        return result.one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        query = select(User).where(User.id == user_id)
        result = await self.session.scalars(query)
        return result.one_or_none()

    async def get_users_with_balances(
        self,
        user_id: UUID | None = None,
        email: str | None = None,
        user_status: UserStatusEnum | None = None,
    ) -> Sequence[User]:
        query = select(User).options(selectinload(User.user_balances)).order_by(User.created)

        if user_id is not None:
            query = query.where(User.id == user_id)
        if email is not None:
            query = query.where(User.email == email)
        if user_status is not None:
            query = query.where(User.status == user_status)

        result = await self.session.scalars(query)
        return result.all()

    async def update_user_status(self, user: User, status: UserStatusEnum) -> User:
        user.status = status
        await self.session.flush()
        return user

    async def create_user(self, email: str) -> User:
        new_user = User(email=email)
        self.session.add(new_user)
        await self.session.flush()
        return new_user
