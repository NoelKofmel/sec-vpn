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
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    log_level: str = "INFO"
    debug: bool = False
    # mTLS client credentials for backend→node-agent calls
    mtls_ca_cert: str = "/certs/ca.crt"
    mtls_client_cert: str = "/certs/client.crt"
    mtls_client_key: str = "/certs/client.key"
    # Health check interval in seconds
    health_check_interval: int = 60


settings = Settings()
