#!/usr/bin/env python3
"""
Export OpenAPI specifications from every UrbanHub service.

Usage:
    # From running services (docker compose up):
    python scripts/export_openapi.py

    # From a running service URL only:
    python scripts/export_openapi.py --service alert-service

    # From a FastAPI app object (no running server needed):
    python scripts/export_openapi.py --in-process

Output:
    api-specs/<service>-<version>.json — versioned, Git-trackable specs.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Resolve project root regardless of where the script is invoked from
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SPECS_DIR = PROJECT_ROOT / "api-specs"


SERVICES = {
    "alert-service": "http://localhost:8000",
    "iot-service": "http://localhost:8001",
}


def fetch_spec_from_url(base_url: str) -> dict:
    """Fetch /openapi.json from a running service."""
    url = f"{base_url.rstrip('/')}/openapi.json"
    print(f"  → GET {url}")
    response = httpx.get(url, timeout=10.0)
    response.raise_for_status()
    return response.json()


def fetch_spec_from_app(service_name: str) -> dict:
    """
    Import the FastAPI app directly and call app.openapi().

    Useful in CI when no service is running. Requires the package and
    all of its dependencies to be importable.
    """
    if service_name == "alert-service":
        from alert_service.main import app  # type: ignore[import-not-found]

        return app.openapi()
    if service_name == "iot-service":
        from iot_service.main import app  # type: ignore[import-not-found]

        return app.openapi()
    raise ValueError(f"Unknown service: {service_name}")


def write_spec(service_name: str, spec: dict) -> Path:
    """Write the spec to api-specs/<service>-<version>.json."""
    version = spec.get("info", {}).get("version", "unknown")
    # Strip non-filesystem-safe chars (though versions usually don't have any)
    safe_version = version.replace("/", "_")
    out_path = SPECS_DIR / f"{service_name}-{safe_version}.json"

    # Inject export metadata so consumers know when/where the spec came from
    spec.setdefault("info", {})
    spec["info"]["x-exported-at"] = datetime.now(timezone.utc).isoformat()
    spec["info"]["x-exported-from"] = service_name

    SPECS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")
    print(f"  ✓ written {out_path.relative_to(PROJECT_ROOT)}")
    return out_path


def export_all(*, in_process: bool, only: str | None) -> list[Path]:
    """Export OpenAPI specs for every service (or a single one)."""
    written: list[Path] = []
    targets = (
        {only: SERVICES[only]} if only and only in SERVICES else SERVICES
    )

    for name, url in targets.items():
        print(f"[{name}]")
        try:
            if in_process:
                spec = fetch_spec_from_app(name)
            else:
                spec = fetch_spec_from_url(url)
        except Exception as exc:
            print(f"  ✗ failed: {exc}", file=sys.stderr)
            continue
        written.append(write_spec(name, spec))

    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--service",
        choices=list(SERVICES.keys()),
        help="Export only this service.",
    )
    parser.add_argument(
        "--in-process",
        action="store_true",
        help="Import the FastAPI app directly instead of HTTP fetching.",
    )
    args = parser.parse_args()

    print(f"Exporting OpenAPI specs to {SPECS_DIR.relative_to(PROJECT_ROOT)}/")
    written = export_all(in_process=args.in_process, only=args.service)

    if not written:
        print("No specs exported.", file=sys.stderr)
        return 1

    print(f"\nDone — {len(written)} spec(s) exported.")
    return 0


if __name__ == "__main__":
    sys.exit(main())