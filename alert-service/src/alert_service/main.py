import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status

logging.basicConfig(level=logging.INFO)

from alert_service.config import settings
from alert_service.kafka_consumer import MeasurementConsumer
from alert_service.models import AlertPayload, AlertResponse
from alert_service.service import alert_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer = MeasurementConsumer()
    await consumer.start()
    task = None
    if consumer._running:
        task = asyncio.create_task(consumer.run())
    yield
    if task:
        task.cancel()
    await consumer.stop()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@app.post("/alertes", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(payload: AlertPayload):
    return await alert_service.process_alert(payload)
