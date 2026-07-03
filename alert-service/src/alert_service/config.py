"""
Centralized application settings for alert-service.

All environment-variable driven configuration lives here so that other
modules can import `settings` instead of scattering `os.getenv` calls.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "alert-service"
    app_version: str = "0.1.0"

    # Infrastructure
    database_url: str = ""
    kafka_bootstrap_servers: str = "localhost:9092"

    # Topics
    water_quality_topic: str = "mesure.qualite.eau"
    pollution_alert_topic: str = "alerte.pollution.detectee"

    # Consumer
    kafka_consumer_group: str = "alert-service-group"
    kafka_auto_offset_reset: str = "latest"

    # WebSocket
    websocket_path: str = "/stream"


settings = Settings()
