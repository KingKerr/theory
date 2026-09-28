from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    MASSIVE_API_KEY: str = Field(validation_alias="MASSIVE_API_KEY")
    massive_base_url: str = Field(
        default="https://api.massive.com",
        validation_alias="MASSIVE_BASE_URL",
    )

    DATABASE_URL: str | None = Field(
        default=None,
        validation_alias="DATABASE_URL",
        repr=False,
    )

    DB_USER: str | None = Field(
        default=None,
        validation_alias="DB_USER",
        repr=False,
    )
    DB_PASSWORD: str | None = Field(
        default=None,
        validation_alias="DB_PASSWORD",
        repr=False,
    )
    DB_HOST: str | None = Field(
        default=None,
        validation_alias="DB_HOST",
    )
    DB_PORT: int | None = Field(
        default=None,
        validation_alias="DB_PORT",
    )
    DB_NAME: str | None = Field(
        default=None,
        validation_alias="DB_NAME",
    )

    app_name: str = Field(default="Theory World")
    api_prefix: str = Field(
        default="/api/v1",
        validation_alias="API_PREFIX",
    )

    OPENAI_API_KEY: str = Field(repr=False)
    CHAT_MODEL: str = "gpt-4.1-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    cors_origins: str = Field(
        default="http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )

    @computed_field(repr=False)
    @property
    def database_url(self) -> str:
        """Return a SQLAlchemy URL compatible with create_async_engine()."""
        if self.DATABASE_URL:
            return self._to_asyncpg_url(self.DATABASE_URL)

        required = {
            "DB_USER": self.DB_USER,
            "DB_PASSWORD": self.DB_PASSWORD,
            "DB_HOST": self.DB_HOST,
            "DB_PORT": self.DB_PORT,
            "DB_NAME": self.DB_NAME,
        }
        missing = [name for name, value in required.items() if value is None]

        if missing:
            raise ValueError(
                "Database configuration is incomplete. Set DATABASE_URL or "
                f"set all DB_* settings. Missing: {', '.join(missing)}."
            )

        encoded_password = quote(self.DB_PASSWORD, safe="")
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{encoded_password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @staticmethod
    def _to_asyncpg_url(url: str) -> str:
        if url.startswith("postgresql+asyncpg://"):
            return url

        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url.removeprefix("postgres://")

        if url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + url.removeprefix("postgresql://")

        raise ValueError(
            "DATABASE_URL must start with postgres://, postgresql://, "
            "or postgresql+asyncpg://."
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()