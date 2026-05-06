"""
Client Hub'eau — API Hydrométrie v2
Endpoint : https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr

Champs disponibles via cet endpoint :
  - niveau (H) en mm   → converti en mètres dans SensorMeasurement.level
  - débit  (Q) en m³/s → SensorMeasurement.flow

Champs NON disponibles (endpoint hydrometrie ne les fournit pas) :
  - pH       → utilise une valeur par défaut configurable
  - turbidité → utilise une valeur par défaut configurable
  Source alternative : https://hubeau.eaufrance.fr/api/v1/qualite_cours_eau/
"""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from sensor_service import SensorMeasurement

_BASE_URL = "https://hubeau.eaufrance.fr/api/v2/hydrometrie/observations_tr"


@dataclass
class HubEauObservation:
    code_station: str
    grandeur_hydro: str  # "H" ou "Q"
    date_obs: str
    resultat_obs: float
    longitude: float
    latitude: float
    qualification: str  # ex. "Non qualifiée", "Bonne"


def _fetch_latest(code_entite: str, grandeur: str) -> Optional[HubEauObservation]:
    url = f"{_BASE_URL}?code_entite={code_entite}&grandeur_hydro={grandeur}&size=1"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            body = json.loads(response.read())
        data = body.get("data", [])
        if not data:
            return None
        d = data[0]
        return HubEauObservation(
            code_station=d.get("code_station", ""),
            grandeur_hydro=d.get("grandeur_hydro", ""),
            date_obs=d.get("date_obs", ""),
            resultat_obs=float(d.get("resultat_obs") or 0.0),
            longitude=float(d.get("longitude") or 0.0),
            latitude=float(d.get("latitude") or 0.0),
            qualification=d.get("libelle_qualification_obs", ""),
        )
    except (urllib.error.URLError, KeyError, ValueError):
        return None


class HubEauSensorClient:
    """
    Adaptateur entre l'API Hub'eau et le modèle SensorMeasurement.

    Usage :
        client = HubEauSensorClient(code_entite="F700000103")
        measurement = client.capture()
    """

    def __init__(
        self,
        code_entite: str,
        default_ph: float = 7.4,
        default_turbidity: float = 5.0,
    ):
        self.code_entite = code_entite
        self.default_ph = default_ph
        self.default_turbidity = default_turbidity

    def capture(self) -> SensorMeasurement:
        h_obs = _fetch_latest(self.code_entite, "H")
        q_obs = _fetch_latest(self.code_entite, "Q")

        # Hub'eau retourne le niveau en mm     → conversion en mètres
        # Hub'eau retourne le débit  en L/s    → conversion en m³/s
        level = (h_obs.resultat_obs / 1000.0) if h_obs else 0.0
        flow = (q_obs.resultat_obs / 1000.0) if q_obs else 0.0

        return SensorMeasurement(
            sensor_id=self.code_entite,
            ph=self.default_ph,
            turbidity=self.default_turbidity,
            level=level,
            flow=flow,
        )
