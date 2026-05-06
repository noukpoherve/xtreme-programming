from iot_service.kafka_publisher import build_measurement_event
from iot_service.sensor_service import IoTSensorSimulator


def test_build_measurement_event_has_kafka_shape():
    sensor = IoTSensorSimulator(sensor_id="SENSOR-01")
    measurement = sensor.capture(ph=7.2, turbidity=12.0, level=1.5, flow=0.8)

    event = build_measurement_event(measurement)

    assert event["event_type"] == "mesure.qualite.eau"
    assert event["event_id"] == measurement.uuid
    assert event["capteur_id"] == "SENSOR-01"
    assert event["mesures"]["turbidite_ntu"] == 12.0
    assert event["mesures"]["ph"] == 7.2
    assert "trace_id" in event
