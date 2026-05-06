from water_quality_service import WaterQualityService
from sensor_service import IoTSensorSimulator

# -------------------------------------------------------
# Scénario : Turbidité critique détectée (SCRUM-8 + SCRUM-11)
# Given les seuils configurés sont : attention=10, critique=50
# When le capteur envoie une turbidité de 75 NTU
# Then le statut retourné est "CRITIQUE"
# And une alerte est générée
# -------------------------------------------------------


def test_turbidite_critique():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(75)
    assert result.status == "CRITICAL"
    assert result.alert == True


def test_turbidite_attention():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(25)
    assert result.status == "WARNING"
    assert result.alert == True


def test_turbidite_normale():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(5)
    assert result.status == "NORMAL"
    assert result.alert == False


def test_turbidite_exactement_au_seuil_critique():
    service = WaterQualityService(warning_threshold=10, critical_threshold=50)
    result = service.evaluate_turbidity(50)
    assert result.status == "CRITICAL"
    assert result.alert == True


# -------------------------------------------------------
# Analyse complète d'une mesure capteur IoT
# -------------------------------------------------------


def _make_service():
    return WaterQualityService(warning_threshold=10, critical_threshold=50)


def _make_sensor():
    return IoTSensorSimulator(sensor_id="SENSOR-01")


def test_analyse_mesure_normale_aucune_alerte():
    service = _make_service()
    sensor = _make_sensor()
    measurement = sensor.capture(ph=7.2, turbidity=5.0, level=1.5, flow=0.8)
    result = service.analyze(measurement)
    assert result.overall_status == "NORMAL"
    assert result.has_alert == False
    assert result.alerts == []


def test_analyse_turbidite_critique_genere_alerte():
    service = _make_service()
    sensor = _make_sensor()
    measurement = sensor.capture(ph=7.2, turbidity=75.0, level=1.5, flow=0.8)
    result = service.analyze(measurement)
    assert result.overall_status == "CRITICAL"
    assert result.has_alert == True
    assert any(a.parameter == "turbidity" for a in result.alerts)


def test_analyse_ph_critique_genere_alerte():
    service = _make_service()
    sensor = _make_sensor()
    measurement = sensor.capture(ph=5.5, turbidity=5.0, level=1.5, flow=0.8)
    result = service.analyze(measurement)
    assert result.overall_status == "CRITICAL"
    assert any(a.parameter == "ph" for a in result.alerts)


def test_analyse_ph_en_attention():
    service = _make_service()
    sensor = _make_sensor()
    measurement = sensor.capture(ph=6.2, turbidity=5.0, level=1.5, flow=0.8)
    result = service.analyze(measurement)
    assert result.overall_status == "WARNING"
    assert any(a.parameter == "ph" and a.status == "WARNING" for a in result.alerts)


def test_analyse_trace_id_correspond_au_uuid_capteur():
    service = _make_service()
    sensor = _make_sensor()
    measurement = sensor.capture(ph=7.2, turbidity=5.0, level=1.5, flow=0.8)
    result = service.analyze(measurement)
    assert result.trace_id == measurement.uuid


def test_analyse_statut_global_critique_si_un_parametre_critique():
    service = _make_service()
    sensor = _make_sensor()
    # pH warning + turbidité critique → overall CRITICAL
    measurement = sensor.capture(ph=6.2, turbidity=75.0, level=1.5, flow=0.8)
    result = service.analyze(measurement)
    assert result.overall_status == "CRITICAL"
