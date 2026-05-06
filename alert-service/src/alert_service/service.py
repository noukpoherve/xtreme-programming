import logging
from alert_service.models import AlertPayload

logger = logging.getLogger(__name__)


class AlertService:
    async def process_alert(self, payload: AlertPayload) -> dict:
        logger.info(f"Alert received: {payload.alert_id} (trace_id={payload.trace_id})")
        return {
            "alert_id": payload.alert_id,
            "status": "CREATED",
            "trace_id": payload.trace_id,
        }


alert_service = AlertService()
