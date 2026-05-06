from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ALERT_", env_file=".env")

    app_name: str = "alert-service"
    app_version: str = "0.1.0"
    kafka_bootstrap_servers: str = "localhost:9092"
    water_quality_topic: str = "mesure.qualite.eau"
    pollution_alert_topic: str = "alerte.pollution.detectee"
    kafka_consumer_group: str = "alert-service-consumer"
    enable_kafka_bridge: bool = False


settings = Settings()
