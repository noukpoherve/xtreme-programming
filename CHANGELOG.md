# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-07-02

### Added

- Restauration de l'état de la machine à états au démarrage (`restore_states_from_db` dans `AlertService`) depuis la table `state_transitions` dans PostgreSQL. Empêche la perte d'état et d'historique des anomalies après un redémarrage du conteneur.
- Création du module `domain.py` regroupant `SensorStreamProcessor` (Aggregate Root) et `SensorProcessorRegistry`, appliquant les concepts du Domain-Driven Design (DDD).
- Test d'intégration complet pour vérifier la reprise d'état depuis la base de données.

### Changed

- Simplification de la couche application `service.py` (contenant `AlertService`) désormais découplée de la logique pure du domaine.

### Removed

- Client d'hydrométrie hérité (`HubEauSensorClient`) et tâche de fond associée (station `F700000103`).
- Endpoints synchrone HTTP `POST /alertes` et `POST /measurements` dans `alert-service`, renforçant l'architecture événementielle asynchrone via Kafka.
- Endpoints HTTP `POST /simulate` et `POST /quality/ingest` dans `iot-service`, isolant le service comme pur producteur Kafka avec uniquement `GET /health` actif.

### Fixed

- Correction des erreurs d'importation de `alert_service.repository` en `alert_service.repositories`.

### Added

- CI job that exports and validates the alert-service OpenAPI contract.
- Automated GitHub Release generation with release notes on `master` pushes.

### Changed

- Merged the legacy `sensor-simulator` service into `iot-service` to simplify operations and share the same Kafka producer/domain model.

### Deprecated

- Legacy hydrometry polling endpoints in `iot-service`; will be removed once water-quality coverage is complete.

### Removed

- Standalone `sensor-simulator` service and container.

### Fixed

- WebSocket path collision: endpoint moved from `/ws` to `/stream` to avoid matching `GET /sensors/{sensor_id}`.
- State machine survives restarts: `list_sensors()` now reads the latest state from `state_transitions` via a LATERAL JOIN instead of relying on the in-memory registry.

### Security

- Added Bandit SAST, pip-audit SCA, gitleaks secret detection and Trivy image scanning to the CI pipeline.

## [0.3.0] - 2026-07-01

### Added

- Real Hub'Eau integration for 6 water-quality stations along the Seine (`SEINE-VITRY-001`, `SEINE-CHARENTON-002`, `SEINE-BERCY-003`, `SEINE-AUSTERLITZ-004`, `SEINE-CONCORDE-006`, `SEINE-COLOMBES-012`).
- `HubEauQualiteClient` adapter fetching 5 parameters (pH, temperature, dissolved O₂, DCO, ammonium) in parallel with bounded timeout.
- New manual trigger endpoint `POST /quality/ingest` on `iot-service`.
- Data-source badge on dashboard markers and drawer (🌐 Hub'Eau / 🎲 Simulé).

### Changed

- Increased Hub'Eau polling interval to 6 hours (`QUALITY_POLL_INTERVAL_SECONDS=21600`) to respect lab-analysis cadence and avoid API quota waste.
- Simulator now excludes all Hub'Eau-mapped sensor IDs via `SIMULATOR_EXCLUDE_SENSORS`.

### Fixed

- Duplicate sensor sources: each sensor now has exactly one source of truth.

## [0.2.0] - 2026-06-15

### Added

- Per-sensor drill-down drawer in the dashboard with:
  - sensor metadata (location, firmware, data source, last measurement),
  - 24-hour time-series chart (pH, temperature, dissolved O₂),
  - last 20 measurements table,
  - last 10 alerts for the sensor.
- Three new REST endpoints on `alert-service`:
  - `GET /sensors/{id}/metadata`
  - `GET /sensors/{id}/measurements`
  - `GET /sensors/{id}/alerts`
- `MeasurementSeriesResponse` and `SensorMetadataView` Pydantic models.
- TimescaleDB continuous aggregates `measurements_hourly` and `measurements_daily`.
- `current_sensor_state` database view for fast latest-state lookups.

### Changed

- Dashboard layout switched to a dashboard-first design: KPI strip, map + right rail, sensor table.
- WebSocket reconnection logic with exponential backoff capped at 30 seconds.

### Fixed

- Drawer not updating when a state transition occurred while it was open.
- Mobile layout: drawer becomes a bottom sheet on screens < 1024 px.

## [0.1.0] - 2026-05-20

### Added

- Initial event-driven UrbanHub platform:
  - `iot-service` producing `WaterMeasurementEvent` messages to Kafka.
  - Local sensor simulator with diurnal cycle, random walk and pollution events for 6 virtual sensors.
  - `alert-service` consuming measurements, running per-sensor state machine (NORMAL → WARNING → CRITICAL).
  - WebSocket broadcast of state transitions to the dashboard.
  - PostgreSQL + TimescaleDB persistence with hypertable `measurements` and 90-day retention.
- React 19 + Vite + Tailwind dashboard with Leaflet map and real-time updates.
- Docker Compose stack: Kafka 3.7 KRaft, PostgreSQL 16 + TimescaleDB, Prometheus, Grafana, Loki, Promtail.
- GitHub Actions CI: lint, test, security scan, Docker build and OpenAPI export.
- Pre-commit hooks: black, ruff, YAML/TOML lint, trailing-whitespace, secret detection.
- Standardized error envelope with `trace_id` propagated end-to-end.

[Unreleased]: https://github.com/said/urbanhub/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/said/urbanhub/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/said/urbanhub/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/said/urbanhub/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/said/urbanhub/releases/tag/v0.1.0
