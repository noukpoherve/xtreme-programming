"""
Realistic water quality measurement generator.

Patterns simulated:
- Diurnal cycle (slight pH variation through the day)
- Random walk (continuous variation)
- Pollution events (random spikes)
- Weather effects (rain → turbidity increase)
"""

from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from iot_service.simulator.sensors import SensorProfile


@dataclass
class GeneratedMeasurement:
    """A single generated measurement ready to be published."""

    event_type: str
    event_id: str
    trace_id: str
    capteur_id: str
    timestamp: datetime
    localisation: dict[str, Any]
    mesures: dict[str, float]
    qualite_signal: str
    firmware_version: str
    data_source: str = "simulated"


class MeasurementGenerator:
    """Stateful generator that produces realistic measurements for one sensor."""

    # Pollution scenarios
    POLLUTION_PH_CRITICAL = {"ph_delta": -2.5}  # pH drops to ~5
    POLLUTION_PH_WARNING = {"ph_delta": -1.5}  # pH drops to ~6
    POLLUTION_TURB_CRITICAL = {"turbidity_delta": 40.0}  # Turbidity goes > 50
    POLLUTION_TURB_WARNING = {"turbidity_delta": 15.0}  # Turbidity goes > 25
    POLLUTION_COMBINED = {"ph_delta": -2.0, "turbidity_delta": 30.0}

    def __init__(self, sensor: SensorProfile, seed: int | None = None):
        self.sensor = sensor
        self.rng = random.Random(seed)
        # Current state for random walk
        self._ph_walk = 0.0
        self._turb_walk = 0.0
        # Active pollution scenario (None = no pollution)
        self._active_pollution: dict[str, float] | None = None
        self._pollution_counter = 0

    def generate(self) -> GeneratedMeasurement:
        """Generate a measurement with diurnal patterns and optional pollution."""

        now = datetime.now(UTC)
        hour = now.hour + now.minute / 60.0

        # ───────────────────────────────────────────
        # 1. Decide if pollution happens this cycle
        # ───────────────────────────────────────────
        if self._active_pollution is not None:
            # Active pollution continues for a few cycles (3-5)
            self._pollution_counter += 1
            if self._pollution_counter >= self.rng.randint(3, 5):
                self._active_pollution = None
                self._pollution_counter = 0
        elif self.rng.random() < self.sensor.pollution_probability:
            # Trigger new pollution based on sensor profile
            self._active_pollution = self._pick_pollution()
            self._pollution_counter = 0

        # ───────────────────────────────────────────
        # 2. Compute pH with diurnal cycle + walk + pollution
        # ───────────────────────────────────────────
        # Diurnal variation: pH slightly higher midday (photosynthesis)
        ph_diurnal = 0.15 * math.sin((hour - 6) * math.pi / 12)
        # Random walk (small drift)
        self._ph_walk = max(
            -0.5, min(0.5, self._ph_walk + self.rng.uniform(-0.05, 0.05))
        )
        # Noise
        ph_noise = self.rng.gauss(0, 0.08)

        ph = self.sensor.ph_baseline + ph_diurnal + self._ph_walk + ph_noise

        # Apply active pollution
        if self._active_pollution and "ph_delta" in self._active_pollution:
            # Pollution decays over its duration
            decay = 1.0 - (self._pollution_counter / 5.0)
            ph += self._active_pollution["ph_delta"] * decay

        # ───────────────────────────────────────────
        # 3. Compute turbidity similarly
        # ───────────────────────────────────────────
        turb_diurnal = 2.0 * math.sin((hour - 18) * math.pi / 12)  # Higher at evening
        self._turb_walk = max(
            -5.0, min(5.0, self._turb_walk + self.rng.uniform(-1.0, 1.0))
        )
        turb_noise = self.rng.gauss(0, 1.5)

        turbidity = (
            self.sensor.turbidity_baseline + turb_diurnal + self._turb_walk + turb_noise
        )

        if self._active_pollution and "turbidity_delta" in self._active_pollution:
            decay = 1.0 - (self._pollution_counter / 5.0)
            turbidity += self._active_pollution["turbidity_delta"] * decay

        # ───────────────────────────────────────────
        # 4. Compute other measurements (less variation)
        # ───────────────────────────────────────────
        temperature = (
            self.sensor.temperature_baseline
            + 2.0 * math.sin((hour - 14) * math.pi / 12)  # Warmer afternoon
            + self.rng.gauss(0, 0.3)
        )
        oxygen = self.sensor.oxygen_baseline + self.rng.gauss(0, 0.2)
        # Constant values for now (could add flow variation later)
        niveau_m = 1.0 + self.rng.gauss(0, 0.1)
        debit_m3s = 250.0 + self.rng.gauss(0, 20.0)

        # ───────────────────────────────────────────
        # 5. Build the event
        # ───────────────────────────────────────────
        return GeneratedMeasurement(
            event_type="mesure.qualite.eau",
            event_id=str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            capteur_id=self.sensor.sensor_id,
            timestamp=now,
            localisation={
                "latitude": self.sensor.latitude,
                "longitude": self.sensor.longitude,
                "point_reference": self.sensor.name,
            },
            mesures={
                "ph": round(ph, 2),
                "turbidite_ntu": round(max(0, turbidity), 2),
                "temperature_c": round(temperature, 2),
                "niveau_m": round(niveau_m, 2),
                "debit_m3s": round(debit_m3s, 2),
                "oxygene_dissous_mgl": round(max(0, oxygen), 2),
            },
            qualite_signal="GOOD" if self.rng.random() > 0.05 else "DEGRADED",
            firmware_version="2.4.1",
            data_source="simulated",
        )

    def _pick_pollution(self) -> dict[str, float]:
        """Choose a pollution scenario based on sensor profile."""
        poll_type = self.sensor.pollution_type
        roll = self.rng.random()

        if poll_type == "ph":
            return self.rng.choice(
                [self.POLLUTION_PH_WARNING, self.POLLUTION_PH_CRITICAL]
            )
        elif poll_type == "turbidity":
            return self.rng.choice(
                [self.POLLUTION_TURB_WARNING, self.POLLUTION_TURB_CRITICAL]
            )
        else:  # both
            if roll < 0.3:
                return self.POLLUTION_PH_CRITICAL
            elif roll < 0.5:
                return self.POLLUTION_PH_WARNING
            elif roll < 0.7:
                return self.POLLUTION_TURB_CRITICAL
            elif roll < 0.85:
                return self.POLLUTION_TURB_WARNING
            else:
                return self.POLLUTION_COMBINED
