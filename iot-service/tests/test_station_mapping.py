"""Tests for the Hub'Eau ↔ UrbanHub station mapping."""

from __future__ import annotations

from iot_service.station_mapping import (
    STATION_MAPPING,
    get_sensor_ids,
    get_station_for_sensor,
)


class TestStationMapping:
    def test_at_least_5_mappings(self):
        """We should have at least 5 real Hub'Eau stations."""
        assert len(STATION_MAPPING) >= 5

    def test_all_mappings_have_unique_sensor_ids(self):
        sensor_ids = [m.sensor_id for m in STATION_MAPPING]
        assert len(sensor_ids) == len(set(sensor_ids))

    def test_all_mappings_have_unique_station_codes(self):
        codes = [m.station_code for m in STATION_MAPPING]
        assert len(codes) == len(set(codes))

    def test_station_codes_are_8_chars_numeric(self):
        """Hub'Eau codes are 8-character strings like '03081000'."""
        for m in STATION_MAPPING:
            assert len(m.station_code) == 8
            assert m.station_code.isdigit()

    def test_sensor_ids_have_seine_prefix(self):
        """UrbanHub sensor IDs follow the SEINE-XXX-NNN pattern."""
        for m in STATION_MAPPING:
            assert m.sensor_id.startswith("SEINE-"), m.sensor_id

    def test_get_station_for_sensor_known(self):
        m = STATION_MAPPING[0]
        result = get_station_for_sensor(m.sensor_id)
        assert result is not None
        assert result.station_code == m.station_code

    def test_get_station_for_sensor_unknown(self):
        result = get_station_for_sensor("SEINE-FAUX-999")
        assert result is None

    def test_get_sensor_ids_returns_set(self):
        ids = get_sensor_ids()
        assert isinstance(ids, set)
        assert len(ids) == len(STATION_MAPPING)

    def test_no_duplicate_sensor_ids_in_set(self):
        ids = get_sensor_ids()
        assert len(ids) == len(STATION_MAPPING)
