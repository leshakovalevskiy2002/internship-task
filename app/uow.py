from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.balances import BalanceRepository
from app.repositories.transactions import TransactionRepository
from app.repositories.users import UserRepository


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> Self:
        self._session = self.session_factory()

        self.balances = BalanceRepository(self.session)
        self.transactions = TransactionRepository(self.session)
        self.users = UserRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
        finally:
            await self.close()
            self._session = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UoW is not started")

        return self._session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def close(self) -> None:
        await self.session.close()
