from functools import lru_cache
from urllib.parse import quote
from pathlib import Path
from dotenv import load_dotenv
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent 
ENV_FILE = BASE_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file= ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    MASSIVE_API_KEY: str = Field(validation_alias="MASSIVE_API_KEY")
    massive_base_url: str = Field(
        default="https://api.massive.com",
        validation_alias="MASSIVE_BASE_URL",
        )
    DB_USER: str = Field(validation_alias="DB_USER")
    DB_PASSWORD: str = Field(validation_alias="DB_PASSWORD")
    DB_HOST: str = Field(default="localhost", validation_alias="DB_HOST")
    DB_PORT: int = Field(default=5432, validation_alias="DB_PORT")
    DB_NAME: str = Field(validation_alias="DB_NAME")
    app_name: str = Field(default="Theory World")
    api_prefix: str = Field(
        default="/api/v1",
        validation_alias="API_PREFIX",
        )

    cors_origins: str = Field(
        default="http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )

    @computed_field
    @property
    def database_url(self) -> str:
        encoded_password = quote(self.DB_PASSWORD, safe="")
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{encoded_password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    print(ENV_FILE, ENV_FILE.exists())
    return Settings()


settings = get_settings()