from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Telecom Service & Network Management System"
    app_version: str = "1.0.0"
    debug: bool = True

    database_url: str = "sqlite:///./telecom.db"

    jwt_secret_key: str = "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    password_reset_token_expire_minutes: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()