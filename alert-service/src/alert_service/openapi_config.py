"""
Centralized OpenAPI / Swagger metadata for the alert service.

Single source of truth for tags, contact info, license, server URLs,
and shared response examples. Keeping this in one module means the
``main.py`` file stays focused on wiring.
"""

from __future__ import annotations

from typing import Any

from alert_service.models import ErrorResponse

# ──────────────────────────────────────────────────────────────────────
# API metadata
# ──────────────────────────────────────────────────────────────────────
API_TITLE = "UrbanHub Alert Service"
API_DESCRIPTION = """
## Water Quality Alert Service

**UrbanHub** is an event-driven platform that ingests water quality
measurements, analyzes them against configurable thresholds, and
publishes pollution alerts.

This service is the **alerting component**. It:

* **Consumes** raw `WaterMeasurementEvent` messages from the
  `mesure.qualite.eau` Kafka topic.
* **Maintains** a per-sensor state machine (NORMAL / WARNING / CRITICAL)
  that requires 3 consecutive anomalies before declaring CRITICAL.
* **Publishes** generated alerts to the `alerte.pollution.detectee`
  Kafka topic.
* **Exposes** a small REST surface for health checks, manual alert
  creation, and state inspection.

### Error contract

Every error response — regardless of the endpoint — follows the same
shape defined by `ErrorResponse`. Clients SHOULD branch on the
machine-readable `error` field rather than on `message`.

### Correlation

Every response carries an `X-Trace-Id` header. Clients can supply their
own `X-Trace-Id` request header to propagate a correlation id end to
end. The same value appears in error payloads and in structured logs.
"""

API_VERSION = "0.1.0"
API_CONTACT = {
    "name": "UrbanHub Platform Team",
    "email": "platform@urbanhub.example.com",
    "url": "https://github.com/urbanhub/urbanhub",
}

API_LICENSE = {
    "name": "MIT",
    "url": "https://opensource.org/licenses/MIT",
}

# Server URLs exposed in Swagger UI dropdown
API_SERVERS = [
    {"url": "http://localhost:8000", "description": "Local development"},
    {"url": "http://alert-service:8000", "description": "Docker compose network"},
    {"url": "https://staging.alerts.urbanhub.example.com", "description": "Staging"},
    {"url": "https://alerts.urbanhub.example.com", "description": "Production"},
]

# Tag metadata — used to group endpoints in Swagger UI
TAGS_METADATA: list[dict[str, Any]] = [
    {
        "name": "alerts",
        "description": "Create and inspect alerts.",
        "externalDocs": {
            "description": "Alert payload specification",
            "url": "https://github.com/urbanhub/urbanhub/blob/main/docs/events.md",
        },
    },
    {
        "name": "measurements",
        "description": "Submit measurements and observe state transitions.",
    },
    {
        "name": "sensors",
        "description": "Inspect the state of tracked sensors.",
    },
    {
        "name": "health",
        "description": "Liveness and readiness probes.",
    },
]


# ──────────────────────────────────────────────────────────────────────
# Shared error examples used by every endpoint's `responses` block
# ──────────────────────────────────────────────────────────────────────
def _error_example(error: str, message: str) -> dict[str, Any]:
    return {
        "summary": error,
        "value": {
            "error": error,
            "message": message,
            "trace_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "timestamp": "2026-06-29T10:30:00Z",
            "path": "/alertes",
            "details": None,
        },
    }


# Pre-built examples — referenced from every endpoint
VALIDATION_ERROR_EXAMPLE = _error_example(
    "VALIDATION_ERROR", "One or more fields failed validation."
)
INVALID_MEASUREMENT_EXAMPLE = _error_example(
    "INVALID_MEASUREMENT",
    "pH value -2.0 is outside the valid range [0.0, 14.0]",
)
SENSOR_NOT_FOUND_EXAMPLE = _error_example(
    "SENSOR_NOT_FOUND", "Sensor 'UNKNOWN-001' is not tracked by this service."
)
KAFKA_PUBLISH_FAILED_EXAMPLE = _error_example(
    "KAFKA_PUBLISH_FAILED", "Alert could not be published to Kafka."
)
INTERNAL_ERROR_EXAMPLE = _error_example(
    "INTERNAL_ERROR",
    "An unexpected error occurred. Please contact support with the trace_id.",
)


# Default responses reused by every endpoint to document the error contract
COMMON_RESPONSES: dict[int | str, dict[str, Any]] = {
    422: {
        "model": ErrorResponse,
        "description": "Validation error — the request payload is invalid.",
        "content": {
            "application/json": {
                "examples": {
                    "validation": VALIDATION_ERROR_EXAMPLE,
                    "domain": INVALID_MEASUREMENT_EXAMPLE,
                }
            }
        },
    },
    500: {
        "model": ErrorResponse,
        "description": "Internal server error.",
        "content": {
            "application/json": {"examples": {"internal": INTERNAL_ERROR_EXAMPLE}}
        },
    },
    503: {
        "model": ErrorResponse,
        "description": "A downstream dependency (Kafka) is unavailable.",
        "content": {
            "application/json": {"examples": {"kafka": KAFKA_PUBLISH_FAILED_EXAMPLE}}
        },
    },
}
