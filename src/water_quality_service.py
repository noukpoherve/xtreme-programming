from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from sensor_service import SensorMeasurement


# ── Types de base ────────────────────────────────────────────────────────────


class Result:
    """Résultat d'une évaluation sur un seul paramètre (backward-compat TDD)."""

    def __init__(self, status: str, alert: bool):
        self.status = status
        self.alert = alert


@dataclass
class Alert:
    parameter: str
    value: float
    status: str
    message: str


@dataclass
class AnalysisResult:
    """Résultat d'une analyse complète d'une mesure capteur."""

    trace_id: str  # propagé depuis measurement.uuid
    overall_status: str  # NORMAL | WARNING | CRITICAL
    alerts: List[Alert] = field(default_factory=list)

    @property
    def has_alert(self) -> bool:
        return len(self.alerts) > 0


# ── Service ──────────────────────────────────────────────────────────────────


class WaterQualityService:
    # Seuils pH standard (OMS / directive eau potable)
    PH_WARNING_LOW = 6.5
    PH_WARNING_HIGH = 8.5
    PH_CRITICAL_LOW = 6.0
    PH_CRITICAL_HIGH = 9.0

    def __init__(self, warning_threshold: float, critical_threshold: float):
        # Seuils turbidité configurables (NTU)
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    # ── Évaluation turbidité (boucles TDD existantes) ────────────────────────

    def evaluate_turbidity(self, value: float) -> Result:
        if value >= self.critical_threshold:
            return Result(status="CRITICAL", alert=True)
        elif value > self.warning_threshold:
            return Result(status="WARNING", alert=True)
        else:
            return Result(status="NORMAL", alert=False)

    # ── Analyse complète d'une mesure capteur ────────────────────────────────

    def analyze(self, measurement: SensorMeasurement) -> AnalysisResult:
        alerts: List[Alert] = []

        # Turbidité
        turb = self.evaluate_turbidity(measurement.turbidity)
        if turb.alert:
            alerts.append(
                Alert(
                    parameter="turbidity",
                    value=measurement.turbidity,
                    status=turb.status,
                    message=f"Turbidité {turb.status} : {measurement.turbidity} NTU",
                )
            )

        # pH
        ph_status = self._evaluate_ph(measurement.ph)
        if ph_status != "NORMAL":
            alerts.append(
                Alert(
                    parameter="ph",
                    value=measurement.ph,
                    status=ph_status,
                    message=f"pH {ph_status} : {measurement.ph}",
                )
            )

        overall = "NORMAL"
        if any(a.status == "CRITICAL" for a in alerts):
            overall = "CRITICAL"
        elif any(a.status == "WARNING" for a in alerts):
            overall = "WARNING"

        return AnalysisResult(
            trace_id=measurement.uuid,
            overall_status=overall,
            alerts=alerts,
        )

    # ── Évaluations internes ─────────────────────────────────────────────────

    def _evaluate_ph(self, ph: float) -> str:
        if ph < self.PH_CRITICAL_LOW or ph > self.PH_CRITICAL_HIGH:
            return "CRITICAL"
        elif ph < self.PH_WARNING_LOW or ph > self.PH_WARNING_HIGH:
            return "WARNING"
        return "NORMAL"
