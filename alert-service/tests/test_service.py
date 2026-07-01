import pytest
from datetime import datetime, timezone

from alert_service.models import (
    AlertPayload,
    Localisation,
    MeasurementLocalisation,
    MeasurementValues,
    WaterMeasurementEvent,
)
from alert_service.service import AlertService


@pytest.fixture
def service():
    return AlertService()


@pytest.fixture
def sample_payload():
    return AlertPayload(
        alert_id="alert-123",
        event_id="event-123",
        sensor_id="SEINE-001",
        timestamp=datetime.now(timezone.utc),
        severity="CRITICAL",
        type="ph_critique",
        message="pH trop bas",
        localisation=Localisation(
            latitude=48.8637,
            longitude=2.3017,
            point_reference="Pont Alma",
        ),
        trace_id="trace-123",
        metadata={"ph": 5.2},
    )


@pytest.mark.asyncio
async def test_process_alert_created(service, sample_payload):
    result = await service.process_alert(sample_payload)
    assert result["status"] == "CREATED"
    assert result["alert_id"] == "alert-123"


def test_build_alerts_uses_injected_rules():
    class DummyRule:
        def evaluate(self, measurement):
            return [
                AlertPayload(
                    alert_id="rule-alert",
                    event_id=measurement.event_id,
                    sensor_id=measurement.capteur_id,
                    timestamp=measurement.timestamp,
                    severity="WARNING",
                    type="custom",
                    message="custom rule applied",
                    localisation=Localisation(
                        latitude=measurement.localisation.latitude,
                        longitude=measurement.localisation.longitude,
                        point_reference=measurement.localisation.point_reference,
                    ),
                    trace_id=measurement.trace_id,
                    metadata={"source": "test"},
                )
            ]

    service = AlertService(rules=[DummyRule()])
    measurement = WaterMeasurementEvent(
        event_type="measurement",
        event_id="event-001",
        trace_id="trace-001",
        capteur_id="sensor-001",
        timestamp=datetime.now(timezone.utc),
        localisation=MeasurementLocalisation(
            latitude=48.8566,
            longitude=2.3522,
            point_reference="Paris",
        ),
        mesures=MeasurementValues(
            ph=7.2,
            turbidite_ntu=12.0,
            temperature_c=14.0,
            niveau_m=1.2,
            debit_m3s=0.4,
            oxygene_dissous_mgl=8.0,
        ),
    )

    alerts = service.build_alerts_from_measurement(measurement)

    assert len(alerts) == 1
    assert alerts[0].message == "custom rule applied"
