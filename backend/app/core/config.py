from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Life180 Sentinel"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+psycopg://sentinel:sentinel@localhost:5432/sentinel"
    REDIS_URL: str = "redis://localhost:6379/0"

    REPOS_DIR: str = "/tmp/sentinel/repos"

    AI_PROVIDER: str = "anthropic"  # "anthropic" or "gemini"
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]


settings = Settings()
