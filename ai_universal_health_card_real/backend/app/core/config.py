from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Universal Health Card"
    environment: str = "development"

    database_url: str
    jwt_secret: str

    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 7

    max_upload_mb: int = 15
    upload_dir: str = "uploads"

    # Current public Cloudflare URL
    public_base_url: str = (
        "https://earrings-swing-accuracy-sometimes.trycloudflare.com"
    )

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_tls: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()