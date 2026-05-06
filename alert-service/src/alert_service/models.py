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
    capteur_id: str
    timestamp: datetime
    severity: str = Field(..., pattern="^(WARNING|CRITICAL)$")
    type: str
    message: str
    localisation: Localisation
    trace_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertResponse(BaseModel):
    alert_id: str
    status: str
    trace_id: str
