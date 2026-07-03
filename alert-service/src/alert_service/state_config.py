"""
Centralized sensor-state configuration.

This module is the single source of truth for:
- state machine thresholds (pH, turbidity, anomaly counts)
- the list of valid sensor states
- per-state metadata (label, severity rank)

Both the business logic (SensorStreamProcessor) and the API layer should
import from here. Keeping thresholds and state names in one place makes
it trivial to add a new state or tune thresholds without hunting through
multiple files.
"""

from __future__ import annotations

from enum import Enum


class SensorState(str, Enum):
    """Possible states of a water quality sensor."""

    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class StateThresholds:
    """Encapsulated thresholds used by the sensor state machine."""

    # pH bounds
    PH_WARNING_LOW = 6.5
    PH_WARNING_HIGH = 8.5
    PH_CRITICAL_LOW = 6.0
    PH_CRITICAL_HIGH = 9.0

    # Turbidity bounds (NTU)
    TURBIDITY_WARNING = 10.0
    TURBIDITY_CRITICAL = 50.0

    # Consecutive anomalies required to transition
    WARNING_ANOMALIES = 1
    CRITICAL_ANOMALIES = 3


class StateMetadata:
    """Read-only metadata for each sensor state."""

    _RANK: dict[SensorState, int] = {
        SensorState.NORMAL: 0,
        SensorState.WARNING: 1,
        SensorState.CRITICAL: 2,
    }

    _LABEL: dict[SensorState, str] = {
        SensorState.NORMAL: "Normal",
        SensorState.WARNING: "Attention",
        SensorState.CRITICAL: "Critique",
    }

    @classmethod
    def rank(cls, state: SensorState) -> int:
        """Severity rank: lower is calmer."""
        return cls._RANK.get(state, 99)

    @classmethod
    def label(cls, state: SensorState) -> str:
        """Human-readable label."""
        return cls._LABEL.get(state, state.value)

    @classmethod
    def ordered(cls) -> tuple[SensorState, ...]:
        """States ordered from most severe to least severe."""
        return tuple(sorted(cls._RANK.keys(), key=cls.rank, reverse=True))
