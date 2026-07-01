# Alert Service

REST API and Kafka consumer that analyses water quality thresholds and publishes alerts.

## Overview

The Alert Service:
1. **Consumes** raw `WaterMeasurementEvent` messages from the `mesure.qualite.eau` Kafka topic
2. **Analyses** pH and turbidity against configurable thresholds
3. **Publishes** generated alerts to the `alerte.pollution.detectee` Kafka topic
4. **Exposes** REST endpoints under `POST /alerts` and the legacy alias `POST /alertes`

## Architecture

```
Kafka (mesure.qualite.eau)  -->  Alert Service  -->  Kafka (alerte.pollution.detectee)
                                         |
                                         +-- REST POST /alerts
```

## Thresholds

| Parameter | Warning | Critical |
|-----------|---------|----------|
| pH | < 6.5 or > 8.5 | < 6.0 or > 9.0 |
| Turbidity | > 10 NTU | > 50 NTU |

## Endpoints

### `GET /health`
Health check.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### `POST /alerts`
Create a new alert directly via REST.

Legacy alias: `POST /alertes`

**Request body:**
```json
{
  "alert_id": "uuid-v4",
  "event_id": "uuid-v4",
  "sensor_id": "SEINE-PONT-ALMA-001",
  "timestamp": "2025-03-15T08:32:00Z",
  "severity": "CRITICAL",
  "type": "ph_critique",
  "message": "pH 5.2 < threshold 5.5",
  "localisation": {
    "latitude": 48.8637,
    "longitude": 2.3017,
    "point_reference": "Pont de l'Alma"
  },
  "trace_id": "trace-001",
  "metadata": {"ph": 5.2}
}
```

**Response:**
```json
{
  "alert_id": "uuid-v4",
  "status": "CREATED",
  "trace_id": "trace-001"
}
```

## Kafka consumer

The consumer uses `aiokafka` with:
- **Manual commit** (`enable_auto_commit=False`) for at-least-once processing
- **Structured events** parsed as `WaterMeasurementEvent` Pydantic models
- **Headers** (`trace_id`) and keyed messages (`sensor_id`)

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker address |
| `WATER_QUALITY_TOPIC` | `mesure.qualite.eau` | Input topic for measurements |
| `POLLUTION_ALERT_TOPIC` | `alerte.pollution.detectee` | Output topic for alerts |
| `KAFKA_CONSUMER_GROUP` | `alert-service-group` | Consumer group ID |
| `REDIS_URL` | `redis://localhost:6379` | Redis persistence endpoint |
| `REDIS_STRICT` | `0` | Set to `1` to fail on Redis errors instead of falling back to memory |
| `DISABLE_BACKGROUND_CONSUMER` | `0` | Set to `1` to skip the Kafka consumer in tests/local runs |

## Run locally

```bash
cd alert-service
PYTHONPATH=src uv run uvicorn alert_service.main:app --host 0.0.0.0 --port 8000
```

## Run tests

```bash
cd alert-service
uv run pytest tests/ -v
```

## Run with Docker

```bash
cd alert-service
docker build -t alert-service .
docker run -p 8000:8000 \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  alert-service
```
