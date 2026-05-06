from contextlib import asynccontextmanager
import os

from fastapi import FastAPI

from iot_service.hubeau_client import HubEauSensorClient
from iot_service.kafka_publisher import (
    KAFKA_BOOTSTRAP_SERVERS,
    KafkaMeasurementPublisher,
    NoopMeasurementPublisher,
)
from iot_service.sensor_service import IoTSensorSimulator

_ENABLE_KAFKA = os.getenv("IOT_ENABLE_KAFKA", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sensor_client = HubEauSensorClient(
        code_entite="F700000103",
        default_ph=7.4,
        default_turbidity=8.0,
    )
    app.state.publisher = (
        KafkaMeasurementPublisher(KAFKA_BOOTSTRAP_SERVERS)
        if _ENABLE_KAFKA
        else NoopMeasurementPublisher()
    )
    yield


app = FastAPI(
    title="iot-service",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}


def _measurement_response(measurement):
    return {
        "sensor_id": measurement.sensor_id,
        "uuid": measurement.uuid,
        "timestamp": measurement.timestamp.isoformat(),
        "ph": measurement.ph,
        "turbidity": measurement.turbidity,
        "level": measurement.level,
        "flow": measurement.flow,
        "latitude": measurement.latitude,
        "longitude": measurement.longitude,
    }


@app.post("/ingest")
async def ingest():
    sensor_client: HubEauSensorClient = app.state.sensor_client
    publisher = app.state.publisher

    measurement = sensor_client.capture()
    publication = publisher.publish(measurement)

    return {
        "measurement": _measurement_response(measurement),
        "publication": publication,
    }


@app.post("/simulate")
async def simulate(ph: float = 7.0, turbidity: float = 75.0):
    publisher = app.state.publisher

    sensor = IoTSensorSimulator(sensor_id="SIM-001")
    measurement = sensor.capture(ph=ph, turbidity=turbidity, level=1.5, flow=0.8)
    publication = publisher.publish(measurement)

    return {
        "measurement": _measurement_response(measurement),
        "publication": publication,
    }
