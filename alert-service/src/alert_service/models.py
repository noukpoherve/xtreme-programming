from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class Localisation(BaseModel):
    latitude: float
    longitude: float
    point_reference: str


class AlertPayload(BaseModel):
    alert_id: str = Field(..., description="UUID v4 unique de l'alerte")
    event_id: str = Field(..., description="UUID v4 de l'evenement source")
    sensor_id: str
    timestamp: datetime
    severity: str = Field(..., pattern="^(WARNING|CRITICAL)$")
    type: str
    message: str
    localisation: Localisation | None = None
    trace_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertResponse(BaseModel):
    alert_id: str
    status: str
    trace_id: str


class MeasurementLocalisation(BaseModel):
    latitude: float
    longitude: float
    point_reference: str


class MeasurementValues(BaseModel):
    ph: float
    turbidite_ntu: float
    temperature_c: float
    niveau_m: float
    debit_m3s: float
    oxygene_dissous_mgl: float


class WaterMeasurementEvent(BaseModel):
    event_type: str
    event_id: str
    trace_id: str
    capteur_id: str
    timestamp: datetime
    localisation: MeasurementLocalisation
    mesures: MeasurementValues
    qualite_signal: str | None = None
    firmware_version: str | None = None
