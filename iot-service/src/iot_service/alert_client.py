"""
Client HTTP vers le service Alertes.

Usage :
    from alert_client import AlertServiceClient
    client = AlertServiceClient(base_url="http://localhost:8000")
    client.send_alerts(analysis_result, measurement)
"""

import json
import uuid
import urllib.error
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone

from iot_service.sensor_service import SensorMeasurement
from iot_service.water_quality_service import AnalysisResult

_DEFAULT_BASE_URL = "http://localhost:8000"


def _isoformat(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class AlertServiceClient:
    def __init__(self, base_url: str = _DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def send_alerts(
        self, analysis: AnalysisResult, measurement: SensorMeasurement
    ) -> list[dict]:
        """Envoie chaque alerte de l'analyse au service Alertes via POST /alertes."""
        responses = []
        for alert in analysis.alerts:
            payload = {
                "alert_id": str(uuid.uuid4()),
                "event_id": measurement.uuid,
                "sensor_id": measurement.sensor_id,
                "timestamp": _isoformat(measurement.timestamp),
                "severity": alert.status,
                "type": alert.parameter,
                "message": alert.message,
                "localisation": {
                    "latitude": measurement.latitude,
                    "longitude": measurement.longitude,
                    "point_reference": f"Station {measurement.sensor_id}",
                },
                "trace_id": analysis.trace_id,
                "metadata": {
                    "value": alert.value,
                    "overall_status": analysis.overall_status,
                },
            }
            resp = self._post("/alertes", payload)
            responses.append(resp)
        return responses

    def _post(self, path: str, payload: dict) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return {
                    "status_code": response.status,
                    "body": json.loads(response.read()),
                }
        except urllib.error.HTTPError as e:
            return {
                "status_code": e.code,
                "body": e.read().decode("utf-8"),
            }
        except urllib.error.URLError as e:
            return {
                "status_code": None,
                "error": str(e.reason),
            }
