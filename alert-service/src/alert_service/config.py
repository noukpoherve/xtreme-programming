from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ALERT_", env_file=".env")

    app_name: str = "alert-service"
    app_version: str = "0.1.0"


settings = Settings()
