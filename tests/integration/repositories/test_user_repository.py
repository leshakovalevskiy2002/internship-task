from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from app.core.enums import CurrencyEnum, UserStatusEnum
from app.models.user import User
from app.repositories.users import UserRepository


class TestUserRepository:
    async def test_get_user_by_email(self, user_repository: UserRepository, user_factory):
        user = await user_factory()

        find_user = await user_repository.get_user_by_email(user.email)
        assert find_user is not None
        assert find_user.email == user.email

    async def test_get_user_by_email_returns_none_when_not_found(self, user_repository: UserRepository):
        find_user = await user_repository.get_user_by_email("not-found@test.com")
        assert find_user is None

    async def test_get_user_by_id(self, user_repository: UserRepository, user_factory):
        user = await user_factory()

        find_user = await user_repository.get_user_by_id(user.id)
        assert find_user is not None
        assert find_user.id == user.id

    async def test_get_user_by_id_returns_none_when_not_found(self, user_repository: UserRepository):
        find_user = await user_repository.get_user_by_id(uuid4())
        assert find_user is None

    async def test_get_users_with_balances_returns_all_users(self, user_repository, user_factory):
        user1 = await user_factory(email="first@test.com", created=datetime(2026, 1, 1))
        user2 = await user_factory(email="second@test.com", created=datetime(2025, 1, 1))

        users = await user_repository.get_users_with_balances()

        assert len(users) == 2
        assert [u.email for u in users] == [user2.email, user1.email]

    async def test_get_users_with_balances_filters_by_id(self, user_repository, user_factory):
        user1 = await user_factory(email="first@test.com")
        await user_factory(email="second@test.com")

        users = await user_repository.get_users_with_balances(user_id=user1.id)

        assert len(users) == 1
        assert users[0].id == user1.id

    async def test_get_users_with_balances_filters_by_email(self, user_repository, user_factory):
        await user_factory(email="first@test.com")
        u2 = await user_factory(email="second@test.com")

        users = await user_repository.get_users_with_balances(email="second@test.com")

        assert len(users) == 1
        assert users[0].email == u2.email

    async def test_get_users_with_balances_filters_by_status(self, user_repository, user_factory):
        await user_factory(email="active@test.com")
        await user_factory(email="blocked@test.com", status=UserStatusEnum.BLOCKED)
        await user_factory(email="active2@test.com")

        users = await user_repository.get_users_with_balances(user_status=UserStatusEnum.BLOCKED)

        assert len(users) == 1
        assert users[0].status == UserStatusEnum.BLOCKED

    async def test_get_users_with_balances_filters_by_email_and_status(self, user_repository, user_factory):
        user = await user_factory(email="test@test.com")
        await user_factory(email="test2@test.com", status=UserStatusEnum.BLOCKED)
        await user_factory(email="test3@test.com")

        users = await user_repository.get_users_with_balances(
            email="test@test.com",
            user_status=UserStatusEnum.ACTIVE,
        )

        assert len(users) == 1
        assert users[0].id == user.id
        assert users[0].email == "test@test.com"
        assert users[0].status == UserStatusEnum.ACTIVE

    async def test_get_users_with_balances_loads_balances(self, user_repository, user_factory_with_balances):
        user = await user_factory_with_balances()

        users = await user_repository.get_users_with_balances(user.id)

        assert users
        assert len(users[0].user_balances) == len(CurrencyEnum)

    async def test_add_user(self, user_repository: UserRepository):
        session = user_repository.session

        email = "test@example.com"
        await user_repository.add_user(email)

        db_user = (await session.scalars(select(User).where(User.email == email))).one_or_none()

        assert db_user is not None
        assert db_user.email == email
