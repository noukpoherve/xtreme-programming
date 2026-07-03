import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import (
    FastAPI,
    HTTPException,
    Path,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import JSONResponse

from alert_service.config import settings
from alert_service.error_handlers import register_error_handlers
from alert_service.kafka_consumer import MeasurementConsumer
from alert_service.middleware import TRACE_ID_HEADER, TraceIdMiddleware
from alert_service.models import (
    AlertListResponse,
    AlertPayload,
    AlertResponse,
    ErrorResponse,
    HealthResponse,
    MeasurementSeriesResponse,
    SensorMetadataView,
    SensorStateListResponse,
    SensorStateView,
    WaterMeasurementEvent,
)
from alert_service.openapi_config import (
    API_CONTACT,
    API_DESCRIPTION,
    API_LICENSE,
    API_SERVERS,
    API_TITLE,
    API_VERSION,
    COMMON_RESPONSES,
    TAGS_METADATA,
    SENSOR_NOT_FOUND_EXAMPLE,
    INVALID_MEASUREMENT_EXAMPLE,
)
from alert_service.repositories import (
    PostgresAlertRepository,
    PostgresMeasurementRepository,
    PostgresSensorRepository,
    PostgresStateTransitionRepository,
    create_pool,
)
from alert_service.service import AlertService, alert_service
from alert_service.websocket import WebSocketHub, hub

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Lifespan — start/stop the Kafka consumer + PostgreSQL pool
# ──────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Try to connect to PostgreSQL (best-effort)
    database_url = settings.database_url
    pool = None
    if database_url:
        try:
            pool = await create_pool(database_url)
            logger.info("PostgreSQL pool created")

            # Wire repositories into the singleton alert_service (DI)
            alert_service._sensor_repo = PostgresSensorRepository(pool)
            alert_service._measurement_repo = PostgresMeasurementRepository(pool)
            alert_service._transition_repo = PostgresStateTransitionRepository(pool)
            alert_service._alert_repo = PostgresAlertRepository(pool)
        except Exception:
            logger.exception("Failed to connect to PostgreSQL, running in-memory mode")
            pool = None

    # Always wire the WebSocket hub
    alert_service._ws_hub = hub

    # Restore state machine from database
    await alert_service.restore_states_from_db()

    # 2. Start the Kafka consumer
    consumer = MeasurementConsumer()
    await consumer.start()
    task = None
    if consumer._running:
        task = asyncio.create_task(consumer.run())

    app.state.consumer = consumer
    app.state.consumer_task = task
    app.state.db_pool = pool

    try:
        yield
    finally:
        if task:
            task.cancel()
        await consumer.stop()
        if pool:
            await pool.close()


# ──────────────────────────────────────────────────────────────────────
# FastAPI application
# ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    contact=API_CONTACT,
    license_info=API_LICENSE,
    servers=API_SERVERS,
    openapi_tags=TAGS_METADATA,
    lifespan=lifespan,
)

# Middleware — order matters: TraceId MUST run before any handler that
# reads request.state.trace_id.
app.add_middleware(TraceIdMiddleware)

# Centralized exception handlers — every error becomes ErrorResponse JSON.
register_error_handlers(app)


# ──────────────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────────────
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Liveness probe",
    description=(
        "Returns the service health. Used by Kubernetes / Docker "
        "Compose healthchecks and by external monitoring."
    ),
    responses={503: COMMON_RESPONSES[503]},
)
async def health() -> HealthResponse:
    consumer: MeasurementConsumer | None = getattr(app.state, "consumer", None)
    components = {
        "kafka_consumer": "up" if (consumer and consumer._running) else "down",
        "sensor_registry": "ok",
    }
    overall = (
        "healthy"
        if all(v == "up" or v == "ok" for v in components.values())
        else "degraded"
    )

    body = HealthResponse(status=overall, version=API_VERSION, components=components)

    if overall != "healthy":
        # Return 503 so orchestrators restart the pod if needed.
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=body.model_dump(),
        )
    return body


@app.get(
    "/sensors",
    response_model=SensorStateListResponse,
    tags=["sensors"],
    summary="List every sensor tracked by the service",
    description="Returns the public view of every sensor currently in memory.",
    responses={500: COMMON_RESPONSES[500]},
)
async def list_sensors() -> SensorStateListResponse:
    sensors = await alert_service.list_sensors()
    return SensorStateListResponse(
        sensors=sensors,
        count=len(sensors),
    )


@app.get(
    "/stats",
    tags=["sensors"],
    summary="Aggregated KPIs for the dashboard",
    description=(
        "Returns aggregated statistics: sensor count by state, alert counts "
        "(open / 24h / 7d), and the top 5 most alerting sensors."
    ),
    responses={500: COMMON_RESPONSES[500]},
)
async def get_stats():
    """
    Compute aggregated KPIs.

    Reads from PostgreSQL if available, otherwise falls back to in-memory
    state from the registry.
    """
    sensors = await alert_service.list_sensors()

    # Sensors by state (always from in-memory registry)
    by_state = {"NORMAL": 0, "WARNING": 0, "CRITICAL": 0}
    for s in sensors:
        by_state[s.state.value] = by_state.get(s.state.value, 0) + 1

    # If PostgreSQL is available, compute alert stats from the DB
    if alert_service._alert_repo is not None:
        pool = app.state.db_pool
        if pool is not None:
            async with pool.acquire() as conn:
                open_count = (
                    await conn.fetchval(
                        "SELECT COUNT(*) FROM alerts WHERE status IN ('OPEN', 'ACK')"
                    )
                    or 0
                )
                last_24h = await conn.fetchval("""SELECT COUNT(*) FROM alerts
                       WHERE opened_at >= NOW() - INTERVAL '24 hours'""") or 0
                last_7d = await conn.fetchval("""SELECT COUNT(*) FROM alerts
                       WHERE opened_at >= NOW() - INTERVAL '7 days'""") or 0
                top_rows = await conn.fetch("""SELECT s.sensor_id, COUNT(*) AS cnt
                       FROM alerts a JOIN sensors s ON a.sensor_uuid = s.id
                       WHERE a.opened_at >= NOW() - INTERVAL '7 days'
                       GROUP BY s.sensor_id
                       ORDER BY cnt DESC LIMIT 5""")
                top = [
                    {"sensor_id": r["sensor_id"], "alert_count": r["cnt"]}
                    for r in top_rows
                ]
        else:
            open_count = last_24h = last_7d = 0
            top = []
    else:
        open_count = last_24h = last_7d = 0
        top = []

    return {
        "sensors_total": len(sensors),
        "sensors_by_state": by_state,
        "alerts_open": open_count,
        "alerts_last_24h": last_24h,
        "alerts_last_7d": last_7d,
        "top_sensors": top,
    }


@app.get(
    "/alerts",
    tags=["alerts"],
    summary="List currently open alerts",
    description="Returns the most recent open alerts (status OPEN or ACK).",
    responses={500: COMMON_RESPONSES[500]},
)
async def list_alerts(limit: int = 50):
    """Return open alerts from the DB (or empty list if no DB)."""
    if alert_service._alert_repo is None or app.state.db_pool is None:
        return {"alerts": [], "count": 0}

    rows = await alert_service._alert_repo.get_open(limit=limit)
    alerts = [
        {
            "id": str(r["id"]),
            "severity": r["severity"],
            "message": r["message"],
            "opened_at": r["opened_at"].isoformat(),
            "sensor_id": r["sensor_id"],
            "sensor_name": r["sensor_name"],
        }
        for r in rows
    ]
    return {"alerts": alerts, "count": len(alerts)}


