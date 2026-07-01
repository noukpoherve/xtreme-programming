from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any
from datetime import datetime


# ===== Generic Responses =====

class ErrorResponse(BaseModel):
    """API error response"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error_code": "NOT_FOUND",
                "message": "Resource not found",
                "details": {"resource": "sensor", "id": "123"}
            }
        }
    )
    
    success: bool = False
    error_code: str
    message: str
    details: Any | None = None


# ===== Sensor Models (Contracts) =====

class SensorCreate(BaseModel):
    """Contract for registering a new sensor"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sensor_id": "SEINE-001",
                "name": "Seine Sensor Pont Alma",
                "location": "Paris, Pont de l'Alma",
                "latitude": 48.8637,
                "longitude": 2.3017,
                "active": True,
                "metadata": {"model": "WaterPro3000", "version": "2.4.1"}
            }
        }
    )
    
    sensor_id: str = Field(..., description="Unique sensor identifier")
    name: str = Field(..., description="Sensor name")
    location: str = Field(..., description="Sensor location")
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    active: bool = Field(default=True, description="Active/inactive status")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class SensorUpdate(BaseModel):
    """Contract for updating a sensor"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Seine Sensor - Section 2",
                "active": False,
                "metadata": {"maintenance": "2026-06-30"}
            }
        }
    )
    
    name: Optional[str] = None
    location: Optional[str] = None
    active: Optional[bool] = None
    metadata: Optional[dict] = None


class SensorActionResponse(BaseModel):
    """Response contract - Sensor action result"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sensor_id": "SEINE-001",
                "status": "registered"
            }
        }
    )
    
    sensor_id: str
    status: str


class SensorDetail(BaseModel):
    """Response contract - Sensor details"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sensor_id": "SEINE-001",
                "name": "Seine Sensor Pont Alma",
                "location": "Paris, Pont de l'Alma",
                "latitude": 48.8637,
                "longitude": 2.3017,
                "active": True,
                "metadata": {"model": "WaterPro3000"}
            }
        }
    )
    
    sensor_id: str
    name: str
    location: str
    latitude: float
    longitude: float
    active: bool
    metadata: dict


class SensorListResponse(BaseModel):
    """Response contract - Sensor list"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 5,
                "sensors": [
                    {
                        "sensor_id": "SEINE-001",
                        "name": "Seine Sensor Pont Alma",
                        "location": "Paris",
                        "latitude": 48.8637,
                        "longitude": 2.3017,
                        "active": True,
                        "metadata": {}
                    }
                ]
            }
        }
    )
    
    total: int
    sensors: list[SensorDetail]


class SensorStatsResponse(BaseModel):
    """Response contract - Sensor statistics"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_sensors": 10,
                "active_sensors": 8,
                "inactive_sensors": 2,
                "last_update": "2026-06-30T12:00:00Z"
            }
        }
    )
    
    total_sensors: int
    active_sensors: int
    inactive_sensors: int
    last_update: Optional[datetime] = None


class MeasurementResponse(BaseModel):
    """Response contract - Captured measurement"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sensor_id": "SEINE-001",
                "uuid": "uuid-1234",
                "timestamp": "2026-06-30T12:00:00Z",
                "ph": 7.2,
                "turbidity": 12.5,
                "level": 1.25,
                "flow": 85.3,
                "latitude": 48.8637,
                "longitude": 2.3017,
                "published": True
            }
        }
    )
    
    sensor_id: str
    uuid: str
    timestamp: str
    ph: float
    turbidity: float
    level: float
    flow: float
    latitude: float
    longitude: float
    published: bool
