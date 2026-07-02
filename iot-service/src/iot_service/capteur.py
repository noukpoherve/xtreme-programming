"""Entite domaine Capteur — encapsulation + pattern State."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from iot_service.capteur_state import CapteurEtat, CapteurState, ActifState, etat_depuis_nom
from iot_service.sensor_repository import Sensor

if TYPE_CHECKING:
    from iot_service.sensor_service import SensorMeasurement


class Capteur:
    """
    Capteur metier : isole la logique d'etat et de capture.
    Le comportement depend de l'etat courant (pattern State).
    """

    def __init__(
        self,
        sensor_id: str,
        name: str,
        location: str,
        latitude: float,
        longitude: float,
        metadata: dict | None = None,
        etat: CapteurState | None = None,
    ):
        self.sensor_id = sensor_id
        self.name = name
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.metadata = metadata or {}
        self._etat = etat or ActifState()

    @property
    def etat_nom(self) -> CapteurEtat:
        return self._etat.nom

    @property
    def active(self) -> bool:
        return self._etat.nom == CapteurEtat.ACTIF

    def _transition(self, nouvel_etat: CapteurState) -> None:
        self._etat = nouvel_etat

    def capturer(
        self, ph: float, turbidity: float, level: float, flow: float
    ) -> SensorMeasurement:
        return self._etat.capturer(self, ph, turbidity, level, flow)

    def activer(self) -> None:
        self._etat.activer(self)

    def desactiver(self) -> None:
        self._etat.desactiver(self)

    def mettre_en_maintenance(self) -> None:
        self._etat.mettre_en_maintenance(self)

    def signaler_panne(self) -> None:
        self._etat.signaler_panne(self)

    @classmethod
    def from_sensor(cls, sensor: Sensor) -> Capteur:
        if not sensor.active and sensor.etat == CapteurEtat.ACTIF.value:
            etat_nom = CapteurEtat.INACTIF.value
        elif sensor.etat:
            etat_nom = sensor.etat
        else:
            etat_nom = CapteurEtat.ACTIF.value if sensor.active else CapteurEtat.INACTIF.value
        return cls(
            sensor_id=sensor.sensor_id,
            name=sensor.name,
            location=sensor.location,
            latitude=sensor.latitude,
            longitude=sensor.longitude,
            metadata=sensor.metadata,
            etat=etat_depuis_nom(etat_nom),
        )

    def to_sensor(self) -> Sensor:
        return Sensor(
            sensor_id=self.sensor_id,
            name=self.name,
            location=self.location,
            latitude=self.latitude,
            longitude=self.longitude,
            active=self.active,
            etat=self._etat.nom.value,
            metadata=self.metadata,
        )
