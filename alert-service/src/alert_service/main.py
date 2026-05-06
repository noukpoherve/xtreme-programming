from fastapi import FastAPI, status

from alert_service.config import settings
from alert_service.models import AlertPayload, AlertResponse
from alert_service.service import alert_service

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
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
