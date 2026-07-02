"""Tests unitaires du pattern State sur la classe Capteur."""

import pytest

from iot_service.capteur import Capteur
from iot_service.capteur_state import (
    ActifState,
    CapteurEtat,
    EnPanneState,
    InactifState,
    MaintenanceState,
    TransitionCapteurInvalide,
    etat_depuis_nom,
)
from iot_service.sensor_repository import Sensor


def _capteur(etat=None) -> Capteur:
    return Capteur(
        sensor_id="SEINE-001",
        name="Capteur Seine",
        location="Paris",
        latitude=48.86,
        longitude=2.35,
        etat=etat,
    )


def test_capteur_actif_peut_capturer():
    capteur = _capteur()
    mesure = capteur.capturer(ph=7.2, turbidity=5.0, level=1.0, flow=0.5)
    assert mesure.sensor_id == "SEINE-001"
    assert mesure.ph == 7.2


def test_capteur_en_panne_ne_peut_pas_capturer():
    capteur = _capteur(EnPanneState())
    with pytest.raises(TransitionCapteurInvalide):
        capteur.capturer(ph=7.0, turbidity=5.0, level=1.0, flow=0.5)


def test_transition_actif_vers_maintenance():
    capteur = _capteur()
    capteur.mettre_en_maintenance()
    assert capteur.etat_nom == CapteurEtat.MAINTENANCE
    assert capteur.active is False


def test_transition_maintenance_vers_actif():
    capteur = _capteur(MaintenanceState())
    capteur.activer()
    assert capteur.etat_nom == CapteurEtat.ACTIF


def test_transition_invalide_actif_vers_actif():
    capteur = _capteur()
    with pytest.raises(TransitionCapteurInvalide):
        capteur.activer()


def test_transition_panne_vers_actif():
    capteur = _capteur(EnPanneState())
    capteur.activer()
    assert capteur.etat_nom == CapteurEtat.ACTIF


def test_roundtrip_sensor_repository():
    capteur = _capteur()
    capteur.signaler_panne()
    sensor = capteur.to_sensor()
    restored = Capteur.from_sensor(sensor)
    assert restored.etat_nom == CapteurEtat.EN_PANNE


def test_from_sensor_compatibilite_active_sans_etat():
    sensor = Sensor(
        sensor_id="LEGACY-01",
        name="Legacy",
        location="Lyon",
        latitude=45.0,
        longitude=4.0,
        active=False,
        metadata={},
    )
    capteur = Capteur.from_sensor(sensor)
    assert capteur.etat_nom == CapteurEtat.INACTIF


def test_etat_depuis_nom_inconnu():
    with pytest.raises(TransitionCapteurInvalide):
        etat_depuis_nom("etat_inexistant")
