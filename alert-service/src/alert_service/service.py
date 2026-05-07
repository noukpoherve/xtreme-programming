import logging
import uuid

from alert_service.models import (
    AlertPayload,
    Localisation,
    WaterMeasurementEvent,
)

logger = logging.getLogger(__name__)


class AlertService:
    PH_WARNING_LOW = 6.5
    PH_WARNING_HIGH = 8.5
    PH_CRITICAL_LOW = 6.0
    PH_CRITICAL_HIGH = 9.0
    TURBIDITY_WARNING = 10.0
    TURBIDITY_CRITICAL = 50.0

    async def process_alert(self, payload: AlertPayload) -> dict:
        logger.info(f"Alert received: {payload.alert_id} (trace_id={payload.trace_id})")
        return {
            "alert_id": payload.alert_id,
            "status": "CREATED",
            "trace_id": payload.trace_id,
        }

    def build_alerts_from_measurement(
        self, measurement: WaterMeasurementEvent
    ) -> list[AlertPayload]:
        alerts: list[AlertPayload] = []

        ph = measurement.mesures.ph
        if ph < self.PH_CRITICAL_LOW or ph > self.PH_CRITICAL_HIGH:
            alerts.append(
                self._build_alert(
                    measurement,
                    severity="CRITICAL",
                    alert_type="ph",
                    message=f"pH critique detecte: {ph}",
                )
            )
        elif ph < self.PH_WARNING_LOW or ph > self.PH_WARNING_HIGH:
            alerts.append(
                self._build_alert(
                    measurement,
                    severity="WARNING",
                    alert_type="ph",
                    message=f"pH en attention: {ph}",
                )
            )

        turbidity = measurement.mesures.turbidite_ntu
        if turbidity > self.TURBIDITY_CRITICAL:
            alerts.append(
                self._build_alert(
                    measurement,
                    severity="CRITICAL",
                    alert_type="turbidity",
                    message=f"Turbidite critique detectee: {turbidity} NTU",
                )
            )
        elif turbidity > self.TURBIDITY_WARNING:
            alerts.append(
                self._build_alert(
                    measurement,
                    severity="WARNING",
                    alert_type="turbidity",
                    message=f"Turbidite en attention: {turbidity} NTU",
                )
            )

        return alerts

    def _build_alert(
        self,
        measurement: WaterMeasurementEvent,
        severity: str,
        alert_type: str,
        message: str,
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
                "overall_status": severity,
                "source_event_type": measurement.event_type,
            },
        )


alert_service = AlertService()
