from core_api.core.config import Settings


def test_database_url_uses_fly_url_with_asyncpg_driver() -> None:
    settings = Settings(
        MASSIVE_API_KEY="test-massive-key",
        OPENAI_API_KEY="test-openai-key",
        DATABASE_URL="postgresql://user:password@db.internal:5432/app",
    )

    assert settings.database_url == (
        "postgresql+asyncpg://user:password@db.internal:5432/app"
    )


def test_database_url_falls_back_to_db_parts() -> None:
    settings = Settings(
        MASSIVE_API_KEY="test-massive-key",
        OPENAI_API_KEY="test-openai-key",
        DB_USER="app_user",
        DB_PASSWORD="p@ss/word",
        DB_HOST="localhost",
        DB_PORT=5432,
        DB_NAME="theory",
    )

    assert settings.database_url == (
        "postgresql+asyncpg://app_user:p%40ss%2Fword@localhost:5432/theory"
    )