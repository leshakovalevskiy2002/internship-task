import pytest


class TestUnitOfWork:
    async def test_session_before_enter_raises(self, uow):
        with pytest.raises(RuntimeError, match="UoW is not started"):
            _ = uow.session

    async def test_enter_creates_sessions_and_repositories(self, uow, session):
        async with uow:
            assert uow.session is session

            assert uow.users.session is session
            assert uow.balances.session is session
            assert uow.transactions.session is session

    async def test_uow_commits_on_success(self, uow, session):
        async with uow:
            pass

        session.commit.assert_called_once()
        session.rollback.assert_not_called()
        session.close.assert_called_once()

        assert uow._session is None

    async def test_uow_rolls_back_on_exception(self, uow, session):
        with pytest.raises(ValueError, match="test error"):
            async with uow:
                raise ValueError("test error")

        session.rollback.assert_called_once()
        session.commit.assert_not_called()
        session.close.assert_called_once()

        assert uow._session is None
