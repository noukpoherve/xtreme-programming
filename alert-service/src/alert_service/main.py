from contextlib import asynccontextmanager

from fastapi import FastAPI, status

from alert_service.config import settings
from alert_service.kafka_bridge import KafkaAlertBridge, NoopKafkaBridge
from alert_service.models import AlertPayload, AlertResponse
from alert_service.service import alert_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    bridge = KafkaAlertBridge() if settings.enable_kafka_bridge else NoopKafkaBridge()
    app.state.kafka_bridge = bridge
    await bridge.start()
    bridge.schedule()
    try:
        yield
    finally:
        await bridge.stop()


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
