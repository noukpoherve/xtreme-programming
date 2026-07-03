import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status

from iot_service.config import settings
from iot_service.ingestion_schemas import (
    HubEauIngestionResponse,
    IngestionStatusResponse,
    SensorMetricsAcceptedResponse,
    SensorMetricsPayload,
    SimulationIngestionResponse,
)
from iot_service.kafka_producer import MeasurementProducer
from iot_service.quality_poller import HubEauQualityPoller
from iot_service.simulator.orchestrator import SimulationOrchestrator
from iot_service.simulator.sensors import SENSORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _quality_poller_loop(poller: HubEauQualityPoller):
    """Hub'Eau quality polling loop (every 6h by default)."""
    await poller.run()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start pollers + Kafka producer."""
    app.state.kafka_producer = MeasurementProducer()
    await app.state.kafka_producer.start()

    app.state.quality_poller = HubEauQualityPoller(
        producer=app.state.kafka_producer,
        interval_seconds=settings.quality_poll_interval_seconds,
    )
    quality_task = asyncio.create_task(_quality_poller_loop(app.state.quality_poller))

    sim_orchestrator = SimulationOrchestrator(
        producer=app.state.kafka_producer,
    )
    sim_orchestrator.register_all_sensors()
    sim_task = asyncio.create_task(sim_orchestrator.run())

    app.state.quality_task = quality_task
    app.state.sim_orchestrator = sim_orchestrator
    app.state.sim_task = sim_task

    try:
        yield
    finally:
        quality_task.cancel()
        sim_orchestrator.request_stop()
        sim_task.cancel()
        for t in (quality_task, sim_task):
            try:
                await t
            except asyncio.CancelledError:
                pass
        await app.state.kafka_producer.stop()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Service d'ingestion UrbanHub : collecte Hub'Eau, simulation locale "
        "et passerelle HTTP pour capteurs physiques. Publie sur Kafka "
        f"(`{settings.water_quality_topic}`)."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Health",
            "description": "Sonde de disponibilite et metriques runtime.",
        },
        {
            "name": "Ingestion",
            "description": (
                "Routes d'ingestion : declenchement Hub'Eau, simulation "
                "et reception de mesures capteurs."
            ),
        },
    ],
)


@app.get("/health", tags=["Health"], summary="Verifier l'etat du service")
async def health() -> dict:
    """Retourne l'etat des composants (Kafka, poller Hub'Eau, simulateur)."""
    poller = getattr(app.state, "quality_poller", None)
    return {
        "status": "healthy",
        "version": settings.app_version,
        "components": {
            "kafka_producer": "up" if app.state.kafka_producer.is_ready else "down",
            "quality_poller": "running",
            "quality_stations": poller.station_count if poller else 0,
        },
        "metrics": {
            "quality_cycles": poller.cycles_completed if poller else 0,
            "quality_messages_published": poller.messages_published if poller else 0,
            "total_messages_sent": app.state.kafka_producer.messages_sent,
        },
    }


@app.get(
    "/ingestion/status",
    response_model=IngestionStatusResponse,
    tags=["Ingestion"],
    summary="Etat du pipeline d'ingestion",
)
async def ingestion_status() -> IngestionStatusResponse:
    """Expose l'etat Kafka, le poller Hub'Eau et le simulateur."""
    poller: HubEauQualityPoller = app.state.quality_poller
    orchestrator: SimulationOrchestrator = app.state.sim_orchestrator
    return IngestionStatusResponse(
        kafka_ready=app.state.kafka_producer.is_ready,
        kafka_topic=settings.water_quality_topic,
        quality_poller={
            "stations": poller.station_count,
            "cycles_completed": poller.cycles_completed,
            "messages_published": poller.messages_published,
            "interval_seconds": settings.quality_poll_interval_seconds,
        },
        simulator={
            "active_sensors": len(orchestrator.sensors),
            "cycles_completed": orchestrator.cycles_completed,
            "interval_seconds": settings.simulator_interval_seconds,
        },
    )


@app.post(
    "/ingestion/hubeau",
    response_model=HubEauIngestionResponse,
    tags=["Ingestion"],
    summary="Declencher une ingestion Hub'Eau",
    responses={503: {"description": "Kafka indisponible"}},
)
async def ingest_hubeau_now() -> HubEauIngestionResponse:
    """
    Lance immediatement un cycle Hub'Eau (6 stations).

    Utile pour tests manuels, demos et validation Postman sans attendre le polling 6h.
    """
    if not app.state.kafka_producer.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kafka producer unavailable",
        )
    poller: HubEauQualityPoller = app.state.quality_poller
    published = await poller.poll_once_now()
    return HubEauIngestionResponse(
        messages_published=published,
        stations_polled=poller.station_count,
    )


@app.post(
    "/ingestion/simuler",
    response_model=SimulationIngestionResponse,
    tags=["Ingestion"],
    summary="Declencher un cycle simulateur",
    responses={503: {"description": "Kafka indisponible"}},
)
async def ingest_simulate_now() -> SimulationIngestionResponse:
    """
    Lance immediatement un cycle du simulateur local (capteurs sans Hub'Eau).

    Publie une mesure synthetique par capteur actif du simulateur.
    """
    if not app.state.kafka_producer.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kafka producer unavailable",
        )
    orchestrator: SimulationOrchestrator = app.state.sim_orchestrator
    sent = await orchestrator.run_once_now()
    return SimulationIngestionResponse(sensors_triggered=sent)


@app.post(
    "/api/sensors/{sensor_id}/metrics",
    response_model=SensorMetricsAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Ingestion"],
    summary="Ingerer une mesure capteur (passerelle HTTP)",
    responses={
        400: {"description": "Capteur inconnu"},
        503: {"description": "Kafka indisponible"},
    },
)
async def post_sensor_metrics(
    sensor_id: str, payload: SensorMetricsPayload
) -> SensorMetricsAcceptedResponse:
    """
    Passerelle HTTP d'ingestion : un capteur physique POST ses metriques.

    La mesure est convertie en `WaterMeasurementEvent` et publiee sur Kafka.
    """
    profile = next((s for s in SENSORS if s.sensor_id == sensor_id), None)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "UNKNOWN_SENSOR",
                "message": f"Sensor '{sensor_id}' is not registered in the system.",
            },
        )

    event = {
        "event_type": "mesure.qualite.eau",
        "event_id": str(uuid.uuid4()),
        "trace_id": str(uuid.uuid4()),
        "capteur_id": sensor_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "localisation": {
            "latitude": profile.latitude,
            "longitude": profile.longitude,
            "point_reference": profile.description or f"Station {profile.name}",
        },
        "mesures": {
            "ph": payload.ph,
            "turbidite_ntu": payload.turbidite_ntu,
            "temperature_c": payload.temperature_c,
            "niveau_m": payload.niveau_m,
            "debit_m3s": payload.debit_m3s,
            "oxygene_dissous_mgl": payload.oxygene_dissous_mgl,
        },
        "qualite_signal": payload.qualite_signal,
        "firmware_version": payload.firmware_version,
        "data_source": "real",
    }

    published = await app.state.kafka_producer.send(event)
    if not published:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "KAFKA_UNAVAILABLE",
                "message": "Failed to publish metrics to the event bus.",
            },
        )

    return SensorMetricsAcceptedResponse(
        status="accepted",
        event_id=event["event_id"],
        sensor_id=sensor_id,
        published=True,
    )
