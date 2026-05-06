import pytest
import pytest_asyncio
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient

from alert_service.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_alert_success(client):
    payload = {
        "alert_id": "alert-001",
        "event_id": "event-001",
        "capteur_id": "SEINE-PONT-ALMA-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": "CRITICAL",
        "type": "ph_critique",
        "message": "pH 5.2 < seuil 5.5",
        "localisation": {
            "latitude": 48.8637,
            "longitude": 2.3017,
            "point_reference": "Pont de l'Alma",
        },
        "trace_id": "trace-001",
        "metadata": {"ph": 5.2},
    }
    response = await client.post("/alertes", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["alert_id"] == "alert-001"
    assert data["status"] == "CREATED"
    assert data["trace_id"] == "trace-001"


@pytest.mark.asyncio
async def test_health_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
