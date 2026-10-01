from unittest.mock import AsyncMock, MagicMock

import pytest

from app.uow import UnitOfWork


@pytest.fixture
def session():
    return AsyncMock()


@pytest.fixture
def session_maker(session):
    return MagicMock(return_value=session)


@pytest.fixture
def uow(session_maker):
    return UnitOfWork(session_maker)
