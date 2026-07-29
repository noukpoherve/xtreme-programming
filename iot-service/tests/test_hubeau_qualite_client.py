"""Tests for the Hub'Eau water-quality client.

Tests use urllib monkey-patching to avoid real HTTP calls.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from iot_service.hubeau_qualite_client import (
    PARAM_OXYGEN,
    PARAM_PH,
    PARAM_TEMP,
    HubEauQualiteClient,
    LatestQualityMeasurement,
)


def make_hubeau_response(
    parameter_code: str, value: float, date: str = "2025-06-15"
) -> dict:
    return {
        "count": 1,
        "data": [
            {
                "code_station": "03081000",
                "libelle_station": "LA SEINE A PARIS-12E",
                "code_parametre": parameter_code,
                "libelle_parametre": {
                    "1302": "Potentiel en Hydrogène (pH)",
                    "1301": "Température de l'Eau",
                    "1311": "Oxygène dissous",
                }[parameter_code],
                "resultat": value,
                "symbole_unite": "unité pH" if parameter_code == "1302" else "°C",
                "date_prelevement": date,
                "latitude": 48.83,
                "longitude": 2.38,
            }
        ],
    }


class TestHubEauQualiteClient:
    def test_get_latest_returns_none_on_no_data(self):
        client = HubEauQualiteClient()
        with patch("urllib.request.urlopen") as mock:
            mock.return_value.__enter__.return_value.read.return_value = json.dumps(
                {"count": 0, "data": []}
            ).encode()
            result = client.get_latest("03081000")
        assert result is None

    def test_get_latest_returns_partial_snapshot(self):
        """Even if only pH is available, we should get a snapshot with ph set."""
        client = HubEauQualiteClient()
        with patch("urllib.request.urlopen") as mock:
            mock.return_value.__enter__.return_value.read.side_effect = [
                json.dumps(make_hubeau_response(PARAM_PH, 8.2)).encode(),
                json.dumps({"count": 0, "data": []}).encode(),
                json.dumps({"count": 0, "data": []}).encode(),
                json.dumps({"count": 0, "data": []}).encode(),
                json.dumps({"count": 0, "data": []}).encode(),
            ]
            snapshot = client.get_latest("03081000")

        assert snapshot is not None
        assert snapshot.station_code == "03081000"
        assert snapshot.ph == 8.2
        assert snapshot.temperature_c is None
        assert snapshot.dissolved_oxygen_mgl is None

    def test_get_latest_aggregates_all_parameters(self):
        client = HubEauQualiteClient()
        with patch("urllib.request.urlopen") as mock:
            mock.return_value.__enter__.return_value.read.side_effect = [
                json.dumps(make_hubeau_response(PARAM_PH, 8.0)).encode(),
                json.dumps(make_hubeau_response(PARAM_TEMP, 18.5)).encode(),
                json.dumps(make_hubeau_response(PARAM_OXYGEN, 9.2)).encode(),
                json.dumps({"count": 0, "data": []}).encode(),
                json.dumps({"count": 0, "data": []}).encode(),
            ]
            snapshot = client.get_latest("03081000")

        assert snapshot is not None
        assert snapshot.ph == 8.0
        assert snapshot.temperature_c == 18.5
        assert snapshot.dissolved_oxygen_mgl == 9.2
        assert snapshot.is_complete()

    def test_get_latest_handles_http_error_gracefully(self):
        client = HubEauQualiteClient()
        with patch("urllib.request.urlopen") as mock:
            mock.side_effect = TimeoutError("hub'eau down")
            result = client.get_latest("03081000")
        assert result is None

    def test_get_latest_handles_malformed_json(self):
        client = HubEauQualiteClient()
        with patch("urllib.request.urlopen") as mock:
            mock.return_value.__enter__.return_value.read.return_value = b"not-json"
            result = client.get_latest("03081000")
        assert result is None


class TestLatestQualityMeasurement:
    def test_is_complete_requires_ph_and_oxygen(self):
        snap = LatestQualityMeasurement(
            station_code="X",
            station_name="Y",
            latitude=0,
            longitude=0,
            ph=7.0,
            temperature_c=15.0,
            dissolved_oxygen_mgl=8.0,
        )
        assert snap.is_complete()

        snap_missing_o2 = LatestQualityMeasurement(
            station_code="X",
            station_name="Y",
            latitude=0,
            longitude=0,
            ph=7.0,
            dissolved_oxygen_mgl=None,
        )
        assert not snap_missing_o2.is_complete()

        snap_missing_ph = LatestQualityMeasurement(
            station_code="X",
            station_name="Y",
            latitude=0,
            longitude=0,
            ph=None,
            dissolved_oxygen_mgl=8.0,
        )
        assert not snap_missing_ph.is_complete()
