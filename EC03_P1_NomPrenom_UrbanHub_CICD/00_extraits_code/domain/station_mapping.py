"""
Extrait EC03 — UrbanHub iot-service (domaine).
Source canonique : iot-service/src/iot_service/station_mapping.py
"""
# Copie conforme au dépôt source (mapping Hub'Eau).

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StationMapping:
    """Binds a Hub'Eau station to an UrbanHub sensor_id."""

    station_code: str
    station_name: str
    sensor_id: str
    sensor_name: str
    latitude: float = 0.0
    longitude: float = 0.0


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

_SENSOR_ID_TO_STATION: dict[str, StationMapping] = {
    m.sensor_id: m for m in STATION_MAPPING
}
_STATION_CODE_TO_STATION: dict[str, StationMapping] = {
    m.station_code: m for m in STATION_MAPPING
}


def get_station_for_sensor(sensor_id: str) -> StationMapping | None:
    return _SENSOR_ID_TO_STATION.get(sensor_id)


def get_station_for_code(station_code: str) -> StationMapping | None:
    return _STATION_CODE_TO_STATION.get(station_code)


def get_sensor_ids() -> set[str]:
    return set(_SENSOR_ID_TO_STATION.keys())
