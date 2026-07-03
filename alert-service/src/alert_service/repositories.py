"""
Repository pattern for persistence.

Each repository encapsulates access to one table or view. SOLID:
- S (Single Responsibility): one repository = one table
- D (Dependency Inversion): services depend on Repository ABC, not on asyncpg
- O (Open/Closed): add a MongoRepository without changing the service
"""

from __future__ import annotations

import abc
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import asyncpg

from alert_service.models import (
    AlertPayload,
    SensorState,
    SensorStateView,
    WaterMeasurementEvent,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# DTOs (Data Transfer Objects) — internal data structures
# ──────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class SensorRow:
    """Row from the `sensors` table."""

    id: uuid.UUID
    sensor_id: str
    name: str
    latitude: float
    longitude: float
    point_reference: str


@dataclass(frozen=True)
class StateTransitionRow:
    """Row from the `state_transitions` table."""

    sensor_uuid: uuid.UUID
    timestamp: datetime
    previous_state: str
    new_state: str
    anomaly_count: int
    anomaly_type: str | None
    trace_id: uuid.UUID


# ──────────────────────────────────────────────────────────────
# Interfaces (ABC)
# ──────────────────────────────────────────────────────────────
class SensorRepository(abc.ABC):
    """Abstract repository for sensor catalogue operations."""

    @abc.abstractmethod
    async def get_by_sensor_id(self, sensor_id: str) -> SensorRow | None: ...

    @abc.abstractmethod
    async def upsert(
        self,
        sensor_id: str,
        name: str,
        latitude: float,
        longitude: float,
        point_reference: str,
    ) -> SensorRow: ...

    @abc.abstractmethod
    async def list_all(self) -> list[SensorRow]: ...

    @abc.abstractmethod
    async def get_metadata(self, sensor_id: str) -> dict[str, Any] | None:
        """
        Return full drill-down metadata for one sensor: catalogue + state +
        firmware + last measurement timestamp. Returns None if not found.
        """


class MeasurementRepository(abc.ABC):
    """Abstract repository for water quality measurements."""

    @abc.abstractmethod
    async def insert(
        self,
        measurement: WaterMeasurementEvent,
        sensor_uuid: uuid.UUID,
    ) -> None: ...

    @abc.abstractmethod
    async def get_recent(
        self,
        sensor_uuid: uuid.UUID,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    async def get_recent_window(
        self,
        sensor_uuid: uuid.UUID,
        since: datetime,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Return measurements newer than `since`, oldest first (for charts)."""

    @abc.abstractmethod
    async def has_firmware(
        self, sensor_uuid: uuid.UUID, firmware_version: str
    ) -> bool:
        """True if at least one measurement with this firmware_version exists."""


class StateTransitionRepository(abc.ABC):
    """Abstract repository for state transitions."""

    @abc.abstractmethod
    async def insert(
        self,
        sensor_uuid: uuid.UUID,
        previous_state: SensorState,
        new_state: SensorState,
        anomaly_count: int,
        anomaly_type: str | None,
        trace_id: str,
    ) -> None: ...

    @abc.abstractmethod
    async def get_current_states(self) -> dict[uuid.UUID, SensorStateView]: ...


class AlertRepository(abc.ABC):
    """Abstract repository for alerts."""

    @abc.abstractmethod
    async def insert(self, alert: AlertPayload, sensor_uuid: uuid.UUID) -> None: ...

    @abc.abstractmethod
    async def get_open(self, limit: int = 50) -> list[dict[str, Any]]: ...

    @abc.abstractmethod
    async def count_by_state(self) -> dict[str, int]: ...

    @abc.abstractmethod
    async def get_for_sensor(
        self,
        sensor_uuid: uuid.UUID,
        limit: int = 20,
        only_open: bool = False,
    ) -> list[dict[str, Any]]: ...


# ──────────────────────────────────────────────────────────────
# PostgreSQL implementations
# ──────────────────────────────────────────────────────────────
class PostgresSensorRepository(SensorRepository):
    """PostgreSQL-backed implementation of SensorRepository."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def get_by_sensor_id(self, sensor_id: str) -> SensorRow | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, sensor_id, name, latitude, longitude, point_reference
                FROM sensors
                WHERE sensor_id = $1 AND deleted_at IS NULL
                """,
                sensor_id,
            )
            if row is None:
                return None
            return SensorRow(
                id=row["id"],
                sensor_id=row["sensor_id"],
                name=row["name"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                point_reference=row["point_reference"],
            )

    async def upsert(
        self,
        sensor_id: str,
        name: str,
        latitude: float,
        longitude: float,
        point_reference: str,
    ) -> SensorRow:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO sensors (sensor_id, name, latitude, longitude, point_reference)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (sensor_id) DO UPDATE
                SET name = EXCLUDED.name,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    point_reference = EXCLUDED.point_reference,
                    updated_at = NOW()
                RETURNING id, sensor_id, name, latitude, longitude, point_reference
                """,
                sensor_id, name, latitude, longitude, point_reference,
            )
            return SensorRow(
                id=row["id"],
                sensor_id=row["sensor_id"],
                name=row["name"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                point_reference=row["point_reference"],
            )

    async def list_all(self) -> list[SensorRow]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, sensor_id, name, latitude, longitude, point_reference
                FROM sensors
                WHERE deleted_at IS NULL
                ORDER BY sensor_id
                """
            )
            return [
                SensorRow(
                    id=r["id"],
                    sensor_id=r["sensor_id"],
                    name=r["name"],
                    latitude=r["latitude"],
                    longitude=r["longitude"],
                    point_reference=r["point_reference"],
                )
                for r in rows
            ]

    async def get_metadata(self, sensor_id: str) -> dict[str, Any] | None:
        """Return full drill-down metadata for one sensor."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    s.id,
                    s.sensor_id,
                    s.name,
                    s.latitude,
                    s.longitude,
                    s.point_reference,
                    COALESCE(st.new_state, 'NORMAL') AS state,
                    COALESCE(st.anomaly_count_at_transition, 0) AS anomaly_count,
                    COALESCE(st.previous_state, NULL) AS previous_state,
                    (SELECT firmware_version FROM measurements m
                        WHERE m.sensor_uuid = s.id
                        ORDER BY timestamp DESC LIMIT 1) AS firmware_version,
                    (SELECT timestamp FROM measurements m
                        WHERE m.sensor_uuid = s.id
                        ORDER BY timestamp DESC LIMIT 1) AS last_measurement_at
                FROM sensors s
                LEFT JOIN LATERAL (
                    SELECT new_state, previous_state, anomaly_count_at_transition
                    FROM state_transitions
                    WHERE sensor_uuid = s.id
                    ORDER BY timestamp DESC LIMIT 1
                ) st ON TRUE
                WHERE s.sensor_id = $1 AND s.deleted_at IS NULL
                """,
                sensor_id,
            )
            if row is None:
                return None
            return dict(row)


class PostgresMeasurementRepository(MeasurementRepository):
    """PostgreSQL-backed implementation of MeasurementRepository."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def insert(
        self,
        measurement: WaterMeasurementEvent,
        sensor_uuid: uuid.UUID,
    ) -> None:
        # asyncpg expects timezone-naive datetimes when the column is TIMESTAMP
        ts_naive = (
            measurement.timestamp.replace(tzinfo=None)
            if measurement.timestamp.tzinfo is not None
            else measurement.timestamp
        )
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO measurements (
                    sensor_uuid, timestamp, ph, turbidity_ntu, temperature_c,
                    level_m, flow_m3s, dissolved_oxygen_mgl,
                    signal_quality, firmware_version, trace_id, event_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (timestamp, event_id) DO NOTHING
                """,
                sensor_uuid,
                ts_naive,
                measurement.mesures.ph,
                measurement.mesures.turbidite_ntu,
                measurement.mesures.temperature_c,
                measurement.mesures.niveau_m,
                measurement.mesures.debit_m3s,
                measurement.mesures.oxygene_dissous_mgl,
                measurement.qualite_signal or "GOOD",
                measurement.firmware_version,
                uuid.UUID(measurement.trace_id),
                uuid.UUID(measurement.event_id),
            )

    async def get_recent(
        self,
        sensor_uuid: uuid.UUID,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT timestamp, ph, turbidity_ntu, temperature_c,
                       dissolved_oxygen_mgl, level_m, flow_m3s, signal_quality
                FROM measurements
                WHERE sensor_uuid = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                sensor_uuid, limit,
            )
            return [dict(r) for r in rows]

    async def get_recent_window(
        self,
        sensor_uuid: uuid.UUID,
        since: datetime,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Return the latest `limit` measurements since `since`, oldest first (chart-friendly)."""
        # asyncpg: ensure tz-naive since column is TIMESTAMP WITHOUT TIME ZONE
        since_naive = since.replace(tzinfo=None) if since.tzinfo else since
        async with self._pool.acquire() as conn:
            # ORDER BY DESC + LIMIT first to grab the LATEST N points in the
            # window (not the OLDEST N). Then reverse to oldest-first for
            # the chart. Without this, LIMIT 500 would silently drop the
            # last few hours of measurements.
            rows = await conn.fetch(
                """
                SELECT timestamp, ph, turbidity_ntu, temperature_c,
                       dissolved_oxygen_mgl, level_m, flow_m3s, signal_quality
                FROM (
                    SELECT timestamp, ph, turbidity_ntu, temperature_c,
                           dissolved_oxygen_mgl, level_m, flow_m3s, signal_quality
                    FROM measurements
                    WHERE sensor_uuid = $1 AND timestamp >= $2
                    ORDER BY timestamp DESC
                    LIMIT $3
                ) recent
                ORDER BY timestamp ASC
                """,
                sensor_uuid, since_naive, limit,
            )
            return [dict(r) for r in rows]

    async def has_firmware(
        self, sensor_uuid: uuid.UUID, firmware_version: str
    ) -> bool:
        """True if at least one measurement with this firmware_version exists."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT EXISTS (SELECT 1 FROM measurements "
                "WHERE sensor_uuid = $1 AND firmware_version = $2 LIMIT 1) AS ok",
                sensor_uuid, firmware_version,
            )
            return bool(row["ok"]) if row else False


class PostgresStateTransitionRepository(StateTransitionRepository):
    """PostgreSQL-backed implementation of StateTransitionRepository."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def insert(
        self,
        sensor_uuid: uuid.UUID,
        previous_state: SensorState,
        new_state: SensorState,
        anomaly_count: int,
        anomaly_type: str | None,
        trace_id: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO state_transitions (
                    sensor_uuid, previous_state, new_state,
                    anomaly_count_at_transition, anomaly_type, trace_id
                )
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                sensor_uuid,
                previous_state.value,
                new_state.value,
                anomaly_count,
                anomaly_type,
                uuid.UUID(trace_id),
            )

    async def get_current_states(self) -> dict[uuid.UUID, SensorStateView]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    s.id AS sensor_uuid,
                    s.sensor_id,
                    s.name,
                    COALESCE(st.new_state, 'NORMAL') AS state,
                    COALESCE(st.anomaly_count_at_transition, 0) AS anomaly_count
                FROM sensors s
                LEFT JOIN LATERAL (
                    SELECT new_state, anomaly_count_at_transition
                    FROM state_transitions
                    WHERE sensor_uuid = s.id
                    ORDER BY timestamp DESC
                    LIMIT 1
                ) st ON TRUE
                WHERE s.deleted_at IS NULL
                """
            )
            return {
                r["sensor_uuid"]: SensorStateView(
                    sensor_id=r["sensor_id"],
                    state=SensorState(r["state"]),
                    anomaly_count=r["anomaly_count"],
                    previous_state=None,
                )
                for r in rows
            }


class PostgresAlertRepository(AlertRepository):
    """PostgreSQL-backed implementation of AlertRepository."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def insert(self, alert: AlertPayload, sensor_uuid: uuid.UUID) -> None:
        ts_naive = (
            alert.timestamp.replace(tzinfo=None)
            if alert.timestamp.tzinfo is not None
            else alert.timestamp
        )
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO alerts (
                    sensor_uuid, severity, alert_type, message, trace_id,
                    status, opened_at, metadata
                )
                VALUES ($1, $2, $3, $4, $5, 'OPEN', $6, $7::jsonb)
                """,
                sensor_uuid,
                alert.severity.value,
                alert.type,
                alert.message,
                uuid.UUID(alert.trace_id),
                ts_naive,
                self._jsonify(alert.metadata),
            )

    async def get_open(self, limit: int = 50) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT a.id, a.severity, a.message, a.opened_at,
                       s.sensor_id, s.name AS sensor_name
                FROM alerts a
                JOIN sensors s ON a.sensor_uuid = s.id
                WHERE a.status IN ('OPEN', 'ACK')
                ORDER BY a.opened_at DESC
                LIMIT $1
                """,
                limit,
            )
            return [dict(r) for r in rows]

    async def count_by_state(self) -> dict[str, int]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    COUNT(*) FILTER (WHERE state = 'NORMAL') AS normal,
                    COUNT(*) FILTER (WHERE state = 'WARNING') AS warning,
                    COUNT(*) FILTER (WHERE state = 'CRITICAL') AS critical
                FROM current_sensor_state
                """
            )
            row = rows[0]
            return {
                "NORMAL": row["normal"],
                "WARNING": row["warning"],
                "CRITICAL": row["critical"],
            }

    async def get_for_sensor(
        self,
        sensor_uuid: uuid.UUID,
        limit: int = 20,
        only_open: bool = False,
    ) -> list[dict[str, Any]]:
        """Return alerts scoped to a single sensor, newest first."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT a.id, a.severity, a.message, a.opened_at, a.status,
                       s.sensor_id, s.name AS sensor_name
                FROM alerts a
                JOIN sensors s ON a.sensor_uuid = s.id
                WHERE a.sensor_uuid = $1
                  AND ($2 = false OR a.status IN ('OPEN', 'ACK'))
                ORDER BY a.opened_at DESC
                LIMIT $3
                """,
                sensor_uuid, only_open, limit,
            )
            return [dict(r) for r in rows]

    @staticmethod
    def _jsonify(metadata: dict[str, Any]) -> str:
        """Convert metadata dict to JSON string for PostgreSQL JSONB."""
        import json
        return json.dumps(metadata, default=str)


# ──────────────────────────────────────────────────────────────
# Connection pool factory
# ──────────────────────────────────────────────────────────────
async def create_pool(database_url: str) -> asyncpg.Pool:
    """Create an asyncpg connection pool from a PostgreSQL URL."""
    return await asyncpg.create_pool(
        database_url,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )