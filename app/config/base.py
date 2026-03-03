import functools

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataBaseSettings(BaseSettings):
    user: str | None = None
    password: SecretStr | None = None
    db: str | None = None
    host: str = "localhost"
    port: int = 5432

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", env_file="../../.env")

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
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}" f"@{self.host}:{self.port}/{self.db}"
        )


@functools.lru_cache()
def get_database_settings() -> DataBaseSettings:
    return DataBaseSettings()
