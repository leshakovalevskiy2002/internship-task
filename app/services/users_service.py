from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserStatusEnum
from app.models import User
from app.repositories.balances import BalanceRepository
from app.repositories.users import UserRepository
from app.services.service_errors.user_errors import (
    UserAlreadyActiveError,
    UserAlreadyBlockedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.balance_repo = BalanceRepository(session)

    async def get_users_with_balances(
        self,
        user_id: int | None = None,
        email: str | None = None,
        user_status: UserStatusEnum | None = None,
    ) -> Sequence[User]:
        return await self.user_repo.get_users_with_balances(user_id=user_id, email=email, user_status=user_status)

    async def create_user_and_balances(self, email: str) -> User:
        existing_user = await self.user_repo.get_user_by_email(email)
        if existing_user is not None:
            raise UserAlreadyExistsError(email)

        new_user = await self.user_repo.create_user(email)
        await self.balance_repo.create_default_balances_for_user(new_user.id)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def update_user_status(self, user_id: int, new_status: UserStatusEnum) -> User:
        db_user = await self.user_repo.get_user_by_id(user_id)
        if db_user is None:
            raise UserNotFoundError(user_id)

        if db_user.status == new_status:
            if db_user.status == UserStatusEnum.BLOCKED:
                raise UserAlreadyBlockedError(user_id)
            raise UserAlreadyActiveError(user_id)

        await self.user_repo.update_user_status(db_user, new_status)
        await self.session.commit()
        await self.session.refresh(db_user)
        return db_user
