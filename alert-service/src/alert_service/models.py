from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from alert_service.state_config import SensorState


# ──────────────────────────────────────────────────────────────────────
# Error response — shared shape for every error in the API
# ──────────────────────────────────────────────────────────────────────
class ErrorCode(str, Enum):
    """Machine-readable identifiers used in the `error` field of responses."""

    INVALID_MEASUREMENT = "INVALID_MEASUREMENT"
    INVALID_ALERT_PAYLOAD = "INVALID_ALERT_PAYLOAD"
    SENSOR_NOT_FOUND = "SENSOR_NOT_FOUND"
    SENSOR_ALREADY_REGISTERED = "SENSOR_ALREADY_REGISTERED"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    KAFKA_PUBLISH_FAILED = "KAFKA_PUBLISH_FAILED"
    KAFKA_CONSUME_FAILED = "KAFKA_CONSUME_FAILED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorResponse(BaseModel):
    """
    Standardized error payload returned by every endpoint on failure.

    Clients SHOULD rely on `error` (machine-readable code) rather than
    `message` to drive behavior. `trace_id` allows support teams to
    correlate the error with logs and traces.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "INVALID_MEASUREMENT",
                "message": "pH value -2.0 is outside the valid range [0.0, 14.0]",
                "trace_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "timestamp": "2026-06-29T10:30:00Z",
                "path": "/alertes",
                "details": {"field": "mesures.ph"},
            }
        }
    )

    error: ErrorCode = Field(..., description="Machine-readable error identifier.")
    message: str = Field(..., description="Human-readable description of the error.")
    trace_id: str | None = Field(
        default=None, description="Correlation ID for log lookup."
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Server-side timestamp when the error was generated.",
    )
    path: str | None = Field(
        default=None, description="URL path that produced the error."
    )
    details: dict[str, Any] | None = Field(
        default=None,
        description="Optional context (invalid field, offending value, etc.).",
    )


# ──────────────────────────────────────────────────────────────────────
# Domain models — payload, response, measurements
# ──────────────────────────────────────────────────────────────────────
class Localisation(BaseModel):
    latitude: float
    longitude: float
    point_reference: str


class AlertPayload(BaseModel):
    alert_id: str = Field(..., description="UUID v4 unique de l'alerte")
    event_id: str = Field(..., description="UUID v4 de l'evenement source")
    sensor_id: str
    timestamp: datetime
    # ── typage fort : SensorState au lieu d'une regex sur str ──
    severity: SensorState
    type: str
    message: str
    localisation: Localisation | None = None
    trace_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    data_source: str = Field(
        default="simulated",
        description="'real' (Hub'Eau) ou 'simulated' (sensor-simulator).",
    )


class AlertResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "alert_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                "status": "CREATED",
                "trace_id": "trace-001",
            }
        }
    )

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
    data_source: str = Field(
        default="simulated",
        description="'real' if from Hub'Eau, 'simulated' if from sensor-simulator.",
    )


# ──────────────────────────────────────────────────────────────────────
# Health + sensors views
# ──────────────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "components": {
                    "kafka_consumer": "up",
                    "sensor_registry": "ok",
                },
            }
        }
    )

    status: str = Field(..., description="'healthy' or 'degraded'.")
    version: str
    components: dict[str, str] | None = Field(
        default=None, description="Status of each critical component."
    )


class SensorStateView(BaseModel):
    """Public view of a sensor's current state."""

    sensor_id: str
    state: SensorState
    anomaly_count: int
    previous_state: SensorState | None = None


class SensorStateListResponse(BaseModel):
    """List of every sensor currently tracked by the service."""

    sensors: list[SensorStateView]
    count: int


class StatsResponse(BaseModel):
    """Aggregated KPIs for the dashboard."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sensors_total": 12,
                "sensors_by_state": {"NORMAL": 8, "WARNING": 3, "CRITICAL": 1},
                "alerts_open": 4,
                "alerts_last_24h": 12,
                "alerts_last_7d": 47,
                "top_sensors": [
                    {"sensor_id": "SEINE-SURESNES-011", "alert_count": 8},
                    {"sensor_id": "SEINE-COLOMBES-012", "alert_count": 5},
                ],
            }
        }
    )

    sensors_total: int = Field(..., description="Total number of sensors tracked.")
    sensors_by_state: dict[str, int] = Field(
        ..., description="Count of sensors in each state."
    )
    alerts_open: int = Field(..., description="Number of currently open alerts.")
    alerts_last_24h: int = Field(..., description="Alerts opened in the last 24 hours.")
    alerts_last_7d: int = Field(..., description="Alerts opened in the last 7 days.")
    top_sensors: list[dict] = Field(
        default_factory=list,
        description="Top 5 sensors by alert count over the last 7 days.",
    )


class AlertListItem(BaseModel):
    """Single alert in the alert list response."""

    id: str
    severity: str
    message: str
    opened_at: datetime
    sensor_id: str
    sensor_name: str


class AlertListResponse(BaseModel):
    """List of currently open alerts."""

    alerts: list[AlertListItem]
    count: int


# ──────────────────────────────────────────────────────────────────────
# Drill-down views (sensor detail page)
# ──────────────────────────────────────────────────────────────────────
class SensorMetadataView(BaseModel):
    """
    Full metadata for one sensor: catalogue + state + last seen.

    Used by the dashboard drill-down drawer.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sensor_id": "SEINE-VITRY-001",
                "name": "Vitry-sur-Seine",
                "latitude": 48.7876,
                "longitude": 2.3926,
                "point_reference": "Pont de Vitry",
                "state": "NORMAL",
                "anomaly_count": 0,
                "previous_state": None,
                "data_source": "real",
                "firmware_version": "Hub'Eau v2",
                "last_measurement_at": "2026-07-01T09:54:23Z",
            }
        }
    )

    sensor_id: str
    name: str
    latitude: float
    longitude: float
    point_reference: str
    state: SensorState
    anomaly_count: int
    previous_state: SensorState | None = None
    data_source: str = Field(
        default="simulated",
        description="'real' (Hub'Eau) ou 'simulated' (sensor-simulator).",
    )
    firmware_version: str | None = None
    last_measurement_at: datetime | None = None


class MeasurementPoint(BaseModel):
    """A single time-series measurement point."""

    timestamp: datetime
    ph: float
    temperature_c: float
    turbidity_ntu: float
    dissolved_oxygen_mgl: float
    level_m: float | None = None
    flow_m3s: float | None = None
    signal_quality: str | None = None


class MeasurementSeriesResponse(BaseModel):
    """Time-series of measurements for a sensor (chart + table)."""

    sensor_id: str
    hours: int
    count: int
    points: list[MeasurementPoint]