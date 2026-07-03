import logging
import uuid
from datetime import datetime, timedelta, timezone

from alert_service.domain import SensorProcessorRegistry, SensorStreamProcessor
from alert_service.exceptions import (
    InvalidAlertPayloadError,
    InvalidMeasurementError,
    SensorNotFoundError,
)
from alert_service.models import (
    AlertPayload,
    Localisation,
    MeasurementPoint,
    MeasurementSeriesResponse,
    SensorMetadataView,
    SensorStateView,
    WaterMeasurementEvent,
)
from alert_service.state_config import SensorState, StateMetadata, StateThresholds
from alert_service.repositories import (
    AlertRepository,
    MeasurementRepository,
    SensorRepository,
    StateTransitionRepository,
)
from alert_service.websocket import WebSocketHub

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Service applicatif (orchestration)
# ──────────────────────────────────────────────────────────────────────
class AlertService:
    """
    High-level orchestration layer used by the HTTP layer.

    Dependencies are injected (SOLID-D). If a repository is None, the
    service works in "in-memory only" mode (useful for tests).
    """

    def __init__(
        self,
        sensor_repo: SensorRepository | None = None,
        measurement_repo: MeasurementRepository | None = None,
        transition_repo: StateTransitionRepository | None = None,
        alert_repo: AlertRepository | None = None,
        ws_hub: WebSocketHub | None = None,
    ) -> None:
        self.__registry = SensorProcessorRegistry()
        self._sensor_repo = sensor_repo
        self._measurement_repo = measurement_repo
        self._transition_repo = transition_repo
        self._alert_repo = alert_repo
        self._ws_hub = ws_hub

    @property
    def registry(self) -> SensorProcessorRegistry:
        """Public accessor for the underlying sensor registry."""
        return self.__registry

    async def restore_states_from_db(self) -> None:
        """
        Restaure l'état de la machine à états pour tous les capteurs
        depuis la base de données (table state_transitions).
        """
        if self._transition_repo is None:
            logger.warning("Restauration impossible : le dépôt des transitions est indisponible.")
            return

        try:
            states = await self._transition_repo.get_current_states()
            for sensor_uuid, state_view in states.items():
                sensor_id = state_view.sensor_id
                processor = SensorStreamProcessor(
                    sensor_id=sensor_id,
                    state=state_view.state,
                    anomaly_count=state_view.anomaly_count,
                    previous_state=state_view.state,
                )
                self.__registry.set(sensor_id, processor)
            logger.info("Machine à états restaurée avec succès pour %d capteurs.", len(states))
        except Exception:
            logger.exception("Erreur lors du chargement des états depuis la base de données")

    async def process_alert(self, payload: AlertPayload) -> dict:
        """
        Validate a manually created alert payload and acknowledge it.

        Raises :class:`InvalidAlertPayloadError` on inconsistent data.
        """
        if not payload.alert_id:
            raise InvalidAlertPayloadError("alert_id is required.")
        if not payload.sensor_id:
            raise InvalidAlertPayloadError("sensor_id is required.")
        if not payload.trace_id:
            raise InvalidAlertPayloadError("trace_id is required.")

        logger.info(f"Alert received: {payload.alert_id} (trace_id={payload.trace_id})")
        return {
            "alert_id": payload.alert_id,
            "status": "CREATED",
            "trace_id": payload.trace_id,
        }

    async def process_measurement(
        self, measurement: WaterMeasurementEvent
    ) -> list[AlertPayload]:
        """
        Feed a measurement into the sensor's state machine, then persist.

        Returns a list containing a single :class:`AlertPayload` if the
        state changed, otherwise an empty list.
        """
        # 1. Resolve the sensor UUID from the catalogue (if persistence is on)
        sensor_row = None
        if self._sensor_repo:
            sensor_row = await self._sensor_repo.get_by_sensor_id(measurement.capteur_id)

        # 2. Persist the raw measurement (best-effort)
        if self._measurement_repo and sensor_row:
            try:
                await self._measurement_repo.insert(measurement, sensor_row.id)
            except Exception:
                logger.exception(
                    "Failed to persist measurement sensor=%s trace_id=%s",
                    measurement.capteur_id,
                    measurement.trace_id,
                )

        # 3. Update state machine
        processor = self.__registry.get(measurement.capteur_id)
        previous, current = processor.update(measurement)

        # 4. Persist the transition (best-effort)
        if self._transition_repo and sensor_row and previous != current:
            try:
                await self._transition_repo.insert(
                    sensor_uuid=sensor_row.id,
                    previous_state=previous,
                    new_state=current,
                    anomaly_count=processor.anomaly_count,
                    anomaly_type=None,
                    trace_id=measurement.trace_id,
                )
            except Exception:
                logger.exception("Failed to persist state transition")

        # 5. No transition → no alert
        if previous == current:
            logger.debug(
                "sensor.no_transition sensor=%s state=%s anomalies=%d",
                measurement.capteur_id,
                current.value,
                processor.anomaly_count,
            )
            return []

        # 6. Build the alert and persist it
        alert = self.__build_alert(
            measurement=measurement,
            severity=current,
            alert_type="state_transition",
            message=(
                f"Transition {previous.value} -> {current.value} "
                f"(anomalies cumulées: {processor.anomaly_count})"
            ),
            previous_state=previous,
        )

        if self._alert_repo and sensor_row:
            try:
                await self._alert_repo.insert(alert, sensor_row.id)
            except Exception:
                logger.exception("Failed to persist alert")

        # 7. Broadcast the transition via WebSocket (real-time)
        if self._ws_hub:
            try:
                await self._ws_hub.broadcast(
                    "state_transition",
                    {
                        "sensor_id": measurement.capteur_id,
                        "previous_state": previous.value,
                        "new_state": current.value,
                        "anomaly_count": processor.anomaly_count,
                        "alert_id": alert.alert_id,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "trace_id": measurement.trace_id,
                    },
                )
            except Exception:
                logger.exception("Failed to broadcast transition")

        return [alert]

    async def list_sensors(self) -> list[SensorStateView]:
        """
        Return the public view of every tracked sensor.

        Reads from the DB (so it survives restarts and includes Hub'Eau sensors
        whose measurements are only published every 6h). Falls back to the
        in-memory registry when the DB is unavailable.
        """
        if self._transition_repo is not None:
            try:
                states = await self._transition_repo.get_current_states()
                return sorted(
                    states.values(),
                    key=lambda v: v.sensor_id,
                )
            except Exception:
                logger.exception("list_sensors: DB read failed, falling back to registry")

        processors = self.__registry.all()
        return [
            SensorStateView(
                sensor_id=p.sensor_id,
                state=p.state,
                anomaly_count=p.anomaly_count,
                previous_state=self.__registry._previous_state_of(p.sensor_id),
            )
            for p in processors
        ]

    async def get_sensor(self, sensor_id: str) -> SensorStateView:
        """
        Return the public view of a single sensor.

        Prefers the live in-memory processor (most up-to-date state) when
        available; otherwise reads from the DB via the transition repo.
        """
        # 1. Try live registry first (most up-to-date)
        processors = self.__registry.all()
        match = next((p for p in processors if p.sensor_id == sensor_id), None)
        if match is not None:
            return SensorStateView(
                sensor_id=match.sensor_id,
                state=match.state,
                anomaly_count=match.anomaly_count,
                previous_state=self.__registry._previous_state_of(sensor_id),
            )
        # 2. Fallback to DB
        if self._transition_repo is not None:
            try:
                states = await self._transition_repo.get_current_states()
                # states is keyed by sensor_uuid, not sensor_id — need to map
                if self._sensor_repo is not None:
                    cat = await self._sensor_repo.get_by_sensor_id(sensor_id)
                    if cat is not None and cat.id in states:
                        return states[cat.id]
            except Exception:
                logger.exception("get_sensor: DB fallback failed")
        # 3. Not found anywhere
        raise SensorNotFoundError(
            f"Sensor '{sensor_id}' is not tracked by this service.",
            details={"sensor_id": sensor_id},
        )

    async def get_sensor_metadata(self, sensor_id: str) -> SensorMetadataView:
        """
        Return full drill-down metadata for a sensor: catalogue + state + last seen.

        Raises SensorNotFoundError if the sensor is unknown to the DB.
        """
        if self._sensor_repo is None:
            raise SensorNotFoundError(
                f"Sensor catalogue is unavailable (no DB).",
                details={"sensor_id": sensor_id},
            )
        row = await self._sensor_repo.get_metadata(sensor_id)
        if row is None:
            raise SensorNotFoundError(
                f"Sensor '{sensor_id}' is not in the catalogue.",
                details={"sensor_id": sensor_id},
            )

        # Prefer in-memory live state if the processor exists, else fall back to DB.
        processors = self.__registry.all()
        match = next((p for p in processors if p.sensor_id == sensor_id), None)
        live_state = match.state if match else SensorState(row.get("state", "NORMAL"))
        live_anomaly = (
            match.anomaly_count if match else int(row.get("anomaly_count") or 0)
        )
        live_previous = (
            self.__registry._previous_state_of(sensor_id)
            if match
            else (SensorState(row["previous_state"]) if row.get("previous_state") else None)
        )

        # data_source is inferred from firmware_version. A sensor is
        # considered "real" (Hub'Eau) if it has at least one measurement
        # with firmware_version = "Hub'Eau v2" in the DB. Otherwise it's
        # purely simulated. This is more robust than checking only the
        # latest measurement (which may be from the simulator).
        firmware = row.get("firmware_version")
        data_source = "simulated"  # default
        if self._measurement_repo is not None:
            sensor_uuid = await _resolve_uuid(self._sensor_repo, sensor_id)
            has_real = await self._measurement_repo.has_firmware(
                sensor_uuid, "Hub'Eau v2"
            )
            if has_real:
                data_source = "real"

        return SensorMetadataView(
            sensor_id=row["sensor_id"],
            name=row["name"],
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            point_reference=row["point_reference"] or "",
            state=live_state,
            anomaly_count=live_anomaly,
            previous_state=live_previous,
            data_source=data_source,
            firmware_version=firmware,
            last_measurement_at=row.get("last_measurement_at"),
        )

    async def get_measurement_series(
        self,
        sensor_id: str,
        hours: int = 24,
        limit: int = 500,
    ) -> MeasurementSeriesResponse:
        """Return the recent time-series for a sensor."""
        if self._sensor_repo is None or self._measurement_repo is None:
            raise SensorNotFoundError(
                f"Persistence is unavailable.",
                details={"sensor_id": sensor_id},
            )
        # Validate sensor exists (raises 404 if not)
        await self.get_sensor_metadata(sensor_id)

        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        sensor_uuid = await _resolve_uuid(self._sensor_repo, sensor_id)
        rows = await self._measurement_repo.get_recent_window(
            sensor_uuid,
            since=since,
            limit=min(limit, 2000),
        )
        return MeasurementSeriesResponse(
            sensor_id=sensor_id,
            hours=hours,
            count=len(rows),
            points=[
                MeasurementPoint(
                    timestamp=r["timestamp"],
                    ph=float(r["ph"]),
                    temperature_c=float(r["temperature_c"]),
                    turbidity_ntu=float(r["turbidity_ntu"]),
                    dissolved_oxygen_mgl=float(r["dissolved_oxygen_mgl"]),
                    signal_quality=r.get("signal_quality"),
                )
                for r in rows
            ],
        )

    async def get_alerts_for_sensor(
        self,
        sensor_id: str,
        limit: int = 20,
        only_open: bool = False,
    ) -> list[dict]:
        """Return recent alerts scoped to a single sensor."""
        if self._sensor_repo is None or self._alert_repo is None:
            raise SensorNotFoundError(
                f"Persistence is unavailable.",
                details={"sensor_id": sensor_id},
            )
        # Validate sensor exists
        await self.get_sensor_metadata(sensor_id)
        sensor_uuid = await _resolve_uuid(self._sensor_repo, sensor_id)
        rows = await self._alert_repo.get_for_sensor(sensor_uuid, limit, only_open)
        return [
            {
                "id": str(r["id"]),
                "severity": r["severity"],
                "message": r["message"],
                "opened_at": r["opened_at"].isoformat(),
                "sensor_id": r["sensor_id"],
                "sensor_name": r["sensor_name"],
            }
            for r in rows
        ]

    def build_alerts_from_measurement(
        self, measurement: WaterMeasurementEvent
    ) -> list[AlertPayload]:
        """
        Construit les alertes À PARTIR de l'état du processor (pas de if/else en chaîne).
        Une alerte n'est émise que lors d'une TRANSITION d'état.
        """
        processor = self.__registry.get(measurement.capteur_id)
        previous, current = processor.update(measurement)

        # Pas de transition → pas d'alerte (évite le spam)
        if previous == current:
            logger.debug(
                "sensor=%s no transition (state=%s, anomalies=%d)",
                measurement.capteur_id,
                current.value,
                processor.anomaly_count,
            )
            return []

        return [
            self.__build_alert(
                measurement=measurement,
                severity=current,
                alert_type="state_transition",
                message=(
                    f"Transition {previous.value} -> {current.value} "
                    f"(anomalies cumulées: {processor.anomaly_count})"
                ),
                previous_state=previous,
            )
        ]

    def __build_alert(
        self,
        measurement: WaterMeasurementEvent,
        severity: SensorState,
        alert_type: str,
        message: str,
        previous_state: SensorState,
    ) -> AlertPayload:
        return AlertPayload(
            alert_id=str(uuid.uuid4()),
            event_id=measurement.event_id,
            sensor_id=measurement.capteur_id,
            timestamp=measurement.timestamp,
            severity=severity,
            type=alert_type,
            message=message,
            localisation=Localisation(
                latitude=measurement.localisation.latitude,
                longitude=measurement.localisation.longitude,
                point_reference=measurement.localisation.point_reference,
            ),
            trace_id=measurement.trace_id,
            metadata={
                "previous_state": previous_state.value,
                "current_state": severity.value,
                "source_event_type": measurement.event_type,
            },
            data_source=getattr(measurement, "data_source", "simulated"),
        )


# Singleton partagé par tous les modules (consumer, API)
alert_service = AlertService()


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
async def _resolve_uuid(sensor_repo: SensorRepository, sensor_id: str) -> uuid.UUID:
    """Resolve a public sensor_id (string) to its internal UUID."""
    row = await sensor_repo.get_by_sensor_id(sensor_id)
    if row is None:
        raise SensorNotFoundError(
            f"Sensor '{sensor_id}' is not in the catalogue.",
            details={"sensor_id": sensor_id},
        )
    return row.id
