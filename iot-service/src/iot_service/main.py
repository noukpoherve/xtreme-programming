import asyncio
import logging
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, status

logging.basicConfig(level=logging.INFO)

from iot_service.api_errors import register_exception_handlers, register_error_middleware
from iot_service.hubeau_client import HubEauSensorClient
from iot_service.kafka_producer import MeasurementProducer
from iot_service.sensor_service import IoTSensorSimulator
from iot_service.sensor_repository import SensorRepository, Sensor
from iot_service.capteur import Capteur
from iot_service.capteur_state import TransitionCapteurInvalide, CapteurEtat
from iot_service.sensor_contracts import (
    ErrorResponse,
    SensorCreate,
    SensorUpdate,
    SensorDetail,
    SensorListResponse,
    SensorStatsResponse,
    MeasurementResponse,
    SensorActionResponse,
    CapteurTransitionResponse,
)

_KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    405: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    503: {"model": ErrorResponse},
}


def _background_poll_enabled() -> bool:
    return os.getenv("DISABLE_BACKGROUND_POLL", "0") != "1"


async def _poll_loop(
    sensor_client: HubEauSensorClient, kafka_producer: MeasurementProducer
):
    while True:
        try:
            measurement = sensor_client.capture()
            published = await kafka_producer.send(measurement)
            if published:
                logging.info(
                    "Scheduled ingest: sensor=%s level=%.2f flow=%.2f",
                    measurement.sensor_id,
                    measurement.level,
                    measurement.flow,
                )
            else:
                logging.warning(
                    "Scheduled ingest skipped: Kafka unavailable for sensor=%s",
                    measurement.sensor_id,
                )
        except Exception:
            logging.exception("Scheduled ingest failed")
        await asyncio.sleep(_POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sensor_client = HubEauSensorClient(
        code_entite="F700000103",
        default_ph=7.4,
        default_turbidity=8.0,
    )
    app.state.kafka_producer = MeasurementProducer(bootstrap_servers=_KAFKA_BOOTSTRAP)
    app.state.sensor_repository = SensorRepository()
    await app.state.kafka_producer.start()

    task = None
    if _background_poll_enabled():
        task = asyncio.create_task(
            _poll_loop(app.state.sensor_client, app.state.kafka_producer)
        )

    yield

    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    await app.state.kafka_producer.stop()


app = FastAPI(
    title="iot-service",
    version="0.1.0",
    lifespan=lifespan,
)
register_error_middleware(app)
register_exception_handlers(app)


def _sensor_detail(sensor: Sensor) -> SensorDetail:
    capteur = Capteur.from_sensor(sensor)
    return SensorDetail(
        sensor_id=capteur.sensor_id,
        name=capteur.name,
        location=capteur.location,
        latitude=capteur.latitude,
        longitude=capteur.longitude,
        active=capteur.active,
        etat=capteur.etat_nom.value,
        metadata=capteur.metadata,
    )


def _measurement_response(measurement) -> MeasurementResponse:
    return MeasurementResponse(
        sensor_id=measurement.sensor_id,
        uuid=measurement.uuid,
        timestamp=measurement.timestamp.isoformat(),
        ph=measurement.ph,
        turbidity=measurement.turbidity,
        level=measurement.level,
        flow=measurement.flow,
        latitude=measurement.latitude,
        longitude=measurement.longitude,
        published=True,
    )


def _sensor_action_response(sensor_id: str, status_value: str) -> SensorActionResponse:
    return SensorActionResponse(sensor_id=sensor_id, status=status_value)


def _sensor_client() -> HubEauSensorClient:
    if not hasattr(app.state, "sensor_client"):
        app.state.sensor_client = HubEauSensorClient(
            code_entite="F700000103",
            default_ph=7.4,
            default_turbidity=8.0,
        )
    return app.state.sensor_client


def _kafka_producer() -> MeasurementProducer:
    if not hasattr(app.state, "kafka_producer"):
        app.state.kafka_producer = MeasurementProducer(bootstrap_servers=_KAFKA_BOOTSTRAP)
    return app.state.kafka_producer


def _sensor_repository() -> SensorRepository:
    if not hasattr(app.state, "sensor_repository"):
        app.state.sensor_repository = SensorRepository()
    return app.state.sensor_repository


def _sensor_stats_response(sensor_repo: SensorRepository) -> SensorStatsResponse:
    sensors = sensor_repo.get_all()
    active = sum(1 for s in sensors if Capteur.from_sensor(s).etat_nom == CapteurEtat.ACTIF)
    return SensorStatsResponse(
        total_sensors=len(sensors),
        active_sensors=active,
        inactive_sensors=len(sensors) - active,
        last_update=datetime.now(timezone.utc),
    )


def _load_capteur(sensor_repo: SensorRepository, sensor_id: str) -> Capteur:
    sensor = sensor_repo.get(sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return Capteur.from_sensor(sensor)


def _save_capteur(sensor_repo: SensorRepository, capteur: Capteur) -> None:
    updated = sensor_repo.update(capteur.sensor_id, capteur.to_sensor())
    if not updated:
        raise HTTPException(status_code=500, detail="Update failed")


def _apply_transition(
    sensor_repo: SensorRepository, sensor_id: str, action: str
) -> CapteurTransitionResponse:
    capteur = _load_capteur(sensor_repo, sensor_id)
    try:
        getattr(capteur, action)()
    except TransitionCapteurInvalide as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _save_capteur(sensor_repo, capteur)
    return CapteurTransitionResponse(sensor_id=sensor_id, etat=capteur.etat_nom.value)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "version": "0.1.0"}


@app.post(
    "/ingest",
    response_model=MeasurementResponse,
    tags=["Ingestion"],
    responses=ERROR_RESPONSES,
)
async def ingest():
    """Ingest a measurement from Hub'eau"""
    sensor_client = _sensor_client()
    kafka_producer = _kafka_producer()

    measurement = sensor_client.capture()
    published = await kafka_producer.send(measurement)
    if not published:
        raise HTTPException(status_code=503, detail="Kafka producer unavailable")

    return _measurement_response(measurement)


@app.post(
    "/simulate",
    response_model=MeasurementResponse,
    tags=["Ingestion"],
    responses=ERROR_RESPONSES,
)
async def simulate(ph: float = 7.0, turbidity: float = 75.0):
    """Simulate a measurement from an IoT sensor"""
    kafka_producer = _kafka_producer()

    sensor = IoTSensorSimulator(sensor_id="SIM-001")
    measurement = sensor.capture(ph=ph, turbidity=turbidity, level=1.5, flow=0.8)
    published = await kafka_producer.send(measurement)
    if not published:
        raise HTTPException(status_code=503, detail="Kafka producer unavailable")

    return _measurement_response(measurement)


# ===== Sensors Endpoints =====

@app.post(
    "/sensors",
    response_model=SensorActionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sensors"],
    responses=ERROR_RESPONSES,
)
@app.post(
    "/capteurs",
    response_model=SensorActionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sensors"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def register_sensor(sensor: SensorCreate):
    """Register a new sensor"""
    sensor_repo = _sensor_repository()
    if sensor_repo.get(sensor.sensor_id):
        raise HTTPException(status_code=409, detail="Sensor already exists")
    capteur = Capteur(
        sensor_id=sensor.sensor_id,
        name=sensor.name,
        location=sensor.location,
        latitude=sensor.latitude,
        longitude=sensor.longitude,
        metadata=sensor.metadata,
    )
    if not sensor.active:
        capteur.desactiver()
    sensor_repo.save(capteur.to_sensor())
    return _sensor_action_response(sensor.sensor_id, "registered")


@app.get(
    "/sensors",
    response_model=SensorListResponse | SensorStatsResponse,
    tags=["Sensors"],
    responses=ERROR_RESPONSES,
)
@app.get(
    "/capteurs",
    response_model=SensorListResponse | SensorStatsResponse,
    tags=["Sensors"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def list_sensors(
    option: str | None = Query(None, description="Use 'stats' to return statistics"),
):
    """List all sensors"""
    sensor_repo = _sensor_repository()
    if option and option != "stats":
        raise HTTPException(status_code=400, detail="Invalid option. Use 'stats'.")
    if option == "stats":
        return _sensor_stats_response(sensor_repo)

    sensors = sensor_repo.get_all()
    return SensorListResponse(
        total=len(sensors),
        sensors=[_sensor_detail(s) for s in sensors],
    )


@app.get(
    "/sensors/stats",
    response_model=SensorStatsResponse,
    tags=["Sensors"],
    responses=ERROR_RESPONSES,
)
@app.get(
    "/capteurs-stats",
    response_model=SensorStatsResponse,
    tags=["Sensors"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def sensor_stats():
    """Get sensor statistics"""
    sensor_repo = _sensor_repository()
    return _sensor_stats_response(sensor_repo)


@app.get(
    "/sensors/{sensor_id}",
    response_model=SensorDetail,
    tags=["Sensors"],
    responses=ERROR_RESPONSES,
)
@app.get(
    "/capteurs/{sensor_id}",
    response_model=SensorDetail,
    tags=["Sensors"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def get_sensor(sensor_id: str):
    """Get sensor details"""
    sensor_repo = _sensor_repository()
    sensor = sensor_repo.get(sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return _sensor_detail(sensor)


@app.put(
    "/sensors/{sensor_id}",
    response_model=SensorActionResponse,
    tags=["Sensors"],
    responses=ERROR_RESPONSES,
)
@app.put(
    "/capteurs/{sensor_id}",
    response_model=SensorActionResponse,
    tags=["Sensors"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def update_sensor(sensor_id: str, sensor_data: SensorUpdate):
    """Update a sensor"""
    sensor_repo = _sensor_repository()
    capteur = _load_capteur(sensor_repo, sensor_id)
    if (
        sensor_data.name is None
        and sensor_data.location is None
        and sensor_data.active is None
        and sensor_data.metadata is None
    ):
        raise HTTPException(status_code=400, detail="No sensor fields provided")

    if sensor_data.name is not None:
        capteur.name = sensor_data.name
    if sensor_data.location is not None:
        capteur.location = sensor_data.location
    if sensor_data.metadata is not None:
        capteur.metadata = sensor_data.metadata
    if sensor_data.active is not None:
        if sensor_data.active:
            try:
                capteur.activer()
            except TransitionCapteurInvalide:
                pass
        else:
            try:
                capteur.desactiver()
            except TransitionCapteurInvalide:
                pass

    _save_capteur(sensor_repo, capteur)
    return _sensor_action_response(sensor_id, "updated")


@app.delete(
    "/sensors/{sensor_id}",
    response_model=SensorActionResponse,
    tags=["Sensors"],
    responses=ERROR_RESPONSES,
)
@app.delete(
    "/capteurs/{sensor_id}",
    response_model=SensorActionResponse,
    tags=["Sensors"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def delete_sensor(sensor_id: str):
    """Delete a sensor"""
    sensor_repo = _sensor_repository()
    deleted = sensor_repo.delete(sensor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return _sensor_action_response(sensor_id, "deleted")


# ===== Capteur State Transitions =====

@app.post(
    "/sensors/{sensor_id}/activer",
    response_model=CapteurTransitionResponse,
    tags=["Sensors"],
    responses=ERROR_RESPONSES,
)
@app.post(
    "/capteurs/{sensor_id}/activer",
    response_model=CapteurTransitionResponse,
    tags=["Sensors"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def activer_capteur(sensor_id: str):
    """Active un capteur (transition d'etat)."""
    return _apply_transition(_sensor_repository(), sensor_id, "activer")


@app.post(
    "/sensors/{sensor_id}/desactiver",
    response_model=CapteurTransitionResponse,
    tags=["Sensors"],
    responses=ERROR_RESPONSES,
)
@app.post(
    "/capteurs/{sensor_id}/desactiver",
    response_model=CapteurTransitionResponse,
    tags=["Sensors"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def desactiver_capteur(sensor_id: str):
    """Desactive un capteur."""
    return _apply_transition(_sensor_repository(), sensor_id, "desactiver")


@app.post(
    "/sensors/{sensor_id}/maintenance",
    response_model=CapteurTransitionResponse,
    tags=["Sensors"],
    responses=ERROR_RESPONSES,
)
@app.post(
    "/capteurs/{sensor_id}/maintenance",
    response_model=CapteurTransitionResponse,
    tags=["Sensors"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def maintenance_capteur(sensor_id: str):
    """Met un capteur en maintenance."""
    return _apply_transition(_sensor_repository(), sensor_id, "mettre_en_maintenance")


@app.post(
    "/sensors/{sensor_id}/panne",
    response_model=CapteurTransitionResponse,
    tags=["Sensors"],
    responses=ERROR_RESPONSES,
)
@app.post(
    "/capteurs/{sensor_id}/panne",
    response_model=CapteurTransitionResponse,
    tags=["Sensors"],
    include_in_schema=False,
    responses=ERROR_RESPONSES,
)
async def panne_capteur(sensor_id: str):
    """Signale une panne sur le capteur."""
    return _apply_transition(_sensor_repository(), sensor_id, "signaler_panne")
