import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, status

logging.basicConfig(level=logging.INFO)

from alert_service.api_errors import register_exception_handlers, register_error_middleware
from alert_service.config import settings
from alert_service.kafka_consumer import MeasurementConsumer
from alert_service.models import AlertPayload, AlertResponse
from alert_service.service import AlertService
from alert_service.contracts import (
    ErrorResponse,
    AlertListResponse, AlertDetail, AlertStatsResponse, AlertUpdate, AlertCreate
)


def _background_consumer_enabled() -> bool:
    return os.getenv("DISABLE_BACKGROUND_CONSUMER", "0") != "1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.alert_service = AlertService()
    consumer = None
    task = None
    if _background_consumer_enabled():
        consumer = MeasurementConsumer(service=app.state.alert_service)
        await consumer.start()
        if consumer._running:
            task = asyncio.create_task(consumer.run())
    yield
    if task:
        task.cancel()
    if consumer:
        await consumer.stop()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
register_error_middleware(app)
register_exception_handlers(app)

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    405: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


def _service():
    if not hasattr(app.state, "alert_service"):
        app.state.alert_service = AlertService()
    return app.state.alert_service


def _alert_detail(alert: AlertPayload) -> AlertDetail:
    return AlertDetail(
        alert_id=alert.alert_id,
        event_id=alert.event_id,
        sensor_id=alert.sensor_id,
        timestamp=alert.timestamp,
        severity=alert.severity,
        type=alert.type,
        message=alert.message,
        trace_id=alert.trace_id,
    )


async def _build_alert_stats() -> AlertStatsResponse:
    count = await _service().count_alerts()
    alerts = [] if count == 0 else await _service().get_all_alerts(count, 0)

    critical_count = sum(1 for a in alerts if a.severity == "CRITICAL")
    warning_count = sum(1 for a in alerts if a.severity == "WARNING")

    by_sensor: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for alert in alerts:
        by_sensor[alert.sensor_id] = by_sensor.get(alert.sensor_id, 0) + 1
        by_type[alert.type] = by_type.get(alert.type, 0) + 1

    return AlertStatsResponse(
        total_alerts=count,
        critical_count=critical_count,
        warning_count=warning_count,
        by_sensor=by_sensor,
        by_type=by_type,
    )


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@app.post(
    "/alerts",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Alerts"],
    responses=ERROR_RESPONSES,
)
@app.post(
    "/alertes",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Alerts"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def create_alert(payload: AlertCreate):
    """Create a new alert"""
    alert = AlertPayload(**payload.model_dump())
    existing = await _service().get_alert(alert.alert_id)
    if existing:
        raise HTTPException(status_code=409, detail="Alert already exists")
    return await _service().process_alert(alert)


@app.get(
    "/alerts",
    response_model=AlertListResponse | AlertStatsResponse,
    tags=["Alerts"],
    responses=ERROR_RESPONSES,
)
@app.get(
    "/alertes",
    response_model=AlertListResponse | AlertStatsResponse,
    tags=["Alerts"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def list_alerts(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    option: str | None = Query(None, description="Use 'stats' to return statistics"),
):
    """List all alerts with pagination"""
    if option and option != "stats":
        raise HTTPException(status_code=400, detail="Invalid option. Use 'stats'.")
    if option == "stats":
        return await _build_alert_stats()

    alerts = await _service().get_all_alerts(limit, offset)
    total = await _service().count_alerts()
    return AlertListResponse(
        total=total,
        limit=limit,
        offset=offset,
        alerts=[_alert_detail(alert) for alert in alerts],
    )


@app.get(
    "/alerts/stats",
    response_model=AlertStatsResponse,
    tags=["Alerts"],
    responses=ERROR_RESPONSES,
)
@app.get(
    "/alertes-stats",
    response_model=AlertStatsResponse,
    tags=["Alerts"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def alert_stats():
    """Get alert statistics"""
    return await _build_alert_stats()


@app.get(
    "/alerts/{alert_id}",
    response_model=AlertDetail,
    tags=["Alerts"],
    responses=ERROR_RESPONSES,
)
@app.get(
    "/alertes/{alert_id}",
    response_model=AlertDetail,
    tags=["Alerts"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def get_alert(alert_id: str):
    """Get an alert by ID"""
    alert = await _service().get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _alert_detail(alert)


@app.get(
    "/alerts/sensor/{sensor_id}",
    response_model=list[AlertDetail],
    tags=["Alerts"],
    responses=ERROR_RESPONSES,
)
@app.get(
    "/alertes/capteur/{sensor_id}",
    response_model=list[AlertDetail],
    tags=["Alerts"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def get_alerts_by_sensor(sensor_id: str):
    """Get all alerts for a sensor"""
    alerts = await _service().get_alerts_by_sensor(sensor_id)
    return [_alert_detail(alert) for alert in alerts]


@app.put(
    "/alerts/{alert_id}",
    response_model=AlertResponse,
    tags=["Alerts"],
    responses=ERROR_RESPONSES,
)
@app.put(
    "/alertes/{alert_id}",
    response_model=AlertResponse,
    tags=["Alerts"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def update_alert(alert_id: str, payload: AlertUpdate):
    """Update an alert"""
    alert = await _service().get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.severity = payload.severity
    alert.message = payload.message
    alert.metadata.update(payload.metadata or {})

    updated = await _service().update_alert(alert_id, alert)
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed")

    return AlertResponse(
        alert_id=alert_id,
        status="UPDATED",
        trace_id=alert.trace_id,
    )


@app.delete(
    "/alerts/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Alerts"],
    responses=ERROR_RESPONSES,
)
@app.delete(
    "/alertes/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Alerts"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def delete_alert(alert_id: str):
    """Delete an alert"""
    deleted = await _service().delete_alert(alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    return None
