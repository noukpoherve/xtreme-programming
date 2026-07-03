"""
Custom exception hierarchy for the alert service.

All domain exceptions inherit from AlertServiceError so that a single
exception handler in FastAPI can catch them and produce a uniform
JSON error response.
"""

from __future__ import annotations


class AlertServiceError(Exception):
    """
    Base exception for every business error raised by the alert service.

    Subclasses MUST define:
        - error_code:  machine-readable identifier (ex: "INVALID_MEASUREMENT")
        - http_status: HTTP status code to return (ex: 400, 404, 409, 503)
        - message:     default human-readable message

    The central error handler picks these attributes to build the response.
    """

    error_code: str = "INTERNAL_ERROR"
    http_status: int = 500

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict | None = None,
    ) -> None:
        self.message = message or self.__class__.__doc__ or self.error_code
        self.details = details or {}
        super().__init__(self.message)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"{self.__class__.__name__}("
            f"error_code={self.error_code!r}, "
            f"http_status={self.http_status}, "
            f"message={self.message!r})"
        )


# ──────────────────────────────────────────────
# 4xx — Client errors
# ──────────────────────────────────────────────
class InvalidMeasurementError(AlertServiceError):
    """Raised when a WaterMeasurementEvent fails domain validation."""

    error_code = "INVALID_MEASUREMENT"
    http_status = 422


class InvalidAlertPayloadError(AlertServiceError):
    """Raised when a manually created AlertPayload is inconsistent."""

    error_code = "INVALID_ALERT_PAYLOAD"
    http_status = 422


class SensorNotFoundError(AlertServiceError):
    """Raised when querying an unknown sensor."""

    error_code = "SENSOR_NOT_FOUND"
    http_status = 404


class SensorAlreadyRegisteredError(AlertServiceError):
    """Raised when a sensor is registered twice with conflicting thresholds."""

    error_code = "SENSOR_ALREADY_REGISTERED"
    http_status = 409


class StateTransitionError(AlertServiceError):
    """Raised when an invalid state transition is attempted."""

    error_code = "INVALID_STATE_TRANSITION"
    http_status = 409


# ──────────────────────────────────────────────
# 5xx — Server / infrastructure errors
# ──────────────────────────────────────────────
class KafkaPublishError(AlertServiceError):
    """Raised when the Kafka producer cannot send a message."""

    error_code = "KAFKA_PUBLISH_FAILED"
    http_status = 503


class KafkaConsumeError(AlertServiceError):
    """Raised when the Kafka consumer cannot process a message after retries."""

    error_code = "KAFKA_CONSUME_FAILED"
    http_status = 503


class DependencyUnavailableError(AlertServiceError):
    """Raised when a downstream service (Redis, DB, Kafka) is unreachable."""

    error_code = "DEPENDENCY_UNAVAILABLE"
    http_status = 503