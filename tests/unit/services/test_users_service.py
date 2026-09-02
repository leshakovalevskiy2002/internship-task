from uuid import uuid4

import pytest

from app.core.enums import UserStatusEnum
from app.models.user import User
from app.services.service_errors.user_errors import (
    UserAlreadyActiveError,
    UserAlreadyBlockedError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.services.users_service import UserService


class TestUserService:
    class TestCreateUserAndBalances:
        async def test_create_user_and_balances_success(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.balances = balances

            users.get_user_by_email.return_value = None

            email = "test@example.com"
            user = User(email=email)
            users.add_user.return_value = user

            service = UserService(uow)

            result = await service.create_user_and_balances(email)

            assert result == user

            users.get_user_by_email.assert_called_once_with(email)
            users.add_user.assert_called_once_with(email)
            balances.create_default_balances_for_user.assert_called_once_with(user.id)

        async def test_create_user_already_exists(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users

            email = "test@example.com"
            existing_user = User(email=email)

            users.get_user_by_email.return_value = existing_user

            service = UserService(uow)

            with pytest.raises(UserAlreadyExistsError):
                await service.create_user_and_balances(email)

            users.get_user_by_email.assert_called_once_with(email)
            users.add_user.assert_not_called()
            uow_context.balances.create_default_balances_for_user.assert_not_called()

        async def test_create_user_propagates_balance_creation_error(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            balances = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.balances = balances

            users.get_user_by_email.return_value = None

            email = "test@example.com"
            user = User(email=email)
            users.add_user.return_value = user
            balances.create_default_balances_for_user.side_effect = Exception("Balance creation failed")

            service = UserService(uow)

            with pytest.raises(Exception, match="Balance creation failed"):
                await service.create_user_and_balances(email)

            users.add_user.assert_called_once_with(email)
            balances.create_default_balances_for_user.assert_called_once_with(user.id)

    class TestChangeUserStatus:
        async def test_change_user_status_success_active_to_blocked(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            session = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.session = session

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)
            users.get_user_by_id.return_value = user

            service = UserService(uow)
            result = await service.change_user_status(user.id, UserStatusEnum.BLOCKED)

            assert result.status == UserStatusEnum.BLOCKED
            users.get_user_by_id.assert_called_once_with(user.id)
            session.flush.assert_awaited_once()
            session.refresh.assert_awaited_once_with(user)

        async def test_change_user_status_success_blocked_to_active(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            session = mocker.AsyncMock()

            uow_contex = uow.__aenter__.return_value
            uow_contex.users = users
            uow_contex.session = session

            user = User(email="test@example.com", status=UserStatusEnum.BLOCKED)
            users.get_user_by_id.return_value = user

            service = UserService(uow)
            result = await service.change_user_status(user.id, UserStatusEnum.ACTIVE)

            assert result.status == UserStatusEnum.ACTIVE
            users.get_user_by_id.assert_called_once_with(user.id)
            session.flush.assert_awaited_once()
            session.refresh.assert_awaited_once_with(user)

        async def test_change_user_status_user_not_found(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            session = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.session = session

            users.get_user_by_id.return_value = None

            service = UserService(uow)

            with pytest.raises(UserNotFoundError):
                await service.change_user_status(user_id=uuid4(), new_status=UserStatusEnum.BLOCKED)

            users.get_user_by_id.assert_called_once()
            session.flush.assert_not_called()
            session.refresh.assert_not_called()

        async def test_change_user_status_user_already_active(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            session = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.session = session

            user = User(email="test@example.com", status=UserStatusEnum.ACTIVE)
            users.get_user_by_id.return_value = user

            service = UserService(uow)

            with pytest.raises(UserAlreadyActiveError):
                await service.change_user_status(user.id, UserStatusEnum.ACTIVE)

            users.get_user_by_id.assert_called_once_with(user.id)
            session.flush.assert_not_called()
            session.refresh.assert_not_called()
            assert user.status == UserStatusEnum.ACTIVE

        async def test_change_user_status_user_already_blocked(self, mocker):
            uow = mocker.AsyncMock()
            users = mocker.AsyncMock()
            session = mocker.AsyncMock()

            uow_context = uow.__aenter__.return_value
            uow_context.users = users
            uow_context.session = session

            user = User(email="test@example.com", status=UserStatusEnum.BLOCKED)
            users.get_user_by_id.return_value = user

            service = UserService(uow)

            with pytest.raises(UserAlreadyBlockedError):
                await service.change_user_status(user.id, UserStatusEnum.BLOCKED)

            users.get_user_by_id.assert_called_once_with(user.id)
            session.flush.assert_not_called()
            session.refresh.assert_not_called()
            assert user.status == UserStatusEnum.BLOCKED
