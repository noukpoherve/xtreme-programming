"""
Client for the official French water-quality API (Hub'Eau v2 — qualite_rivieres).

This module is an **Adapter** that translates the Hub'Eau JSON schema into
UrbanHub's domain model (SensorMeasurement). It is the *real-data* counterpart
of `HubEauSensorClient` which only handles hydrometry (level + flow).

Hub'Eau documentation:
    https://hubeau.eaufrance.fr/page/api-qualite-cours-deau

Open access — no authentication required. CORS-enabled.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────
# Hub'Eau parameter codes (Sandre référential)
# ──────────────────────────────────────────────────────────────────────
PARAM_PH = "1302"  # Potentiel en Hydrogène
PARAM_TEMP = "1301"  # Température de l'eau
PARAM_OXYGEN = "1311"  # Oxygène dissous
PARAM_COD = "1314"  # Demande Chimique en Oxygène (pollution organique)
PARAM_AMMONIUM = "1335"  # Ammonium

ALL_QUALITY_PARAMS = [PARAM_PH, PARAM_TEMP, PARAM_OXYGEN, PARAM_COD, PARAM_AMMONIUM]

_BASE_URL = "https://hubeau.eaufrance.fr/api/v2/qualite_rivieres/analyse_pc"


@dataclass(frozen=True)
class HubEauAnalysis:
    """A single water-quality analysis from Hub'Eau."""

    station_code: str
    station_name: str
    parameter_code: str
    parameter_label: str
    value: float
    unit: str
    sampled_at: datetime
    latitude: float
    longitude: float


@dataclass
class LatestQualityMeasurement:
    """
    Latest quality snapshot for one station, combining all available parameters.

    Some fields may be None if Hub'Eau has no recent data for that parameter.
    """

    station_code: str
    station_name: str
    latitude: float
    longitude: float
    sampled_at: datetime | None = None
    ph: float | None = None
    temperature_c: float | None = None
    dissolved_oxygen_mgl: float | None = None
    cod_mgl: float | None = None  # Demande Chimique en Oxygène (pollution indicator)
    ammonium_mgl: float | None = None

    def is_complete(self) -> bool:
        """A measurement is usable for state-machine analysis only if it has pH + O₂."""
        return self.ph is not None and self.dissolved_oxygen_mgl is not None


# ──────────────────────────────────────────────────────────────────────
# Mapping helpers
# ──────────────────────────────────────────────────────────────────────
_PARAMETER_LABEL_TO_FIELD = {
    "Potentiel en Hydrogène (pH)": "ph",
    "Température de l'Eau": "temperature_c",
    "Oxygène dissous": "dissolved_oxygen_mgl",
    "Demande Chimique en Oxygène (DCO)": "cod_mgl",
    "Ammonium": "ammonium_mgl",
}


