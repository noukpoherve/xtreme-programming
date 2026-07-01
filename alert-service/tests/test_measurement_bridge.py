from datetime import datetime, timezone

from alert_service.models import (
    Localisation,
    MeasurementValues,
    WaterMeasurementEvent,
)
from alert_service.service import AlertService


def _measurement(**overrides):
    base = {
        "event_type": "mesure.qualite.eau",
        "event_id": "event-001",
        "trace_id": "trace-001",
        "capteur_id": "SEINE-001",
        "timestamp": datetime.now(timezone.utc),
        "localisation": Localisation(
            latitude=48.8637,
            longitude=2.3017,
            point_reference="Pont de l'Alma",
        ),
        "mesures": MeasurementValues(
            ph=7.2,
            turbidite_ntu=5.0,
            temperature_c=14.3,
            niveau_m=1.5,
            debit_m3s=0.8,
            oxygene_dissous_mgl=7.1,
        ),
    }
    base.update(overrides)
    return WaterMeasurementEvent(**base)


def test_build_alerts_from_measurement_no_alert():
    service = AlertService()
    alerts = service.build_alerts_from_measurement(_measurement())
    assert alerts == []


def test_build_alerts_from_measurement_ph_and_turbidity():
    service = AlertService()
    measurement = _measurement(
        mesures=MeasurementValues(
            ph=5.2,
            turbidite_ntu=145.0,
            temperature_c=14.3,
            niveau_m=1.5,
            debit_m3s=0.8,
            oxygene_dissous_mgl=7.1,
        )
    )

    alerts = service.build_alerts_from_measurement(measurement)

    assert len(alerts) == 2
    assert {alert.type for alert in alerts} == {"ph", "turbidity"}
    assert any(alert.severity == "CRITICAL" for alert in alerts)
