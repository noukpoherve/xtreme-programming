from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from iot_service.main import app


def test_post_sensor_metrics_ok():
    client = TestClient(app)

    # Mock the kafka producer on app.state
    mock_producer = AsyncMock()
    mock_producer.send.return_value = True
    app.state.kafka_producer = mock_producer

    payload = {
        "ph": 7.5,
        "turbidite_ntu": 12.0,
        "temperature_c": 19.5,
        "niveau_m": 1.2,
        "debit_m3s": 220.0,
        "oxygene_dissous_mgl": 8.0,
        "qualite_signal": "GOOD",
        "firmware_version": "1.2.3",
    }

    response = client.post("/api/sensors/SEINE-VITRY-001/metrics", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"
    assert data["sensor_id"] == "SEINE-VITRY-001"
    assert data["published"] is True

    # Verify the producer send was called
    mock_producer.send.assert_called_once()
    called_arg = mock_producer.send.call_args[0][0]
    assert called_arg["capteur_id"] == "SEINE-VITRY-001"
    assert called_arg["mesures"]["ph"] == 7.5
    assert called_arg["data_source"] == "real"


def test_post_sensor_metrics_unknown_sensor():
    client = TestClient(app)
    payload = {
        "ph": 7.5,
        "turbidite_ntu": 12.0,
        "temperature_c": 19.5,
        "niveau_m": 1.2,
        "debit_m3s": 220.0,
        "oxygene_dissous_mgl": 8.0,
    }
    response = client.post("/api/sensors/UNKNOWN-SENSOR-007/metrics", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"] == "UNKNOWN_SENSOR"