# ──────────────────────────────────────────────────────────────────────
# Adapter (SOLID: depends on urllib, no aiokafka)
# ──────────────────────────────────────────────────────────────────────
class HubEauQualiteClient:
    """
    Fetches the latest water-quality snapshot for a station.

    Strategy:
      1. For each known parameter (pH, O₂, …) call `analyse_pc` once.
      2. Sort by `date_prelevement DESC` and take the first row.
      3. Aggregate into a single `LatestQualityMeasurement`.

    The API does NOT provide a "latest per station" endpoint — we have to
    paginate per parameter. This is fine because we only poll once per
    few hours (lab analysis frequency).
    """

    def __init__(self, *, timeout_seconds: float = 15.0) -> None:
        self._timeout = timeout_seconds

    def get_latest(self, station_code: str) -> LatestQualityMeasurement | None:
        """
        Return the latest available snapshot for the given station, or None
        if no recent data could be retrieved.

        Implementation note: parameters are fetched in **parallel** via threads
        because Hub'Eau sometimes hangs on individual parameter queries
        (e.g. DCO for some stations). Parallelizing bounds the worst-case
        latency to ~timeout instead of N*timeout.
        """
        import concurrent.futures

        latest_by_param: dict[str, HubEauAnalysis] = {}
        station_meta: HubEauAnalysis | None = None

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(ALL_QUALITY_PARAMS)
        ) as pool:
            futures = {
                pool.submit(self._fetch_latest_analysis, station_code, param): param
                for param in ALL_QUALITY_PARAMS
            }
            for future in concurrent.futures.as_completed(
                futures, timeout=self._timeout + 5
            ):
                param = futures[future]
                try:
                    analysis = future.result(timeout=self._timeout)
                except Exception:
                    logger.warning(
                        "Hub'Eau fetch failed for station=%s param=%s (ignored)",
                        station_code,
                        param,
                    )
                    continue
                if analysis is None:
                    continue
                latest_by_param[param] = analysis
                if station_meta is None:
                    station_meta = analysis

        if station_meta is None:
            logger.warning(
                "No Hub'Eau quality data found for station=%s",
                station_code,
            )
            return None

        # Aggregate into the domain snapshot
        snapshot = LatestQualityMeasurement(
            station_code=station_meta.station_code,
            station_name=station_meta.station_name,
            latitude=station_meta.latitude,
            longitude=station_meta.longitude,
            sampled_at=max(
                (a.sampled_at for a in latest_by_param.values()),
                default=station_meta.sampled_at,
            ),
        )

        # Map Hub'Eau values into our fields by parameter LABEL
        for analysis in latest_by_param.values():
            field_name = _PARAMETER_LABEL_TO_FIELD.get(analysis.parameter_label)
            if field_name is None:
                continue
            setattr(snapshot, field_name, analysis.value)

        return snapshot if snapshot.is_complete() else snapshot

    # ────────────────────────────────────────────────
    # Private — single HTTP call per parameter
    # ────────────────────────────────────────────────
    def _fetch_latest_analysis(
        self, station_code: str, parameter_code: str
    ) -> HubEauAnalysis | None:
        """
        Fetch the most recent analysis for (station, parameter).
        Hub'Eau returns analyses sorted ASC by date; we ask size=20 and
        sort client-side to handle any historical ordering quirks.
        """
        url = (
            f"{_BASE_URL}"
            f"?code_station={station_code}"
            f"&code_parametre={parameter_code}"
            f"&size=20"
            f"&sort=desc"
        )

        try:
            with urllib.request.urlopen(url, timeout=self._timeout) as resp:
                payload = json.loads(resp.read())
        except TimeoutError:
            logger.warning(
                "Hub'Eau quality fetch timed out (%.1fs) station=%s param=%s",
                self._timeout,
                station_code,
                parameter_code,
            )
            return None
        except urllib.error.URLError as e:
            logger.warning(
                "Hub'Eau quality connection error station=%s param=%s: %s",
                station_code,
                parameter_code,
                str(e),
            )
            return None
        except (json.JSONDecodeError, KeyError):
            logger.exception(
                "Hub'Eau quality payload parsing failed station=%s param=%s",
                station_code,
                parameter_code,
            )
            return None

        rows = payload.get("data", [])
        if not rows:
            return None

        # Sort DESC by date_prelevement (just in case the API didn't honor sort)
        rows.sort(
            key=lambda r: r.get("date_prelevement") or "",
            reverse=True,
        )
        first = rows[0]

        try:
            sampled_at = datetime.fromisoformat(first["date_prelevement"])
        except (KeyError, ValueError):
            sampled_at = datetime.utcnow()

        try:
            return HubEauAnalysis(
                station_code=first["code_station"],
                station_name=first.get("libelle_station", ""),
                parameter_code=str(first["code_parametre"]),
                parameter_label=first.get("libelle_parametre", ""),
                value=float(first["resultat"]),
                unit=first.get("symbole_unite", ""),
                sampled_at=sampled_at,
                latitude=float(first.get("latitude", 0.0)),
                longitude=float(first.get("longitude", 0.0)),
            )
        except (KeyError, ValueError, TypeError):
            logger.exception(
                "Malformed Hub'Eau row for station=%s param=%s: %s",
                station_code,
                parameter_code,
                first,
            )
            return None
