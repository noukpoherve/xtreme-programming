from iot_service.sensor_service import IoTSensorSimulator, SensorMeasurement


def test_capture_retourne_une_mesure():
    sensor = IoTSensorSimulator(sensor_id="SENSOR-01")
    measurement = sensor.capture(ph=7.2, turbidity=5.0, level=1.5, flow=0.8)
    assert isinstance(measurement, SensorMeasurement)


def test_capture_stocke_tous_les_parametres():
    sensor = IoTSensorSimulator(sensor_id="SENSOR-01")
    measurement = sensor.capture(ph=7.2, turbidity=5.0, level=1.5, flow=0.8)
    assert measurement.sensor_id == "SENSOR-01"
    assert measurement.ph == 7.2
    assert measurement.turbidity == 5.0
    assert measurement.level == 1.5
    assert measurement.flow == 0.8


def test_chaque_mesure_a_un_uuid_unique():
    sensor = IoTSensorSimulator(sensor_id="SENSOR-01")
    m1 = sensor.capture(ph=7.0, turbidity=5.0, level=1.0, flow=0.5)
    m2 = sensor.capture(ph=7.0, turbidity=5.0, level=1.0, flow=0.5)
    assert m1.uuid != m2.uuid


def test_mesure_a_un_timestamp():
    sensor = IoTSensorSimulator(sensor_id="SENSOR-01")
    measurement = sensor.capture(ph=7.0, turbidity=5.0, level=1.0, flow=0.5)
    assert measurement.timestamp is not None
