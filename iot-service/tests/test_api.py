import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from iot_service.main import app
from iot_service.sensor_service import SensorMeasurement
from iot_service.sensor_repository import SensorRepository


class DummyProducer:
    def __init__(self, published: bool = True):
        self.published = published

    async def send(self, measurement):
        return self.published


class DummySensorClient:
    def capture(self):
        return SensorMeasurement(
            sensor_id="F700000103",
            ph=7.4,
            turbidity=8.0,
            level=0.93,
            flow=252.0,
            latitude=48.8447,
            longitude=2.3655,
        )


@pytest_asyncio.fixture
async def client(monkeypatch):
    monkeypatch.setenv("DISABLE_BACKGROUND_POLL", "1")
    app.state.sensor_repository = SensorRepository()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _sensor_payload(sensor_id: str = "SEINE-001"):
    return {
        "sensor_id": sensor_id,
        "name": "Seine Sensor Pont Alma",
        "location": "Paris, Pont de l'Alma",
        "latitude": 48.8637,
        "longitude": 2.3017,
        "active": True,
        "metadata": {"model": "WaterPro3000"},
    }


@pytest.mark.asyncio
async def test_register_sensor_success(client):
    response = await client.post("/sensors", json=_sensor_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["sensor_id"] == "SEINE-001"
    assert data["status"] == "registered"


@pytest.mark.asyncio
async def test_register_sensor_legacy_alias_still_works(client):
    response = await client.post("/capteurs", json=_sensor_payload("SENSOR-ALIAS-001"))
    assert response.status_code == 201
    data = response.json()
    assert data["sensor_id"] == "SENSOR-ALIAS-001"


@pytest.mark.asyncio
async def test_register_sensor_conflict_returns_409(client):
    payload = _sensor_payload("SENSOR-CONFLICT-001")
    first = await client.post("/sensors", json=payload)
    assert first.status_code == 201

    second = await client.post("/sensors", json=payload)
    assert second.status_code == 409
    data = second.json()
    assert data["success"] is False
    assert data["error_code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_get_sensor_not_found_returns_404(client):
    response = await client.get("/sensors/missing-sensor")
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
async def test_update_sensor_partial_payload(client):
    await client.post("/sensors", json=_sensor_payload("SENSOR-UPDATE-001"))

    response = await client.put(
        "/sensors/SENSOR-UPDATE-001",
        json={"active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == "SENSOR-UPDATE-001"
    assert data["status"] == "updated"

    detail = await client.get("/sensors/SENSOR-UPDATE-001")
    assert detail.status_code == 200
    assert detail.json()["active"] is False


@pytest.mark.asyncio
async def test_sensor_stats_supports_query_option(client):
    await client.post("/sensors", json=_sensor_payload("SENSOR-STATS-001"))
    response = await client.get("/sensors", params={"option": "stats"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_sensors"] >= 1


@pytest.mark.asyncio
async def test_validation_error_returns_standard_error(client):
    response = await client.post("/sensors", json={"sensor_id": "INVALID"})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_ingest_returns_503_when_kafka_unavailable(client):
    app.state.sensor_client = DummySensorClient()
    app.state.kafka_producer = DummyProducer(published=False)

    response = await client.post("/ingest")
    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert data["error_code"] == "SERVICE_UNAVAILABLE"


@pytest.mark.asyncio
async def test_ingest_succeeds_with_stubbed_producer(client):
    app.state.sensor_client = DummySensorClient()
    app.state.kafka_producer = DummyProducer(published=True)

    response = await client.post("/ingest")
    assert response.status_code == 200
    data = response.json()
    assert data["sensor_id"] == "F700000103"
    assert data["published"] is True


@pytest.mark.asyncio
async def test_capteur_transition_maintenance(client):
    await client.post("/sensors", json=_sensor_payload("STATE-001"))
    response = await client.post("/sensors/STATE-001/maintenance")
    assert response.status_code == 200
    assert response.json()["etat"] == "maintenance"

    detail = await client.get("/sensors/STATE-001")
    assert detail.json()["etat"] == "maintenance"
    assert detail.json()["active"] is False


@pytest.mark.asyncio
async def test_capteur_transition_activer_apres_maintenance(client):
    await client.post("/sensors", json=_sensor_payload("STATE-002"))
    await client.post("/sensors/STATE-002/maintenance")
    response = await client.post("/sensors/STATE-002/activer")
    assert response.status_code == 200
    assert response.json()["etat"] == "actif"


@pytest.mark.asyncio
async def test_capteur_transition_invalide_retourne_409(client):
    await client.post("/sensors", json=_sensor_payload("STATE-003"))
    response = await client.post("/sensors/STATE-003/activer")
    assert response.status_code == 409
