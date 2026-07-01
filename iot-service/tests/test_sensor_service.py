from iot_service.domain.models import SensorMeasurement
from iot_service.sensor_service import Sensor


def test_capture_retourne_une_mesure():
    sensor = Sensor(sensor_id="SENSOR-01")
    measurement = sensor.capture(ph=7.2, turbidity=5.0, level=1.5, flow=0.8)
    assert isinstance(measurement, SensorMeasurement)


def test_capture_stocke_tous_les_parametres():
    sensor = Sensor(sensor_id="SENSOR-01")
    measurement = sensor.capture(ph=7.2, turbidity=5.0, level=1.5, flow=0.8)
    assert measurement.sensor_id == "SENSOR-01"
    assert measurement.ph == 7.2
    assert measurement.turbidity == 5.0
    assert measurement.level == 1.5
    assert measurement.flow == 0.8


def test_chaque_mesure_a_un_uuid_unique():
    sensor = Sensor(sensor_id="SENSOR-01")
    m1 = sensor.capture(ph=7.0, turbidity=5.0, level=1.0, flow=0.5)
    m2 = sensor.capture(ph=7.0, turbidity=5.0, level=1.0, flow=0.5)
    assert m1.uuid != m2.uuid


def test_mesure_a_un_timestamp():
    sensor = Sensor(sensor_id="SENSOR-01")
    measurement = sensor.capture(ph=7.0, turbidity=5.0, level=1.0, flow=0.5)
    assert measurement.timestamp is not None


def test_sensor_utilise_ses_metadonnees_par_defaut():
    sensor = Sensor(
        sensor_id="SENSOR-02",
        latitude=48.86,
        longitude=2.35,
        firmware_version="3.0.0",
        qualite_signal="DEGRADED",
    )
    measurement = sensor.capture(ph=7.0, turbidity=5.0, level=1.0, flow=0.5)
    assert measurement.latitude == 48.86
    assert measurement.longitude == 2.35
    assert measurement.firmware_version == "3.0.0"
    assert measurement.qualite_signal == "DEGRADED"


def test_capture_accepte_override_lat_lon():
    sensor = Sensor(sensor_id="SENSOR-03", latitude=0.0, longitude=0.0)
    measurement = sensor.capture(
        ph=7.0, turbidity=5.0, level=1.0, flow=0.5, latitude=48.86, longitude=2.35
    )
    assert measurement.latitude == 48.86
    assert measurement.longitude == 2.35
