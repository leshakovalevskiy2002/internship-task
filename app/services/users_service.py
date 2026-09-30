from uuid import UUID

from asyncpg import UniqueViolationError
from sqlalchemy.exc import IntegrityError

from app.core.enums import UserStatusEnum
from app.models.user import User
from app.services.service_errors.user_errors import (
    UserAlreadyActiveError,
    UserAlreadyBlockedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.uow import UnitOfWork


class UserService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create_user_and_balances(self, email: str) -> User:
        try:
            async with self.uow as uow:
                existing_user = await uow.users.get_user_by_email(email)

                if existing_user:
                    raise UserAlreadyExistsError(email)

                new_user = await uow.users.add_user(email)
                await uow.balances.create_default_balances_for_user(new_user.id)
                return new_user

        except IntegrityError as exc:
            if exc.orig is None:
                raise

            original_exc = exc.orig.__cause__

            if isinstance(original_exc, UniqueViolationError):
                if getattr(original_exc, "constraint_name") == "users_email_key":
                    raise UserAlreadyExistsError(email) from exc
            raise

    async def update_user_status(self, user_id: UUID, new_status: UserStatusEnum) -> User:
        async with self.uow as uow:
            user = await uow.users.get_user_by_id(user_id)

            if user is None:
                raise UserNotFoundError(user_id)

            if user.status == new_status:
                if user.status == UserStatusEnum.BLOCKED:
                    raise UserAlreadyBlockedError(user_id)

                raise UserAlreadyActiveError(user_id)

            user.status = new_status

            await uow.session.flush()
            await uow.session.refresh(user)

            return user
