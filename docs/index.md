# UrbanHub

Bienvenue dans la documentation de **UrbanHub**, la plateforme Smart City de surveillance de la qualité de l'eau.

## Qu'est-ce qu'UrbanHub ?

UrbanHub est une preuve de concept d'une plateforme urbaine événementielle qui :

- ingère des données **réelles** (API Hub'Eau) et des données **simulées** ;
- détecte les anomalies par une **machine à états** (`NORMAL` → `WARNING` → `CRITICAL`) ;
- persiste les séries temporelles dans **TimescaleDB** ;
- pousse les transitions d'état en temps réel via **WebSocket** vers un tableau de bord React ;
- embarque une stack d'**observabilité** complète (Prometheus, Grafana, Loki).

## Par où commencer ?

- [Démarrage rapide](getting-started.md) — lancer la plateforme en local avec Docker Compose.
- [Architecture](architecture.md) — vue d'ensemble technique.
- [Services](services/index.md) — documentation de chaque micro-service.
- [Communication technique vs fonctionnelle](communication.md) — exemples de messages adaptés à chaque audience.
- [Changelog](changelog.md) — historique des versions.

## Structure de la documentation

| Section | Contenu |
|---|---|
| **Démarrage** | Prérequis, commandes Docker Compose, vérifications |
| **Architecture** | Flux de données, patterns, schéma de base de données |
| **Services** | Documentation détaillée de `alert-service`, `iot-service`, `dashboard`, `monitoring` |
| **Communication** | Guide et exemples de communication métier vs technique |
| **Changelog** | Versions et évolutions du projet |

## Contribution

La documentation est générée automatiquement avec [MkDocs Material](https://squidfunk.github.io/mkdocs-material/). Les pages de services reprennent directement les `README.md` de chaque service pour éviter la duplication d'information.
