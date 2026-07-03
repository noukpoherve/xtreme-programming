import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from unittest.mock import MagicMock

from alert_service.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_sensors_ok(client):
    response = await client.get("/sensors")
    assert response.status_code == 200
    data = response.json()
    assert "sensors" in data
    assert "count" in data
    assert isinstance(data["sensors"], list)


@pytest.mark.asyncio
async def test_health_ok(client):
    # Provide a fake running Kafka consumer so health returns 200 in tests
    fake_consumer = MagicMock()
    fake_consumer._running = True
    app.state.consumer = fake_consumer
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
