# Changelog — UrbanHub

Toutes les modifications notables du projet sont documentées dans ce fichier.

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et du [versionnement sémantique](https://semver.org/lang/fr/).

---

## Comment lire ce document

| Section | Public visé | Contenu |
|---------|-------------|---------|
| **Synthèse dirigeants** | équipes de direction, encadrement, jury | impacts métier, valeur livrée, risques réduits |
| **Détail technique** | développeurs, ops, architectes | changements précis par version |

---

## Synthèse dirigeants (vue d'ensemble)

### Version 0.5.0 — Juillet 2026 *(en cours)*

**En une phrase :** la plateforme dispose désormais de routes d'ingestion documentées et pilotables, prêtes pour démonstration et intégration partenaires.

| Thème | Impact pour la direction |
|-------|--------------------------|
| Ingestion maîtrisée | déclenchement manuel Hub'Eau / simulation / capteurs physiques, sans attendre les cycles automatiques |
| Documentation API | Swagger et contrats lisibles pour valider les échanges avec des tiers |
| Traçabilité | chaque livraison reste reliée à l'historique Git et au changelog |

### Version 0.4.0 — 2 juillet 2026

**En une phrase :** UrbanHub passe d'un prototype technique à une plateforme opérationnelle supervisable en conditions réelles.

| Thème | Impact pour la direction |
|-------|--------------------------|
| Fiabilité | reprise automatique de l'état des capteurs après redémarrage (plus de perte d'historique) |
| Supervision | tableau de bord temps réel (carte, alertes, indicateurs) |
| Données réelles | connexion à 6 stations Hub'Eau officielles sur la Seine |
| Sécurité & qualité | scans automatiques (vulnérabilités, secrets, images Docker) à chaque livraison |
| Documentation | site MkDocs publiable sur GitHub Pages pour le pilotage projet |

### Version 0.3.0 — 1 juillet 2026

**En une phrase :** les données officielles Hub'Eau alimentent la plateforme avec une fréquence adaptée au terrain.

| Thème | Impact pour la direction |
|-------|--------------------------|
| Source de vérité | chaque capteur a une seule source (réelle ou simulée), sans doublon |
| Données publiques | intégration Hub'Eau (pH, température, oxygène, etc.) |
| Pilotage visuel | distinction claire sur le dashboard entre données réelles et simulées |

### Version 0.2.0 — 15 juin 2026

**En une phrase :** les opérateurs peuvent analyser chaque capteur en profondeur depuis le dashboard.

| Thème | Impact pour la direction |
|-------|--------------------------|
| Analyse fine | historique 24h, mesures récentes, alertes par capteur |
| Décision | vue consolidée pour prioriser les interventions |

### Version 0.1.0 — 20 mai 2026

**En une phrase :** mise en service de la première version de la plateforme de surveillance de la qualité de l'eau.

| Thème | Impact pour la direction |
|-------|--------------------------|
| Architecture | microservices communicant par événements (Kafka) |
| Alertes automatiques | détection des anomalies pH / turbidité |
| Industrialisation | CI/CD, conteneurs Docker, observabilité de base |

---

## Détail technique par version

## [Unreleased]

### Synthèse dirigeants

- Routes d'ingestion explicites pour démonstrations, tests Postman et intégrations externes.
- Documentation Swagger enrichie sur le service IoT.

### Added

