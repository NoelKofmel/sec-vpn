from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    wg_interface: str = "wg0"
    log_level: str = "INFO"
    # mTLS: path to CA cert for verifying backend client certs
    mtls_ca_cert: str = "/certs/ca.crt"
    mtls_server_cert: str = "/certs/server.crt"
    mtls_server_key: str = "/certs/server.key"


settings = Settings()
