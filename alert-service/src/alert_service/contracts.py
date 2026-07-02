from typing import Any
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from alert_service.models import Localisation


# ===== Generic Responses =====

class ApiResponse(BaseModel):
    """Generic API response"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation successful",
                "data": {"id": "123"},
                "timestamp": "2026-06-30T12:00:00Z"
            }
        }
    )
    
    success: bool
    message: str
    data: Any | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """API error response"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error_code": "NOT_FOUND",
                "message": "Resource not found",
                "details": {"resource": "alert", "id": "123"}
            }
        }
    )
    
    success: bool = False
    error_code: str
    message: str
    details: Any | None = None

# ===== Alert Models (Contracts) =====

class AlertCreate(BaseModel):
    """Contract for creating an alert"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "alert_id": "a1b2c3d4",
                "event_id": "e1e2e3e4",
                "sensor_id": "SEINE-001",
                "timestamp": "2026-06-30T12:00:00Z",
                "severity": "CRITICAL",
                "type": "ph",
                "message": "Critical pH detected: 5.2",
                "trace_id": "trace-xyz"
            }
        }
    )
    
    alert_id: str = Field(..., description="Unique alert UUID")
    event_id: str = Field(..., description="Source event ID")
    sensor_id: str = Field(..., description="Sensor ID")
    timestamp: datetime = Field(..., description="Alert timestamp")
    severity: str = Field(..., pattern="^(WARNING|CRITICAL)$", description="Severity level")
    type: str = Field(..., description="Alert type (ph, turbidity, etc.)")
    message: str = Field(..., description="Descriptive message")
    localisation: Localisation | None = None
    trace_id: str = Field(..., description="Trace ID for debugging")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AlertUpdate(BaseModel):
    """Contract for updating an alert"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "severity": "WARNING",
                "message": "Alert updated",
                "metadata": {"updated_reason": "retesting"}
            }
        }
    )
    
    severity: str = Field(..., pattern="^(WARNING|CRITICAL)$")
    message: str = Field(...)
    metadata: dict = Field(default_factory=dict)


class AlertDetail(BaseModel):
    """Response contract - Alert details"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "alert_id": "a1b2c3d4",
                "event_id": "e1e2e3e4",
                "sensor_id": "SEINE-001",
                "timestamp": "2026-06-30T12:00:00Z",
                "severity": "CRITICAL",
                "type": "ph",
                "message": "Critical pH detected: 5.2",
                "trace_id": "trace-xyz"
            }
        }
    )
    
    alert_id: str
    event_id: str
    sensor_id: str
    timestamp: datetime
    severity: str
    type: str
    message: str
    trace_id: str


class AlertListResponse(BaseModel):
    """Response contract - List of alerts"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 42,
                "limit": 10,
                "offset": 0,
                "alerts": [
                    {
                        "alert_id": "a1b2c3d4",
                        "event_id": "e1e2e3e4",
                        "sensor_id": "SEINE-001",
                        "timestamp": "2026-06-30T12:00:00Z",
                        "severity": "CRITICAL",
                        "type": "ph",
                        "message": "Critical pH detected: 5.2",
                        "trace_id": "trace-xyz"
                    }
                ]
            }
        }
    )
    
    total: int
    limit: int
    offset: int
    alerts: list[AlertDetail]


class AlertStatsResponse(BaseModel):
    """Response contract - Alert statistics"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_alerts": 150,
                "critical_count": 45,
                "warning_count": 105,
                "by_sensor": {"SEINE-001": 50, "SEINE-002": 100},
                "by_type": {"ph": 80, "turbidity": 70}
            }
        }
    )
    
    total_alerts: int
    critical_count: int
    warning_count: int
    by_sensor: dict[str, int]
    by_type: dict[str, int]
