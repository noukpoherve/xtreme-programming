# tests/test_water_quality.py

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from water_quality_service import WaterQualityService

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
