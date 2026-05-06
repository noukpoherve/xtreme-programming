# Alert Service

REST API microservice for receiving and processing water quality alerts.

## Overview

The Alert Service exposes a single REST endpoint that receives alert payloads and responds with a confirmation. It also consumes the Kafka topic `mesure.qualite.eau`, builds alert payloads from measurements, and republishes them to `alerte.pollution.detectee`.

## Architecture

```
IoT Ingestion Service  --Kafka topic mesure.qualite.eau-->  Alert Service  --Kafka topic alerte.pollution.detectee-->  Notification Service
```

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

### `POST /alertes`
Create a new alert.

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
docker run -p 8000:8000 alert-service
```

## Kafka integration

Kafka bridge is enabled in Docker Compose with:

- `ALERT_ENABLE_KAFKA_BRIDGE=true`
- `ALERT_KAFKA_BOOTSTRAP_SERVERS=kafka:9092`
- `ALERT_WATER_QUALITY_TOPIC=mesure.qualite.eau`
- `ALERT_POLLUTION_ALERT_TOPIC=alerte.pollution.detectee`
