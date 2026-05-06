"""
Stratégie de test pour HubEauSensorClient
------------------------------------------
Le client fait de vrais appels HTTP → on ne peut pas dépendre du réseau en CI.
Solution : mocker urllib.request.urlopen avec unittest.mock.patch.

Principe du mock :
  - On remplace urlopen par un faux objet qui retourne le JSON qu'on contrôle
  - Les tests sont déterministes, rapides, et fonctionnent sans connexion
  - Les conversions d'unités (mm→m, L/s→m³/s) sont vérifiées sur des valeurs connues

Ordre des appels dans HubEauSensorClient.capture() :
  1er appel urlopen → données H (niveau)
  2ème appel urlopen → données Q (débit)
  → on utilise side_effect=[réponse_H, réponse_Q] pour les distinguer
"""

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from iot_service.hubeau_client import HubEauSensorClient

# ── Helpers ──────────────────────────────────────────────────────────────────


def _mock_response(observations: list) -> MagicMock:
    """Crée un faux contexte urlopen retournant le JSON donné."""
    body = json.dumps({"data": observations}).encode()
    response = MagicMock()
    response.read.return_value = body
    response.__enter__ = lambda s: s
    response.__exit__ = MagicMock(return_value=False)
    return response


def _mock_empty() -> MagicMock:
    """Faux urlopen retournant une liste vide (aucune donnée)."""
    return _mock_response([])


_H_OBS = {
    "code_station": "F700000103",
    "grandeur_hydro": "H",
    "date_obs": "2026-05-06T12:00:00Z",
    "resultat_obs": 1051.0,  # 1051 mm dans l'API
    "longitude": 2.365510635,
    "latitude": 48.84468962,
    "libelle_qualification_obs": "Non qualifiée",
}

_Q_OBS = {
    "code_station": "F700000103",
    "grandeur_hydro": "Q",
    "date_obs": "2026-05-06T12:00:00Z",
    "resultat_obs": 348000.0,  # 348 000 L/s dans l'API
    "longitude": 2.365510635,
    "latitude": 48.84468962,
    "libelle_qualification_obs": "Non qualifiée",
}


# ── Tests de conversion d'unités ─────────────────────────────────────────────


def test_niveau_converti_mm_en_metres():
    """L'API retourne le niveau en mm → le service doit le convertir en mètres."""
    client = HubEauSensorClient(code_entite="F700000103")
    with patch("iot_service.hubeau_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [_mock_response([_H_OBS]), _mock_response([_Q_OBS])]
        measurement = client.capture()
    assert measurement.level == pytest.approx(1.051)


def test_debit_converti_ls_en_m3s():
    """L'API retourne le débit en L/s → le service doit le convertir en m³/s."""
    client = HubEauSensorClient(code_entite="F700000103")
    with patch("iot_service.hubeau_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [_mock_response([_H_OBS]), _mock_response([_Q_OBS])]
        measurement = client.capture()
    assert measurement.flow == pytest.approx(348.0)


# ── Tests de mapping ─────────────────────────────────────────────────────────


def test_sensor_id_correspond_au_code_entite():
    client = HubEauSensorClient(code_entite="F700000103")
    with patch("iot_service.hubeau_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [_mock_response([_H_OBS]), _mock_response([_Q_OBS])]
        measurement = client.capture()
    assert measurement.sensor_id == "F700000103"


def test_ph_utilise_la_valeur_par_defaut():
    client = HubEauSensorClient(code_entite="F700000103", default_ph=7.8)
    with patch("iot_service.hubeau_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [_mock_response([_H_OBS]), _mock_response([_Q_OBS])]
        measurement = client.capture()
    assert measurement.ph == 7.8


def test_turbidite_utilise_la_valeur_par_defaut():
    client = HubEauSensorClient(code_entite="F700000103", default_turbidity=12.5)
    with patch("iot_service.hubeau_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [_mock_response([_H_OBS]), _mock_response([_Q_OBS])]
        measurement = client.capture()
    assert measurement.turbidity == 12.5


# ── Tests de robustesse ───────────────────────────────────────────────────────


def test_niveau_vaut_zero_si_api_retourne_liste_vide():
    """Aucune donnée H → level=0.0, pas d'exception."""
    client = HubEauSensorClient(code_entite="F700000103")
    with patch("iot_service.hubeau_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [_mock_empty(), _mock_response([_Q_OBS])]
        measurement = client.capture()
    assert measurement.level == 0.0


def test_debit_vaut_zero_si_api_retourne_liste_vide():
    """Aucune donnée Q → flow=0.0, pas d'exception."""
    client = HubEauSensorClient(code_entite="F700000103")
    with patch("iot_service.hubeau_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = [_mock_response([_H_OBS]), _mock_empty()]
        measurement = client.capture()
    assert measurement.flow == 0.0


def test_capture_resilient_si_api_indisponible():
    """Réseau coupé → URLError absorbée, level=0 et flow=0, pas de crash."""
    client = HubEauSensorClient(code_entite="F700000103")
    with patch("iot_service.hubeau_client.urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.URLError("timeout")
        measurement = client.capture()
    assert measurement.level == 0.0
    assert measurement.flow == 0.0
