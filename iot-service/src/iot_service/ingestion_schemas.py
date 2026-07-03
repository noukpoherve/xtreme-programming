"""Schemas Pydantic pour les routes d'ingestion — documentation Swagger."""

from pydantic import BaseModel, ConfigDict, Field


class IngestionStatusResponse(BaseModel):
    """Etat du pipeline d'ingestion iot-service."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "kafka_ready": True,
                "quality_poller": {
                    "stations": 6,
                    "cycles_completed": 12,
                    "messages_published": 48,
                    "interval_seconds": 21600,
                },
                "simulator": {
                    "active_sensors": 6,
                    "cycles_completed": 120,
                    "interval_seconds": 300.0,
                },
                "kafka_topic": "mesure.qualite.eau",
            }
        }
    )

    kafka_ready: bool
    kafka_topic: str
    quality_poller: dict
    simulator: dict


class HubEauIngestionResponse(BaseModel):
    """Resultat d'une ingestion Hub'Eau declenchee manuellement."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "hubeau",
                "messages_published": 4,
                "stations_polled": 6,
            }
        }
    )

    source: str = "hubeau"
    messages_published: int = Field(..., ge=0)
    stations_polled: int = Field(..., ge=0)


class SimulationIngestionResponse(BaseModel):
    """Resultat d'un cycle simulateur declenche manuellement."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "simulate",
                "sensors_triggered": 6,
            }
        }
    )

    source: str = "simulate"
    sensors_triggered: int = Field(..., ge=0)


class SensorMetricsPayload(BaseModel):
    """Metriques envoyees par un capteur physique via la passerelle HTTP."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ph": 7.5,
                "turbidite_ntu": 12.0,
                "temperature_c": 19.5,
                "niveau_m": 1.2,
                "debit_m3s": 220.0,
                "oxygene_dissous_mgl": 8.0,
                "qualite_signal": "GOOD",
                "firmware_version": "1.2.3",
            }
        }
    )

    ph: float = Field(..., ge=0.0, le=14.0, description="pH (0-14)")
    turbidite_ntu: float = Field(..., ge=0.0, description="Turbidite en NTU")
    temperature_c: float = Field(..., description="Temperature en Celsius")
    niveau_m: float = Field(..., ge=0.0, description="Niveau d'eau en metres")
    debit_m3s: float = Field(..., ge=0.0, description="Debit en m3/s")
    oxygene_dissous_mgl: float = Field(..., ge=0.0, description="Oxygene dissous mg/L")
    qualite_signal: str = Field("GOOD", description="Qualite du signal capteur")
    firmware_version: str = Field("1.0.0", description="Version firmware capteur")


class SensorMetricsAcceptedResponse(BaseModel):
    """Accuse de reception apres ingestion d'une mesure capteur."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "accepted",
                "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "sensor_id": "SEINE-VITRY-001",
                "published": True,
            }
        }
    )

    status: str
    event_id: str
    sensor_id: str
    published: bool
