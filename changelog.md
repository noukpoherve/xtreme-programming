# Changelog

Toutes les modifications notables de ce projet sont documentees dans ce fichier.

Le format s'inspire de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et applique le versioning semantique.

## [0.1.2] - 2026-07-01

### Added
- Nouveau `supervision-service` pour la supervision IRVE en temps reel.
- Endpoints supervision pour bornes, sessions, incidents et dashboard (`/bornes`, `/sessions`, `/incidents`, `/tableau-de-bord/*`).
- Endpoint WebSocket `/ws/supervision/direct` pour pousser les mises a jour temps reel.

### Changed
- Reorganisation de la logique WebSocket dans `supervision-service/src/supervision_service/api.py`.
- Enrichissement de la reponse de `/tableau-de-bord/carte` (sante borne, connecteurs, sessions actives).
- Documentation de projet et changelog harmonises pour refleter l'etat reel du monorepo.

### Fixed
- Gestion d'erreurs et de logs amelioree autour des connexions WebSocket.
- Standardisation des erreurs 404/405 sur les APIs (middleware commun).

## [0.1.1] - 2026-05-07

### Added
- Pipeline evenementiel Kafka entre `iot-service` et `alert-service`.
- Endpoints de simulation et ingestion de mesures dans `iot-service` (`/simulate`, `/ingest`).
- Publication et consommation des evenements metier (`mesure.qualite.eau`, `alerte.pollution.detectee`).
- Environnement d'observabilite complet en local (Prometheus, Grafana, Loki, Promtail).
- Endpoints CRUD stabilises pour capteurs et alertes (`/sensors`, `/alerts`) avec aliases legacy FR.

### Changed
- Renforcement de la resilience des flux Kafka (retry/backoff, robustesse du consumer/producer).
- Ajustements Docker et healthchecks pour un demarrage local plus fiable.
- Evolution de la CI (tests matrix, build check, tagging et releases automatisees).

### Fixed
- Corrections CI sur les chemins pytest/black et validation du pipeline.
- Nettoyage de code mort et coherence workspace pour eviter les regressions.

## [0.1.0] - 2026-05-06

### Added
- Initialisation du projet UrbanHub avec architecture microservices.
- Creation de `alert-service` (FastAPI) avec endpoint initial de creation d'alertes.
- Base des regles metier sur la qualite de l'eau (pH, turbidite) et premiers tests.
- Mise en place initiale de l'outillage CI/CD.
- Documentation de cadrage et structure de travail XP.
