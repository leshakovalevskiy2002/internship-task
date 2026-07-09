import functools
from collections.abc import AsyncGenerator

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base


class DatabaseSettings(BaseSettings):
    user: str | None = None
    password: SecretStr | None = None
    db: str | None = None
    host: str = "localhost"
    port: int = 5432

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", env_file=".env")

    @model_validator(mode="after")
    def validate_required(self):
        if self.user is None:
            raise ValueError("POSTGRES_USER must be set in environment")
        if self.password is None:
            raise ValueError("POSTGRES_PASSWORD must be set in environment")
        if self.db is None:
            raise ValueError("POSTGRES_DB must be set in environment")
        return self

    def url(self) -> str:
        if self.password is None:
            raise ValueError("POSTGRES_PASSWORD must be set in environment")
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}" f"@{self.host}:{self.port}/{self.db}"
        )


@functools.lru_cache()
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


settings = get_database_settings()
engine = create_async_engine(settings.url(), echo=True)

async_session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("SET TIME ZONE 'UTC'"))
