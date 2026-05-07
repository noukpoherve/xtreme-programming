import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)

from iot_service.hubeau_client import HubEauSensorClient
from iot_service.kafka_producer import MeasurementProducer
from iot_service.sensor_service import IoTSensorSimulator

_KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
_POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))


async def _poll_loop(
    sensor_client: HubEauSensorClient, kafka_producer: MeasurementProducer
):
    while True:
        try:
            measurement = sensor_client.capture()
            await kafka_producer.send(measurement)
            logging.info(
                "Scheduled ingest: sensor=%s level=%.2f flow=%.2f",
                measurement.sensor_id,
                measurement.level,
                measurement.flow,
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
    await app.state.kafka_producer.start()

    task = asyncio.create_task(
        _poll_loop(app.state.sensor_client, app.state.kafka_producer)
    )

    yield

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


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "0.1.0"}


@app.post("/ingest")
async def ingest():
    sensor_client: HubEauSensorClient = app.state.sensor_client
    kafka_producer: MeasurementProducer = app.state.kafka_producer

    measurement = sensor_client.capture()
    await kafka_producer.send(measurement)

    return {
        "measurement": {
            "sensor_id": measurement.sensor_id,
            "uuid": measurement.uuid,
            "timestamp": measurement.timestamp.isoformat(),
            "ph": measurement.ph,
            "turbidity": measurement.turbidity,
            "level": measurement.level,
            "flow": measurement.flow,
            "latitude": measurement.latitude,
            "longitude": measurement.longitude,
        },
        "published": True,
    }


@app.post("/simulate")
async def simulate(ph: float = 7.0, turbidity: float = 75.0):
    kafka_producer: MeasurementProducer = app.state.kafka_producer

    sensor = IoTSensorSimulator(sensor_id="SIM-001")
    measurement = sensor.capture(ph=ph, turbidity=turbidity, level=1.5, flow=0.8)
    await kafka_producer.send(measurement)

    return {
        "measurement": {
            "sensor_id": measurement.sensor_id,
            "uuid": measurement.uuid,
            "timestamp": measurement.timestamp.isoformat(),
            "ph": measurement.ph,
            "turbidity": measurement.turbidity,
            "level": measurement.level,
            "flow": measurement.flow,
            "latitude": measurement.latitude,
            "longitude": measurement.longitude,
        },
        "published": True,
    }