# NOTE: WebSocket endpoint declared here (BEFORE the /sensors/{sensor_id}
# pattern route) so FastAPI matches the GET upgrade request against
# the websocket handler, not the path-parametrized GET endpoint.
# We use `/stream` instead of `/ws` to avoid the HTTP upgrade GET matching
# the `GET /sensors/{sensor_id}` path parameter.
@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time event streaming.

    Clients receive JSON messages of the form:
        {
            "event_type": "state_transition",
            "data": { ... },
            "timestamp": "2026-..."
        }
    """
    await hub.connect(websocket)
    try:
        # Send a welcome message
        await websocket.send_json(
            {
                "event_type": "welcome",
                "data": {"message": "Connected to UrbanHub alert-service"},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        # Keep the connection open; we don't expect inbound messages
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception:
        logger.exception("WebSocket error")
    finally:
        await hub.disconnect(websocket)


# ──────────────────────────────────────────────────────────────────────
# Drill-down endpoints (per-sensor detail) — declared BEFORE
# `/sensors/{sensor_id}` so the path-param pattern doesn't shadow them.
# ──────────────────────────────────────────────────────────────────────
@app.get(
    "/sensors/{sensor_id}/metadata",
    response_model=SensorMetadataView,
    tags=["sensors"],
    summary="Get full sensor metadata (drill-down)",
    description=(
        "Returns the catalogue row + live state + last measurement timestamp "
        "for one sensor. Used by the dashboard drawer."
    ),
    responses={
        404: {"description": "Sensor not found.", "model": ErrorResponse},
        503: COMMON_RESPONSES[503],
    },
)
async def get_sensor_metadata(
    sensor_id: str = Path(..., min_length=1)
) -> SensorMetadataView:
    if alert_service._sensor_repo is None or app.state.db_pool is None:
        raise HTTPException(
            status_code=503,
            detail="Sensor catalogue is unavailable (no database connection).",
        )
    return await alert_service.get_sensor_metadata(sensor_id)


@app.get(
    "/sensors/{sensor_id}/measurements",
    response_model=MeasurementSeriesResponse,
    tags=["measurements"],
    summary="Get recent measurements for one sensor (chart data)",
    description=(
        "Returns the time-series of measurements for one sensor over the last "
        "`hours` hours, ordered oldest-first (chart-friendly). Capped at 2000 points."
    ),
    responses={
        404: {"description": "Sensor not found.", "model": ErrorResponse},
        503: COMMON_RESPONSES[503],
    },
)
async def get_sensor_measurements(
    sensor_id: str = Path(..., min_length=1),
    hours: int = Query(
        24, ge=1, le=168, description="Lookback window in hours (max 7 days)."
    ),
    limit: int = Query(500, ge=1, le=2000, description="Max points returned."),
) -> MeasurementSeriesResponse:
    if alert_service._measurement_repo is None or app.state.db_pool is None:
        raise HTTPException(
            status_code=503,
            detail="Measurement store is unavailable (no database connection).",
        )
    return await alert_service.get_measurement_series(sensor_id, hours, limit)


@app.get(
    "/sensors/{sensor_id}/alerts",
    response_model=AlertListResponse,
    tags=["alerts"],
    summary="Get alerts scoped to a single sensor",
    description=(
        "Returns recent alerts for one sensor (newest first). "
        "Use `only_open=true` to filter out resolved ones."
    ),
    responses={
        404: {"description": "Sensor not found.", "model": ErrorResponse},
        503: COMMON_RESPONSES[503],
    },
)
async def get_sensor_alerts(
    sensor_id: str = Path(..., min_length=1),
    limit: int = Query(20, ge=1, le=100, description="Max alerts returned."),
    only_open: bool = Query(False, description="If true, only return OPEN/ACK alerts."),
) -> AlertListResponse:
    if alert_service._alert_repo is None or app.state.db_pool is None:
        raise HTTPException(
            status_code=503,
            detail="Alert store is unavailable (no database connection).",
        )
    rows = await alert_service.get_alerts_for_sensor(sensor_id, limit, only_open)
    return {"alerts": rows, "count": len(rows)}


@app.get(
    "/sensors/{sensor_id}",
    response_model=SensorStateView,
    tags=["sensors"],
    summary="Get a sensor by ID",
    description="Returns the current state, anomaly count and previous state.",
    responses={
        404: {
            "description": "Sensor not found.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {"not_found": SENSOR_NOT_FOUND_EXAMPLE}
                }
            },
        },
        500: COMMON_RESPONSES[500],
    },
)
async def get_sensor(
    sensor_id: str = Path(..., min_length=1, description="Sensor identifier."),
) -> SensorStateView:
    return await alert_service.get_sensor(sensor_id)


@app.delete(
    "/sensors/{sensor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["sensors"],
    summary="Reset a sensor's state machine",
    description=(
        "Removes the sensor from the registry. The next measurement "
        "for this sensor will start a fresh processor in NORMAL state."
    ),
    responses={
        204: {"description": "Sensor reset."},
        404: {
            "description": "Sensor not found.",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {"not_found": SENSOR_NOT_FOUND_EXAMPLE}
                }
            },
        },
    },
)
async def reset_sensor(
    sensor_id: str = Path(..., min_length=1, description="Sensor identifier."),
) -> None:
    alert_service.registry.reset(sensor_id)
    logger.info("sensor.reset sensor=%s", sensor_id)
    return None


# ──────────────────────────────────────────────────────────────────────
# Debug helper — exposes trace_id for manual curl testing
# ──────────────────────────────────────────────────────────────────────
@app.get(
    "/_echo",
    tags=["health"],
    summary="Echo the trace_id (debug)",
    description="Returns the trace_id attached to the current request.",
    include_in_schema=False,
)
async def echo_trace(request: Request) -> dict:
    return {"trace_id": getattr(request.state, "trace_id", None)}
