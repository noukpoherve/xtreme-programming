# UrbanHub — Smart City Water Quality Platform

> Master project — Distributed architecture & Extreme Programming practices

## Architecture

UrbanHub is composed of independent microservices that communicate via REST and (future) Kafka events.

```
                    +------------------+
                    |   Hub'Eau API    |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    |  IoT Ingestion   |  <-- Fetches real sensor data
                    |    Service       |  <-- Analyses water quality
                    |   (iot-service)  |
                    +--------+---------+
                             | HTTP POST /alertes
                             v
                    +------------------+
                    |  Alert Service   |  <-- Receives & validates alerts
                    | (alert-service)  |  <-- (future) publishes to Kafka
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
              v                             v
    +------------------+          +------------------+
    |  Kafka (future)  |          |  REST consumers  |
    +--------+---------+          +--------+---------+
             |                             |
             v                             v
    +------------------+          +------------------+
    | Notification Svc |          |  Dashboard / Ops |
    +------------------+          +------------------+
```

## Services

| Service | Role | Port | Tech |
|---------|------|------|------|
| **iot-service** | Ingestion & analysis | `8001` | FastAPI, Hub'Eau client |
| **alert-service** | Alert reception & validation | `8000` | FastAPI |

## Quick start (Docker Compose)

```bash
# Build and run both services
docker-compose up --build

# Health checks
curl http://localhost:8000/health   # alert-service
curl http://localhost:8001/health   # iot-service

# Simulate a critical alert
curl -X POST "http://localhost:8001/simulate?ph=5.5&turbidity=75.0"

# Check that alerts were created
curl -X POST http://localhost:8000/alertes \
  -H "Content-Type: application/json" \
  -d '{"alert_id":"a1","event_id":"e1","sensor_id":"S1","timestamp":"2025-03-15T08:32:00Z","severity":"CRITICAL","type":"ph","message":"pH low","trace_id":"t1","metadata":{}}'
```

## Development

Each service is fully autonomous with its own `pyproject.toml`, `uv.lock`, `Dockerfile` and test suite.

```bash
cd alert-service
uv run pytest tests/ -v

cd ../iot-service
uv run pytest tests/ -v
```

## Roadmap: Kafka integration

1. **Broker** : Deploy Kafka (topic `mesure.qualite.eau`)
   IoT Service will publish raw measurements instead of calling REST.

2. **Consumer** : Alert Service consumes `mesure.qualite.eau`, analyses thresholds, then publishes to `alerte.pollution.detectee`.

3. **Notification Service** : A new microservice consumes `alerte.pollution.detectee` and sends push/email/SMS.

4. **Resilience** : Idempotence (Redis), Retry + DLQ, distributed tracing (`trace_id`).

## Project structure

```
urbanhub/
├── alert-service/          # Alert REST API
├── iot-service/            # Ingestion & analysis
├── docker-compose.yml      # Local orchestration
└── README.md               # This file
```

## CI / Tests

- `black` for formatting
- `pytest` for unit and integration tests
- `Docker` for containerised deployment
