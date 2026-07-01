import pytest
import pytest_asyncio
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient

from alert_service.main import app
from alert_service.service import AlertService


@pytest_asyncio.fixture
async def client(monkeypatch):
    monkeypatch.setenv("DISABLE_BACKGROUND_CONSUMER", "1")
    app.state.alert_service = AlertService()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _payload(alert_id: str = "alert-001"):
    return {
        "alert_id": alert_id,
        "event_id": "event-001",
        "sensor_id": "SEINE-PONT-ALMA-001",
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


@pytest.mark.asyncio
async def test_create_alert_success(client):
    response = await client.post("/alerts", json=_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["alert_id"] == "alert-001"
    assert data["status"] == "CREATED"
    assert data["trace_id"] == "trace-001"


@pytest.mark.asyncio
async def test_create_alert_legacy_alias_still_works(client):
    response = await client.post("/alertes", json=_payload("alert-alias-001"))
    assert response.status_code == 201
    data = response.json()
    assert data["alert_id"] == "alert-alias-001"


@pytest.mark.asyncio
async def test_create_alert_conflict_returns_409(client):
    payload = _payload("alert-conflict-001")
    first = await client.post("/alerts", json=payload)
    assert first.status_code == 201

    second = await client.post("/alerts", json=payload)
    assert second.status_code == 409
    data = second.json()
    assert data["success"] is False
    assert data["error_code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_get_alert_not_found_returns_404(client):
    response = await client.get("/alerts/missing-alert")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_unknown_route_returns_standard_404(client):
    response = await client.get("/totally-unknown-route")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_method_not_allowed_returns_standard_405(client):
    response = await client.post("/health")
    assert response.status_code == 405
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "METHOD_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_alert_stats_supports_query_option(client):
    await client.post("/alerts", json=_payload("alert-stats-001"))
    response = await client.get("/alerts", params={"option": "stats"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_alerts"] >= 1


@pytest.mark.asyncio
async def test_validation_error_returns_standard_error(client):
    response = await client.post("/alerts", json={"alert_id": "invalid"})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_health_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
