import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from iot_service.hubeau_client import HubEauSensorClient
from iot_service.water_quality_service import WaterQualityService
from iot_service.alert_client import AlertServiceClient

_ALERT_SERVICE_URL = os.getenv("ALERT_SERVICE_URL", "http://localhost:8000")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sensor_client = HubEauSensorClient(
        code_entite="F700000103",
        default_ph=7.4,
        default_turbidity=8.0,
    )
    app.state.quality_service = WaterQualityService(
        warning_threshold=10,
        critical_threshold=50,
    )
    app.state.alert_client = AlertServiceClient(base_url=_ALERT_SERVICE_URL)
    yield


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
    quality_service: WaterQualityService = app.state.quality_service
    alert_client: AlertServiceClient = app.state.alert_client

    measurement = sensor_client.capture()
    analysis = quality_service.analyze(measurement)

    alert_responses = []
    if analysis.has_alert:
        alert_responses = alert_client.send_alerts(analysis, measurement)

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
        "analysis": {
            "trace_id": analysis.trace_id,
            "overall_status": analysis.overall_status,
            "alerts": [
                {
                    "parameter": a.parameter,
                    "value": a.value,
                    "status": a.status,
                    "message": a.message,
                }
                for a in analysis.alerts
            ],
        },
        "alerts_sent": len(alert_responses),
        "alert_responses": alert_responses,
    }


from iot_service.sensor_service import IoTSensorSimulator


@app.post("/simulate")
async def simulate(ph: float = 7.0, turbidity: float = 75.0):
    quality_service: WaterQualityService = app.state.quality_service
    alert_client: AlertServiceClient = app.state.alert_client

    sensor = IoTSensorSimulator(sensor_id="SIM-001")
    measurement = sensor.capture(ph=ph, turbidity=turbidity, level=1.5, flow=0.8)
    analysis = quality_service.analyze(measurement)

    alert_responses = []
    if analysis.has_alert:
        alert_responses = alert_client.send_alerts(analysis, measurement)

    return {
        "analysis": {
            "overall_status": analysis.overall_status,
            "alerts": [
                {"parameter": a.parameter, "status": a.status, "message": a.message}
                for a in analysis.alerts
            ],
        },
        "alerts_sent": len(alert_responses),
        "alert_responses": alert_responses,
    }
