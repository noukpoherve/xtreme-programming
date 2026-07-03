from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from iot_service.main import app


def _mock_kafka_ready():
    mock_producer = AsyncMock()
    mock_producer.is_ready = True
    mock_producer.send.return_value = True
    mock_producer.messages_sent = 0
    app.state.kafka_producer = mock_producer
    return mock_producer


def test_ingestion_status():
    with TestClient(app) as client:
        response = client.get("/ingestion/status")
        assert response.status_code == 200
        data = response.json()
        assert data["kafka_topic"] == "mesure.qualite.eau"
        assert "quality_poller" in data
        assert "simulator" in data


def test_ingest_hubeau_now():
    with TestClient(app) as client:
        _mock_kafka_ready()
        with patch.object(
            app.state.quality_poller, "poll_once_now", new_callable=AsyncMock
        ) as mock_poll:
            mock_poll.return_value = 3
            response = client.post("/ingestion/hubeau")
        assert response.status_code == 200
        assert response.json()["messages_published"] == 3
        assert response.json()["source"] == "hubeau"


def test_ingest_simulate_now():
    with TestClient(app) as client:
        _mock_kafka_ready()
        with patch.object(
            app.state.sim_orchestrator, "run_once_now", new_callable=AsyncMock
        ) as mock_run:
            mock_run.return_value = 6
            response = client.post("/ingestion/simuler")
        assert response.status_code == 200
        assert response.json()["sensors_triggered"] == 6


def test_ingest_hubeau_kafka_down():
    with TestClient(app) as client:
        mock_producer = AsyncMock()
        mock_producer.is_ready = False
        app.state.kafka_producer = mock_producer
        response = client.post("/ingestion/hubeau")
        assert response.status_code == 503
