# Journal des Versions (Changelog)

Le journal des modifications s'appuie sur la convention internationale **Conventional Commits** (`feat:`, `fix:`, `ci:`, `docs:`, `refactor:`).

Toutes les dates sont au format ISO 8601 (AAAA-MM-JJ).

---

## [0.4.0] — 2026-07-02

### Added
- Restauration de l'etat de la machine a etats au demarrage depuis la base PostgreSQL (`state_transitions`).
- Architecture Domain-Driven Design (DDD) avec `SensorStreamProcessor` comme Aggregate Root.

### Changed
- Suppression des anciens endpoints synchrone HTTP pour renforcer l'architecture evenementielle asynchrone via Kafka.

---

## [0.3.0] — 2026-07-01

### Added
- Integration de l'API reelle Hub'Eau (`qualite_rivieres`) pour 6 stations de la Seine (`SEINE-VITRY-001` a `SEINE-COLOMBES-012`).
- Poller automatique avec frequence d'interrogation fixee a 6 heures (`QUALITY_POLL_INTERVAL_SECONDS=21600`).

---

## [0.2.0] — 2026-06-15

### Added
- Panneau d'analyse detaille (drawer) par capteur sur le tableau de bord React SPA.
- Endpoints REST de consultation de metriques historiques et d'alertes.

---

## [0.1.1] — 2026-05-20

### Added
- Initialisation du microservice `iot-service` avec Gateway FastAPI, simulateur de capteurs virtuels et publication Kafka.
- Pipeline CI/CD 6 etapes bloquantes avec scans DevSecOps (Gitleaks, Bandit, Trivy, CycloneDX).

---

## [0.1.0] — 2026-05-01

### Added
- Scaffold initial du monorepo UrbanHub (Docker Compose, Kafka KRaft, PostgreSQL/TimescaleDB).
- Premiere version du microservice `alert-service` avec machine a etats et WebSocket.
