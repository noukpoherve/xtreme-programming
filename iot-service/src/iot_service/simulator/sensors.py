"""
Catalog of 12 realistic water quality sensors along the Seine in Paris.

Each sensor has:
- Real GPS coordinates (from actual monitoring stations or bridges)
- A baseline pH / turbidity profile
- A pollution scenario (some sensors trigger anomalies more often)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class SensorProfile:
    """Static profile of a virtual sensor."""

    sensor_id: str
    name: str
    latitude: float
    longitude: float
    # Baseline values
    ph_baseline: float
    turbidity_baseline: float
    temperature_baseline: float
    oxygen_baseline: float
    # Pollution profile
    pollution_probability: float  # 0.0 to 1.0 per cycle
    pollution_type: Literal["ph", "turbidity", "both"] = "both"
    # Description for UI
    description: str = ""


# 12 real Seine sensors from upstream (east) to downstream (west)
SENSORS: list[SensorProfile] = [
    SensorProfile(
        sensor_id="SEINE-VITRY-001",
        name="Vitry-sur-Seine",
        latitude=48.7876,
        longitude=2.3926,
        ph_baseline=7.6,
        turbidity_baseline=8.0,
        temperature_baseline=18.5,
        oxygen_baseline=8.5,
        pollution_probability=0.02,
        description="Amont de Paris - zone industrielle",
    ),
    SensorProfile(
        sensor_id="SEINE-CHARENTON-002",
        name="Charenton-le-Pont",
        latitude=48.8207,
        longitude=2.4151,
        ph_baseline=7.5,
        turbidity_baseline=10.0,
        temperature_baseline=18.8,
        oxygen_baseline=8.3,
        pollution_probability=0.03,
        description="Confluence Marne/Seine",
    ),
    SensorProfile(
        sensor_id="SEINE-BERCY-003",
        name="Bercy",
        latitude=48.8359,
        longitude=2.3823,
        ph_baseline=7.4,
        turbidity_baseline=12.0,
        temperature_baseline=19.0,
        oxygen_baseline=8.0,
        pollution_probability=0.04,
        description="Quai de Bercy - trafic fluvial",
    ),
    SensorProfile(
        sensor_id="SEINE-AUSTERLITZ-004",
        name="Pont d'Austerlitz",
        latitude=48.8447,
        longitude=2.3655,
        ph_baseline=7.4,
        turbidity_baseline=15.0,
        temperature_baseline=19.2,
        oxygen_baseline=7.8,
        pollution_probability=0.05,
        pollution_type="turbidity",
        description="Zone urbaine dense",
    ),
    SensorProfile(
        sensor_id="SEINE-ILES-LOUVRE-005",
        name="Île de la Cité",
        latitude=48.8530,
        longitude=2.3470,
        ph_baseline=7.3,
        turbidity_baseline=18.0,
        temperature_baseline=19.5,
        oxygen_baseline=7.5,
        pollution_probability=0.06,
        description="Cœur de Paris - bateaux-mouches",
    ),
    SensorProfile(
        sensor_id="SEINE-CONCORDE-006",
        name="Pont de la Concorde",
        latitude=48.8637,
        longitude=2.3017,
        ph_baseline=7.3,
        turbidity_baseline=20.0,
        temperature_baseline=19.8,
        oxygen_baseline=7.3,
        pollution_probability=0.07,
        pollution_type="both",
        description="Haut lieu touristique",
    ),
    SensorProfile(
        sensor_id="SEINE-ALMA-007",
        name="Pont de l'Alma",
        latitude=48.8637,
        longitude=2.3017,
        ph_baseline=7.2,
        turbidity_baseline=22.0,
        temperature_baseline=20.0,
        oxygen_baseline=7.0,
        pollution_probability=0.08,
        description="Zouave et crue de la Seine",
    ),
    SensorProfile(
        sensor_id="SEINE-TOUR-EIFFEL-008",
        name="Tour Eiffel",
        latitude=48.8584,
        longitude=2.2945,
        ph_baseline=7.2,
        turbidity_baseline=25.0,
        temperature_baseline=20.2,
        oxygen_baseline=6.8,
        pollution_probability=0.10,
        pollution_type="turbidity",
        description="Zone touristique majeure",
    ),
    SensorProfile(
        sensor_id="SEINE-IENA-009",
        name="Pont d'Iéna",
        latitude=48.8597,
        longitude=2.2923,
        ph_baseline=7.1,
        turbidity_baseline=28.0,
        temperature_baseline=20.5,
        oxygen_baseline=6.5,
        pollution_probability=0.12,
        pollution_type="both",
        description="Aval immédiat Tour Eiffel",
    ),
    SensorProfile(
        sensor_id="SEINE-BILLANCOURT-010",
        name="Boulogne-Billancourt",
        latitude=48.8412,
        longitude=2.2528,
        ph_baseline=7.0,
        turbidity_baseline=30.0,
        temperature_baseline=20.8,
        oxygen_baseline=6.3,
        pollution_probability=0.15,
        pollution_type="both",
        description="Aval - rejets industriels",
    ),
    SensorProfile(
        sensor_id="SEINE-SURESNES-011",
        name="Suresnes",
        latitude=48.8714,
        longitude=2.2286,
        ph_baseline=6.9,
        turbidity_baseline=32.0,
        temperature_baseline=21.0,
        oxygen_baseline=6.0,
        pollution_probability=0.18,
        pollution_type="both",
        description="Boucle de Gennevilliers",
    ),
    SensorProfile(
        sensor_id="SEINE-COLOMBES-012",
        name="Colombes",
        latitude=48.9135,
        longitude=2.2546,
        ph_baseline=6.8,
        turbidity_baseline=35.0,
        temperature_baseline=21.2,
        oxygen_baseline=5.8,
        pollution_probability=0.20,
        description="Rejets STEP + industries",
    ),
]


def get_sensor(sensor_id: str) -> SensorProfile:
    """Return the sensor profile for the given ID, or raise KeyError."""
    for sensor in SENSORS:
        if sensor.sensor_id == sensor_id:
            return sensor
    raise KeyError(f"Unknown sensor: {sensor_id}")