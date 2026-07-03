from datetime import datetime, timezone

from alert_service.models import (
    MeasurementLocalisation,
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
        "localisation": MeasurementLocalisation(
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
    """
    A single measurement can only trigger ONE state transition.
    Even if both pH and turbidity are abnormal, the state machine advances
    by one step (NORMAL → WARNING). The severity hint is ignored by the
    transition logic; only the anomaly count matters.
    """
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

    # One measurement → one transition → one alert
    assert len(alerts) == 1
    assert alerts[0].severity.value == "WARNING"
    assert alerts[0].type == "state_transition"


def test_build_alerts_from_measurement_reaches_critical_after_three_anomalies():
    """
    Send three consecutive anomalous measurements for the same sensor
    to verify the progression NORMAL → WARNING → CRITICAL.
    """
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

    first = service.build_alerts_from_measurement(measurement)
    second = service.build_alerts_from_measurement(measurement)
    third = service.build_alerts_from_measurement(measurement)

    assert len(first) == 1 and first[0].severity.value == "WARNING"
    assert len(second) == 0  # still WARNING, no transition
    assert len(third) == 1 and third[0].severity.value == "CRITICAL"
