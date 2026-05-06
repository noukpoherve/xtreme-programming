# IoT Ingestion Service

Microservice that collects sensor data and publishes water quality measurements to Kafka.

## Overview

The IoT Ingestion Service fetches real-time hydrometric data from the French **Hub'Eau** API (Seine river, Paris station), enriches it with default pH and turbidity values, and publishes the measurement to the Kafka topic `mesure.qualite.eau`.

## Architecture

```
Hub'Eau API  -->  IoT Ingestion Service  -->  Kafka topic mesure.qualite.eau  -->  Alert Service
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
Fetch the latest real sensor data from Hub'Eau and publish it to Kafka.

**Response:**
```json
{
  "measurement": { "sensor_id": "...", "ph": 7.4, "turbidity": 8.0, ... },
  "publication": { "topic": "mesure.qualite.eau", "published": true, ... }
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

The service publishes to Kafka when `IOT_ENABLE_KAFKA=true` and `KAFKA_BOOTSTRAP_SERVERS` is set.

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

## Kafka

Kafka publishing is enabled in Docker Compose and can be controlled with:

- `IOT_ENABLE_KAFKA=true`
- `KAFKA_BOOTSTRAP_SERVERS=kafka:9092`
