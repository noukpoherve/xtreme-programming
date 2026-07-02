import pytest
import pytest_asyncio
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient

from alert_service.main import app


@pytest_asyncio.fixture
async def client(monkeypatch):
    monkeypatch.setenv("DISABLE_BACKGROUND_CONSUMER", "1")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_end_to_end_alert_publish(client):
    payload = {
        "alert_id": "alert-int-001",
        "event_id": "event-int-001",
        "sensor_id": "SEINE-PONT-ALMA-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": "CRITICAL",
        "type": "ph_critique",
        "message": "pH critique detecte",
        "localisation": {
            "latitude": 48.8637,
            "longitude": 2.3017,
            "point_reference": "Pont de l'Alma",
        },
        "trace_id": "trace-int-001",
        "metadata": {"ph": 5.2},
    }
    response = await client.post("/alerts", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["alert_id"] == "alert-int-001"
    assert data["status"] == "CREATED"
