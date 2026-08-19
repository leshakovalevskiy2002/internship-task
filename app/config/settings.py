import functools
from urllib.parse import quote

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    user: str = "postgres"
    password: SecretStr
    db: str = "postgres"
    host: str = "localhost"
    port: int = 5432

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", env_file=".env", extra="ignore")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("POSTGRES_PASSWORD cannot be empty")
        return value

    @property
    def url(self) -> str:
        password = quote(self.password.get_secret_value(), safe="")
        user = quote(self.user, safe="")
        db = quote(self.db, safe="")

        return f"postgresql+asyncpg://{user}:{password}@{self.host}:{self.port}/{db}"


class RabbitMQSettings(BaseSettings):
    user: str = "guest"
    password: SecretStr
    host: str = "localhost"
    port: int = 5672
    vhost: str = "/"

    model_config = SettingsConfigDict(env_prefix="RABBITMQ_", env_file=".env", extra="ignore")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("RABBITMQ_PASSWORD cannot be empty")
        return value

    @property
    def url(self) -> str:
        user = quote(self.user, safe="")
        password = quote(self.password.get_secret_value(), safe="")
        vhost = quote(self.vhost, safe="")

        return f"amqp://{user}:{password}@{self.host}:{self.port}/{vhost}"


class RedisSettings(BaseSettings):
    host: str = "localhost"
    port: int = 6379
    password: SecretStr | None = None
    db: int = 0

    model_config = SettingsConfigDict(env_prefix="REDIS_", env_file=".env", extra="ignore")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and not value.get_secret_value().strip():
            raise ValueError("REDIS_PASSWORD cannot be empty")
        return value

    @property
    def url(self) -> str:
        if self.password is None:
            return f"redis://{self.host}:{self.port}/{self.db}"

        password = quote(self.password.get_secret_value(), safe="")

        return f"redis://:{password}@{self.host}:{self.port}/{self.db}"


@functools.lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


@functools.lru_cache
def get_rabbitmq_settings() -> RabbitMQSettings:
    return RabbitMQSettings()


@functools.lru_cache
def get_redis_settings() -> RedisSettings:
    return RedisSettings()
