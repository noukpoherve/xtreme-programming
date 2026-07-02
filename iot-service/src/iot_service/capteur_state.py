"""Etats du capteur — implementation du pattern State (GoF)."""

from abc import ABC, abstractmethod
from enum import Enum


class CapteurEtat(str, Enum):
    ACTIF = "actif"
    MAINTENANCE = "maintenance"
    EN_PANNE = "en_panne"
    INACTIF = "inactif"


class TransitionCapteurInvalide(Exception):
    """Levee lorsqu'une transition d'etat n'est pas autorisee."""


class CapteurState(ABC):
    """Interface commune des etats — chaque etat encapsule son comportement."""

    @property
    @abstractmethod
    def nom(self) -> CapteurEtat:
        ...

    @abstractmethod
    def capturer(self, capteur: "Capteur", ph: float, turbidity: float, level: float, flow: float):
        ...

    @abstractmethod
    def activer(self, capteur: "Capteur") -> None:
        ...

    @abstractmethod
    def desactiver(self, capteur: "Capteur") -> None:
        ...

    @abstractmethod
    def mettre_en_maintenance(self, capteur: "Capteur") -> None:
        ...

    @abstractmethod
    def signaler_panne(self, capteur: "Capteur") -> None:
        ...


class ActifState(CapteurState):
    @property
    def nom(self) -> CapteurEtat:
        return CapteurEtat.ACTIF

    def capturer(self, capteur, ph, turbidity, level, flow):
        from iot_service.sensor_service import SensorMeasurement

        return SensorMeasurement(
            sensor_id=capteur.sensor_id,
            ph=ph,
            turbidity=turbidity,
            level=level,
            flow=flow,
            latitude=capteur.latitude,
            longitude=capteur.longitude,
        )

    def activer(self, capteur) -> None:
        raise TransitionCapteurInvalide("Le capteur est deja actif")

    def desactiver(self, capteur) -> None:
        capteur._transition(InactifState())

    def mettre_en_maintenance(self, capteur) -> None:
        capteur._transition(MaintenanceState())

    def signaler_panne(self, capteur) -> None:
        capteur._transition(EnPanneState())


class InactifState(CapteurState):
    @property
    def nom(self) -> CapteurEtat:
        return CapteurEtat.INACTIF

    def capturer(self, capteur, ph, turbidity, level, flow):
        raise TransitionCapteurInvalide("Capture impossible : capteur inactif")

    def activer(self, capteur) -> None:
        capteur._transition(ActifState())

    def desactiver(self, capteur) -> None:
        raise TransitionCapteurInvalide("Le capteur est deja inactif")

    def mettre_en_maintenance(self, capteur) -> None:
        capteur._transition(MaintenanceState())

    def signaler_panne(self, capteur) -> None:
        raise TransitionCapteurInvalide("Un capteur inactif ne peut pas signaler de panne")


class MaintenanceState(CapteurState):
    @property
    def nom(self) -> CapteurEtat:
        return CapteurEtat.MAINTENANCE

    def capturer(self, capteur, ph, turbidity, level, flow):
        raise TransitionCapteurInvalide("Capture impossible : capteur en maintenance")

    def activer(self, capteur) -> None:
        capteur._transition(ActifState())

    def desactiver(self, capteur) -> None:
        capteur._transition(InactifState())

    def mettre_en_maintenance(self, capteur) -> None:
        raise TransitionCapteurInvalide("Le capteur est deja en maintenance")

    def signaler_panne(self, capteur) -> None:
        capteur._transition(EnPanneState())


class EnPanneState(CapteurState):
    @property
    def nom(self) -> CapteurEtat:
        return CapteurEtat.EN_PANNE

    def capturer(self, capteur, ph, turbidity, level, flow):
        raise TransitionCapteurInvalide("Capture impossible : capteur en panne")

    def activer(self, capteur) -> None:
        capteur._transition(ActifState())

    def desactiver(self, capteur) -> None:
        capteur._transition(InactifState())

    def mettre_en_maintenance(self, capteur) -> None:
        capteur._transition(MaintenanceState())

    def signaler_panne(self, capteur) -> None:
        raise TransitionCapteurInvalide("Le capteur est deja en panne")


_ETATS: dict[CapteurEtat, CapteurState] = {
    CapteurEtat.ACTIF: ActifState(),
    CapteurEtat.INACTIF: InactifState(),
    CapteurEtat.MAINTENANCE: MaintenanceState(),
    CapteurEtat.EN_PANNE: EnPanneState(),
}


def etat_depuis_nom(nom: str) -> CapteurState:
    try:
        return _ETATS[CapteurEtat(nom)]
    except ValueError as exc:
        raise TransitionCapteurInvalide(f"Etat inconnu: {nom}") from exc
