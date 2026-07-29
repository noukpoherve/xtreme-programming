"""
Extrait EC03 — UrbanHub iot-service (API FastAPI).
Source canonique : iot-service/src/iot_service/main.py
"""
import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from iot_service.simulator.sensors import SENSORS

from iot_service.config import settings
from iot_service.kafka_producer import MeasurementProducer
from iot_service.quality_poller import HubEauQualityPoller
from iot_service.simulator.orchestrator import SimulationOrchestrator

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
    version=settings.app_version,
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    """Liveness probe + component status."""
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


class SensorMetricsPayload(BaseModel):
    ph: float = Field(..., ge=0.0, le=14.0, description="pH level (0-14)")
    turbidite_ntu: float = Field(..., ge=0.0, description="Turbidity in NTU")
    temperature_c: float = Field(..., description="Temperature in Celsius")
    niveau_m: float = Field(..., ge=0.0, description="Water level in meters")
    debit_m3s: float = Field(..., ge=0.0, description="Flow rate in m3/s")
    oxygene_dissous_mgl: float = Field(
        ..., ge=0.0, description="Dissolved oxygen in mg/L"
    )
    qualite_signal: str = Field("GOOD", description="Quality of signal")
    firmware_version: str = Field("1.0.0", description="Firmware version of the sensor")


@app.post("/api/sensors/{sensor_id}/metrics", status_code=202)
async def post_sensor_metrics(sensor_id: str, payload: SensorMetricsPayload):
    """
    HTTP Ingestion Gateway: Allows physical IoT sensors to POST metrics directly.
    Maps input payload to a canonical WaterMeasurementEvent and publishes it to Kafka.
    """
    profile = next((s for s in SENSORS if s.sensor_id == sensor_id), None)
    if not profile:
        raise HTTPException(
            status_code=400,
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
            status_code=503,
            detail={
                "error": "KAFKA_UNAVAILABLE",
                "message": "Failed to publish metrics to the event bus.",
            },
        )

    return {
        "status": "accepted",
        "event_id": event["event_id"],
        "sensor_id": sensor_id,
        "published": True,
    }
