"""
Mapping between Hub'Eau official station codes and UrbanHub sensor IDs.

We use 6 real Seine stations from the Agence de l'Eau Seine-Normandie.
The remaining 6 sensors in the UrbanHub catalog are simulated locally.

Source: https://hubeau.eaufrance.fr/api/v2/qualite_rivieres/station_pc
        ?code_commune=75056,92012,92025
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StationMapping:
    """Binds a Hub'Eau station to an UrbanHub sensor_id."""

    station_code: str  # Hub'Eau code, e.g. "03081000"
    station_name: str  # Human label
    sensor_id: str  # UrbanHub sensor_id, e.g. "SEINE-BERCY-003"
    sensor_name: str  # Display label on the dashboard
    latitude: float = 0.0
    longitude: float = 0.0


# 6 official Hub'Eau stations, mapped to nearby UrbanHub sensor_ids.
# Coordinates are taken from the Hub'Eau response.
STATION_MAPPING: tuple[StationMapping, ...] = (
    StationMapping(
        station_code="03112328",
        station_name="BONNEUIL-SUR-MARNE 8",
        sensor_id="SEINE-CHARENTON-002",
        sensor_name="Charenton-le-Pont (Hub'Eau)",
        latitude=48.8207,
        longitude=2.4151,
    ),
    StationMapping(
        station_code="03081000",
        station_name="LA SEINE A PARIS-12E",
        sensor_id="SEINE-BERCY-003",
        sensor_name="Bercy (Hub'Eau)",
        latitude=48.8359,
        longitude=2.3823,
    ),
    StationMapping(
        station_code="03081270",
        station_name="LA SEINE A PARIS-7E",
        sensor_id="SEINE-AUSTERLITZ-004",
        sensor_name="Pont d'Austerlitz (Hub'Eau)",
        latitude=48.8447,
        longitude=2.3655,
    ),
    StationMapping(
        station_code="03081570",
        station_name="LA SEINE A PARIS-16E",
        sensor_id="SEINE-CONCORDE-006",
        sensor_name="Pont de la Concorde (Hub'Eau)",
        latitude=48.8637,
        longitude=2.3017,
    ),
    StationMapping(
        station_code="03083450",
        station_name="LA SEINE A COLOMBES 2",
        sensor_id="SEINE-COLOMBES-012",
        sensor_name="Colombes (Hub'Eau)",
        latitude=48.9135,
        longitude=2.2546,
    ),
    StationMapping(
        station_code="03112331",
        station_name="BONNEUIL-SUR-MARNE 9",
        sensor_id="SEINE-VITRY-001",
        sensor_name="Vitry-sur-Seine (Hub'Eau)",
        latitude=48.7876,
        longitude=2.3926,
    ),
)

# O(1) lookup tables derived from the canonical mapping.
_SENSOR_ID_TO_STATION: dict[str, StationMapping] = {
    m.sensor_id: m for m in STATION_MAPPING
}
_STATION_CODE_TO_STATION: dict[str, StationMapping] = {
    m.station_code: m for m in STATION_MAPPING
}


def get_station_for_sensor(sensor_id: str) -> StationMapping | None:
    """Return the Hub'Eau station mapped to this UrbanHub sensor_id, or None."""
    return _SENSOR_ID_TO_STATION.get(sensor_id)


def get_station_for_code(station_code: str) -> StationMapping | None:
    """Return the station mapping for a Hub'Eau station code, or None."""
    return _STATION_CODE_TO_STATION.get(station_code)


def get_sensor_ids() -> set[str]:
    """Return the set of UrbanHub sensor_ids that have a real Hub'Eau station."""
    return set(_SENSOR_ID_TO_STATION.keys())
