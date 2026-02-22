"""Configuration settings for Learning Hub MCP."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database URL (SQLite by default)
    database_url: str = "sqlite+aiosqlite:///./data/learning_hub.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