- `GET /ingestion/status` — état du pipeline (Kafka, Hub'Eau, simulateur).
- `POST /ingestion/hubeau` — déclenchement manuel d'un cycle Hub'Eau.
- `POST /ingestion/simuler` — déclenchement manuel d'un cycle simulateur.
- Schémas Pydantic `ingestion_schemas.py` pour la documentation OpenAPI.
- Tests `test_ingestion_routes.py` (4 scénarios).

### Changed

- `main.py` iot-service : tags Swagger `Health` / `Ingestion`, descriptions orientées exploitation.
- `mkdocs.yml` : URL dépôt corrigée (`noukpoherve/xtreme-programming`).

*Commits Git : `516247e` (2026-07-03)*

---

## [0.4.0] - 2026-07-03

### Synthèse dirigeants

Livraison majeure : dashboard opérationnel, ingestion multi-sources, alertes résilientes, documentation publiable et pipeline qualité renforcé.

### Added

- **Dashboard React** : carte capteurs, KPI, alertes temps réel, tiroir de détail par capteur.
- **IoT** : poller Hub'Eau qualité (6 stations), simulateur local (6 capteurs), passerelle HTTP capteurs physiques.
- **Alert-service** : domaine DDD (`domain.py`), reprise d'état PostgreSQL au redémarrage, gestionnaires d'erreurs robustes.
- **Infra** : stack Docker Compose unifiée, Loki/Promtail/Grafana, workspaces `uv`.
- **Documentation** : MkDocs Material, guides architecture (Mermaid), README par service.
- **CI** : export/validation OpenAPI, releases GitHub automatiques, couverture pytest, scan Trivy images.

### Changed

- Refactor `alert-service` selon principes DDD ; couche application allégée.
- Fusion simulateur dans `iot-service` (un seul producteur Kafka).
- Formatage codebase (`black`, `ruff`).

### Removed

- Client hydrométrie legacy `HubEauSensorClient` (station unique).
- Endpoints HTTP synchrones obsolètes (`POST /alertes`, `POST /simulate` legacy).
- Service `sensor-simulator` autonome.

### Fixed

- Imports `repository` → `repositories`.
- Collision WebSocket `/ws` → `/stream`.
- État capteurs lu depuis PostgreSQL (`state_transitions`) et non plus uniquement en mémoire.

### Security

- Bandit (SAST), pip-audit (SCA), gitleaks, Trivy en CI.

*Commits Git principaux : `6377154`, `906f542`, `5c671db`, `479bff9`, `d55e8b2`, `fe309dd`, `afb9383`, `74bf5e4`, `d396271`*

---

## [0.3.0] - 2026-07-01

### Synthèse dirigeants

Connexion aux données publiques Hub'Eau pour 6 stations ; cadence de collecte adaptée aux analyses laboratoire.

### Added

- Intégration Hub'Eau : 6 stations Seine (`SEINE-VITRY-001` … `SEINE-COLOMBES-012`).
- Client `HubEauQualiteClient` (5 paramètres en parallèle).
- Badge source de données sur le dashboard (réel / simulé).

### Changed

- Intervalle polling Hub'Eau : 6 heures.
- Simulateur exclut les capteurs déjà couverts par Hub'Eau.

### Fixed

- Suppression des doublons de source par capteur.

---

## [0.2.0] - 2026-06-15

### Synthèse dirigeants

Analyse détaillée par capteur pour les opérateurs (graphiques, historique, alertes).

### Added

- Tiroir drill-down dashboard (métadonnées, courbe 24h, tableau mesures, alertes).
- Endpoints `GET /sensors/{id}/metadata|measurements|alerts`.
- Agrégats TimescaleDB (`measurements_hourly`, `measurements_daily`).

### Changed

- Layout dashboard : KPI + carte + rail latéral.
- Reconnexion WebSocket avec backoff.

### Fixed

- Mise à jour du tiroir lors des transitions d'état.
- Layout mobile (bottom sheet).

---

## [0.1.0] - 2026-05-20

### Synthèse dirigeants

Première version exploitable : collecte, alertes automatiques, persistance et supervision.

### Added

- Plateforme événementielle : `iot-service` → Kafka → `alert-service`.
- Machine à états capteurs (NORMAL → WARNING → CRITICAL).
- Dashboard React + WebSocket temps réel.
- PostgreSQL/TimescaleDB, rétention 90 jours.
- Stack Docker : Kafka, Prometheus, Grafana, Loki.
- CI GitHub Actions + pre-commit (black, ruff).
- Enveloppe d'erreur standardisée avec `trace_id`.

*Commits Git : init microservices mai 2026 (`ea56d81`, `65e6cd4`, `5f32d9c`, …)*

---

[Unreleased]: https://github.com/noukpoherve/xtreme-programming/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/noukpoherve/xtreme-programming/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/noukpoherve/xtreme-programming/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/noukpoherve/xtreme-programming/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/noukpoherve/xtreme-programming/releases/tag/v0.1.0
