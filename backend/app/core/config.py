from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "dev-secret-change-in-production"
    log_level: str = "INFO"
    debug: bool = False


settings = Settings()
