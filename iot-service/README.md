# IoT Ingestion Service

Microservice that collects sensor data, analyses water quality thresholds, and forwards alerts to the Alert Service.

## Overview

The IoT Ingestion Service fetches real-time hydrometric data from the French **Hub'Eau** API (Seine river, Paris station), enriches it with default pH and turbidity values, and analyses the measurements against configured thresholds. When an anomaly is detected, it calls the Alert Service synchronously via `POST /alertes`.

## Architecture

```
Hub'Eau API  -->  IoT Ingestion Service  --HTTP POST /alertes-->  Alert Service
                      |
                      +-- Analyse pH / turbidity / level / flow
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

### `POST /ingest`
Fetch the latest real sensor data from Hub'Eau, analyse it, and forward any alerts to the Alert Service.

**Response:**
```json
{
  "measurement": { "sensor_id": "...", "ph": 7.4, "turbidity": 8.0, ... },
  "analysis": { "overall_status": "NORMAL", "alerts": [] },
  "alerts_sent": 0
}
```

### `POST /simulate`
Simulate a sensor measurement with custom parameters (useful for testing alert propagation without hitting the external API).

**Query params:**
- `ph` (float, default 7.0)
- `turbidity` (float, default 75.0)

**Response:** same shape as `/ingest`.

## Run locally

```bash
cd iot-service
PYTHONPATH=src uv run uvicorn iot_service.main:app --host 0.0.0.0 --port 8001
```

The service expects the Alert Service at `http://localhost:8000`. You can override this with the environment variable `ALERT_SERVICE_URL`.

## Run tests

```bash
cd iot-service
uv run pytest tests/ -v
```

## Run with Docker

```bash
cd iot-service
docker build -t iot-service .
docker run -p 8001:8001 -e ALERT_SERVICE_URL=http://host.docker.internal:8000 iot-service
```

## Future: Kafka integration

When the event bus is introduced, the synchronous `POST /alertes` call will be replaced (or complemented) by an **async event** published to a Kafka topic (`mesure.qualite.eau`). The Alert Service will then consume this topic instead of (or in addition to) receiving direct REST calls.
