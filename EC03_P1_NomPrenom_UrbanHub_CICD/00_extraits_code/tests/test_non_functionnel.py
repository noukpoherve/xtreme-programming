"""
Tests non fonctionnels EC03 — iot-service.

- Temps de réponse de /health (SLA local)
- Robustesse face à des données métriques aberrantes (validation Pydantic)
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from iot_service.main import app

# Seuil EC03 : /health doit répondre vite en local/CI (sans réseau externe)
HEALTH_MAX_LATENCY_MS = 500


def _client_with_mock_kafka() -> TestClient:
    mock_producer = AsyncMock()
    mock_producer.is_ready = False
    mock_producer.messages_sent = 0
    mock_producer.send.return_value = True
    app.state.kafka_producer = mock_producer
    return TestClient(app)


def test_health_response_time_under_sla():
    """Non-fonctionnel : latence /health <= seuil (charge légère, 20 requêtes)."""
    client = _client_with_mock_kafka()
    latencies_ms: list[float] = []

    for _ in range(20):
        start = time.perf_counter()
        response = client.get("/health")
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies_ms.append(elapsed_ms)
        assert response.status_code == 200

    p95 = sorted(latencies_ms)[int(len(latencies_ms) * 0.95) - 1]
    assert p95 <= HEALTH_MAX_LATENCY_MS, (
        f"p95 latency {p95:.1f}ms exceeds SLA {HEALTH_MAX_LATENCY_MS}ms"
    )


def test_post_metrics_rejects_aberrant_ph():
    """Non-fonctionnel : rejet des valeurs hors bornes (pH > 14)."""
    client = _client_with_mock_kafka()
    payload = {
        "ph": 99.0,
        "turbidite_ntu": 12.0,
        "temperature_c": 19.5,
        "niveau_m": 1.2,
        "debit_m3s": 220.0,
        "oxygene_dissous_mgl": 8.0,
    }
    response = client.post("/api/sensors/SEINE-VITRY-001/metrics", json=payload)
    assert response.status_code == 422


def test_post_metrics_rejects_negative_turbidity():
    """Non-fonctionnel : rejet turbidité négative."""
    client = _client_with_mock_kafka()
    payload = {
        "ph": 7.0,
        "turbidite_ntu": -1.0,
        "temperature_c": 19.5,
        "niveau_m": 1.2,
        "debit_m3s": 220.0,
        "oxygene_dissous_mgl": 8.0,
    }
    response = client.post("/api/sensors/SEINE-VITRY-001/metrics", json=payload)
    assert response.status_code == 422
