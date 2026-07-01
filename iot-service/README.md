# IoT Ingestion Service

Microservice that continuously collects sensor data from the French **Hub'Eau** API and streams raw measurements to Kafka.

## Overview

The IoT Ingestion Service runs a **background polling loop** that fetches real-time hydrometric data every 5 minutes (configurable), enriches it with default pH and turbidity values, and publishes structured `WaterMeasurementEvent` messages to the `mesure.qualite.eau` Kafka topic.

This service **only produces raw measurements** — threshold analysis and alert generation are handled entirely by the **Alert Service** via Kafka consumption.

## Architecture

```
Hub'Eau API  -->  IoT Ingestion Service  --Kafka-->  mesure.qualite.eau
                      |
                      +-- background poll loop (every 5 min)
```

## Streaming behaviour

On startup, a background `asyncio` task begins polling Hub'Eau automatically:

- Fetches latest level (m) and flow (m³/s) from the Seine river station
- Enriches with default pH and turbidity
- Publishes a `WaterMeasurementEvent` to Kafka
- Sleeps for `POLL_INTERVAL_SECONDS` (default: 300s)

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
Manual trigger — fetches the latest real sensor data from Hub'Eau and publishes it to Kafka immediately.

**Response:**
```json
{
  "measurement": {
    "sensor_id": "F700000103",
    "ph": 7.4,
    "turbidity": 8.0,
    "level": 0.93,
    "flow": 252.0,
    "latitude": 48.8447,
    "longitude": 2.3655
  },
  "published": true
}
```

### `POST /simulate`
Simulate a sensor measurement with custom parameters (useful for testing the Kafka pipeline without hitting the external API).

Legacy aliases kept for compatibility: `POST /capteurs`, `GET /capteurs`, `GET /capteurs/{sensor_id}`, `PUT /capteurs/{sensor_id}`, `DELETE /capteurs/{sensor_id}`, `GET /capteurs-stats`.

**Query params:**
- `ph` (float, default 7.0)
- `turbidity` (float, default 75.0)

The simulated measurement is published to Kafka as a raw event. The Alert Service will analyse it and generate alerts if thresholds are exceeded.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker address |
| `WATER_QUALITY_TOPIC` | `mesure.qualite.eau` | Kafka topic for raw measurements |
| `POLL_INTERVAL_SECONDS` | `300` | Hub'Eau polling interval |
| `REDIS_URL` | `redis://localhost:6379` | Redis persistence endpoint |
| `REDIS_STRICT` | `0` | Set to `1` to fail on Redis errors instead of falling back to memory |
| `DISABLE_BACKGROUND_POLL` | `0` | Set to `1` to skip the scheduled Hub'Eau poller in tests/local runs |

## Run locally

```bash
cd iot-service
PYTHONPATH=src uv run uvicorn iot_service.main:app --host 0.0.0.0 --port 8001
```

## Run tests

```bash
cd iot-service
uv run pytest tests/ -v
```

## Run with Docker

```bash
cd iot-service
docker build -t iot-service .
docker run -p 8001:8001 \
  -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
  -e WATER_QUALITY_TOPIC=mesure.qualite.eau \
  iot-service
```
