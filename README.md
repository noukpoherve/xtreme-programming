# UrbanHub — Smart City Water Quality Platform

> Master project — Distributed architecture, event-driven microservices & Extreme Programming practices

## Architecture

UrbanHub is composed of independent microservices that communicate via REST and Kafka events.

```
                    +------------------+
                    |   Hub'Eau API    |
                    +--------+---------+
                             |
                             | (poll every 5 min)
                             v
                    +------------------+
                    |  IoT Ingestion   |  <-- Background scheduler fetches data
                    |    Service       |  <-- Publishes raw measurements to Kafka
                    |   (iot-service)  |
                    +--------+---------+
                             | Kafka: mesure.qualite.eau
                             v
                    +------------------+
                    |  Alert Service   |  <-- Consumes measurements from Kafka
                    | (alert-service)  |  <-- Analyses thresholds & publishes alerts
                    +--------+---------+
                             | Kafka: alerte.pollution.detectee
                             v
                    +------------------+
                    | Notification Svc |  <-- (future) Push / email / SMS
                    +------------------+
```

## Services

| Service | Role | Port | Tech |
|---------|------|------|------|
| **iot-service** | Ingestion & raw measurement publisher | `8001` | FastAPI, aiokafka, Hub'Eau client |
| **alert-service** | Threshold analysis & alert publisher | `8000` | FastAPI, aiokafka |
| **kafka** | Event bus (KRaft mode, no ZooKeeper) | `9092` | apache/kafka:3.7.1 |
| **kafka-ui** | Topic inspection | `8080` | kafbat/kafka-ui |
| **prometheus** | Metrics collection | `9090` | prom/prometheus |
| **grafana** | Logs & metrics dashboards | `3000` | grafana/grafana |
| **loki** | Log aggregation | `3100` | grafana/loki |
| **promtail** | Docker log shipping | — | grafana/promtail |

## Quick start (Docker Compose)

```bash
# Build and run the full stack
docker compose up --build -d

# The IoT service now polls Hub'Eau automatically every 5 minutes.
# Manual trigger if you want an immediate fetch:
curl -X POST http://localhost:8001/ingest

# Simulate a critical alert for testing
curl -X POST "http://localhost:8001/simulate?ph=5.5&turbidity=75.0"

# Inspect Kafka topics
open http://localhost:8080  # Kafka UI

# View dashboards
open http://localhost:3000  # Grafana (admin / admin)
```

## Development

Each service is fully autonomous with its own `pyproject.toml`, `uv.lock`, `Dockerfile` and test suite.

```bash
cd alert-service
uv run pytest tests/ -v

cd ../iot-service
uv run pytest tests/ -v
```

## Kafka topics

| Topic | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| `mesure.qualite.eau` | iot-service | alert-service | Raw water quality measurements |
| `alerte.pollution.detectee` | alert-service | (future) | Generated alerts after threshold analysis |

## Event format

Raw measurements use a structured `WaterMeasurementEvent`:

```json
{
  "event_type": "mesure.qualite.eau",
  "event_id": "uuid-v4",
  "trace_id": "uuid-v4",
  "capteur_id": "F700000103",
  "timestamp": "2026-05-06T14:52:01Z",
  "localisation": {
    "latitude": 48.8447,
    "longitude": 2.3655,
    "point_reference": "Station F700000103"
  },
  "mesures": {
    "ph": 7.4,
    "turbidite_ntu": 8.0,
    "temperature_c": 0.0,
    "niveau_m": 0.93,
    "debit_m3s": 252.0,
    "oxygene_dissous_mgl": 0.0
  }
}
```

## Thresholds

| Parameter | Warning | Critical |
|-----------|---------|----------|
| pH | < 6.5 or > 8.5 | < 6.0 or > 9.0 |
| Turbidity | > 10 NTU | > 50 NTU |

## CI / Tests

- `black` for formatting
- `pytest` for unit and integration tests
- GitHub Actions matrix CI for both services
- Docker build check

## Project structure

```
urbanhub/
├── alert-service/          # Alert REST API + Kafka consumer/producer
├── iot-service/            # Ingestion + Kafka producer
├── monitoring/             # Prometheus, Grafana, Loki, Promtail configs
├── docker-compose.yml      # Local orchestration
└── README.md               # This file
```
