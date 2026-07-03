"""
Domain layer for the water quality state machine.

Defines the core business entities, aggregate roots, and invariants.
"""

from __future__ import annotations

from alert_service.models import WaterMeasurementEvent
from alert_service.state_config import SensorState, StateThresholds


class SensorStreamProcessor:
    """
    Machine à états (Aggregate Root) pour un capteur de qualité de l'eau.

    Règle d'or : l'état et le compteur d'anomalies sont PRIVÉS.
    La seule façon de faire évoluer l'état est d'appeler update().
    """

    def __init__(
        self,
        sensor_id: str,
        state: SensorState = SensorState.NORMAL,
        anomaly_count: int = 0,
        previous_state: SensorState = SensorState.NORMAL,
    ) -> None:
        # ── Attributs PRIVÉS (name mangling __x → _Classe__x)
        self.__sensor_id: str = sensor_id
        self.__state: SensorState = state
        self.__anomaly_count: int = anomaly_count
        self.__previous_state: SensorState = previous_state

    # ────────────────────────────────────────────────
    # API publique en LECTURE SEULE (propriétés)
    # ────────────────────────────────────────────────
    @property
    def state(self) -> SensorState:
        """État actuel du capteur."""
        return self.__state

    @property
    def anomaly_count(self) -> int:
        """Nombre d'anomalies cumulées."""
        return self.__anomaly_count

    @property
    def sensor_id(self) -> str:
        """Identifiant du capteur suivi."""
        return self.__sensor_id

    @property
    def previous_state(self) -> SensorState:
        """État précédent du capteur (lecture seule)."""
        return self.__previous_state

    def update(self, measurement: WaterMeasurementEvent) -> tuple[SensorState, SensorState]:
        """
        Met à jour l'état interne à partir d'une nouvelle mesure.
        Retourne (état_précédent, nouvel_état) pour permettre la détection de transitions.
        """
        # 1. Détection d'anomalies (encapsulée, privée)
        is_anomaly, anomaly_type, severity_hint = self.__detect_anomaly(measurement)

        # 2. Mise à jour du compteur (logique de fenêtre glissante simple)
        if is_anomaly:
            self.__anomaly_count += 1
        else:
            self.__anomaly_count = max(0, self.__anomaly_count - 1)

        # 3. Mémorisation de l'état précédent AVANT transition
        self.__previous_state = self.__state

        # 4. Transition d'état (encapsulée, privée)
        self.__transition_state()

        return self.__previous_state, self.__state

    # ────────────────────────────────────────────────
    # Méthodes PRIVÉES — internes uniquement
    # ────────────────────────────────────────────────
    def __detect_anomaly(
        self, measurement: WaterMeasurementEvent
    ) -> tuple[bool, str | None, SensorState]:
        """
        Analyse la mesure et retourne (is_anomaly, anomaly_type, severity_hint).
        severity_hint est l'état que la mesure SUGGÈRE (pas l'état confirmé).
        """
        ph = measurement.mesures.ph
        turbidity = measurement.mesures.turbidite_ntu
        thresholds = StateThresholds

        # pH hors-bornes critiques → CRITICAL direct
        if ph < thresholds.PH_CRITICAL_LOW or ph > thresholds.PH_CRITICAL_HIGH:
            return True, "ph", SensorState.CRITICAL

        # pH hors-bornes warning → WARNING direct
        if ph < thresholds.PH_WARNING_LOW or ph > thresholds.PH_WARNING_HIGH:
            return True, "ph", SensorState.WARNING

        # Turbidité critique
        if turbidity > thresholds.TURBIDITY_CRITICAL:
            return True, "turbidity", SensorState.CRITICAL

        # Turbidité warning
        if turbidity > thresholds.TURBIDITY_WARNING:
            return True, "turbidity", SensorState.WARNING

        return False, None, SensorState.NORMAL

    def __transition_state(self) -> None:
        """Met à jour l'état selon le compteur d'anomalies."""
        thresholds = StateThresholds
        if self.__anomaly_count >= thresholds.CRITICAL_ANOMALIES:
            self.__state = SensorState.CRITICAL
        elif self.__anomaly_count >= thresholds.WARNING_ANOMALIES:
            self.__state = SensorState.WARNING
        else:
            self.__state = SensorState.NORMAL


# ──────────────────────────────────────────────────────────────────────
# Registre de processors — un état par capteur
# ──────────────────────────────────────────────────────────────────────
class SensorProcessorRegistry:
    """
    Maintient une instance de SensorStreamProcessor par capteur.
    Permet de persister l'état entre les messages Kafka entrants.
    """

    def __init__(self) -> None:
        self.__processors: dict[str, SensorStreamProcessor] = {}

    def get(self, sensor_id: str) -> SensorStreamProcessor:
        """Retourne le processor d'un capteur, en crée un nouveau si besoin."""
        if sensor_id not in self.__processors:
            self.__processors[sensor_id] = SensorStreamProcessor(sensor_id)
        return self.__processors[sensor_id]

    def set(self, sensor_id: str, processor: SensorStreamProcessor) -> None:
        """Enregistre ou met à jour manuellement un processor."""
        self.__processors[sensor_id] = processor

    def all(self) -> list[SensorStreamProcessor]:
        """Liste de tous les processors actifs (debug / observabilité)."""
        return list(self.__processors.values())

    def reset(self, sensor_id: str) -> None:
        """Réinitialise l'état d'un capteur (utile pour tests / maintenance)."""
        self.__processors.pop(sensor_id, None)

    def _previous_state_of(self, sensor_id: str) -> SensorState:
        """
        Read the previous state of a sensor.

        Used by AlertService to build public views. Returns the current
        state if the sensor is unknown (defensive — callers should not
        rely on this for error handling).
        """
        proc = self.__processors.get(sensor_id)
        if proc is None:
            return SensorState.NORMAL
        return proc.previous_state
