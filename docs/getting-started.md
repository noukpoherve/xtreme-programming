# Démarrage rapide

Ce guide explique comment lancer UrbanHub en local.

## Prérequis

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose v2](https://docs.docker.com/compose/install/)
- (Optionnel, pour le développement) Python 3.13+, Node 20+, [`uv`](https://docs.astral.sh/uv/)

## Lancer la stack complète

```bash
git clone https://github.com/chrfsa/xtreme-programming.git
cd xtreme-programming
docker compose up --build -d
```

Attendez environ 60 secondes que tous les services démarrent.

## Vérifier le bon fonctionnement

| URL | Service |
|---|---|
| <http://localhost:5173> | Tableau de bord UrbanHub |
| <http://localhost:8000/docs> | Swagger UI — `alert-service` |
| <http://localhost:8001/docs> | Swagger UI — `iot-service` |
| <http://localhost:8080> | Kafka UI |
| <http://localhost:3000> | Grafana (admin / admin) |

### Commandes de test rapide

```bash
# Vérifier les statistiques globales
curl http://localhost:5173/api/stats

# Forcer une ingestion Hub'Eau manuelle
curl -X POST http://localhost:8001/quality/ingest

# Envoyer une mesure CRITICAL de test
curl -X POST http://localhost:8000/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "mesure.qualite.eau",
    "event_id": "demo-1", "trace_id": "demo-trace",
    "capteur_id": "SEINE-COLOMBES-012",
    "timestamp": "2026-07-01T10:00:00Z",
    "localisation": {"latitude": 48.91, "longitude": 2.25, "point_reference": "Demo"},
    "mesures": {"ph": 4.0, "turbidite_ntu": 60.0, "temperature_c": 20.0,
                "niveau_m": 1.0, "debit_m3s": 250.0, "oxygene_dissous_mgl": 5.0},
    "qualite_signal": "GOOD", "firmware_version": "2.4.1", "data_source": "simulated"
  }'
```

## Documentation en local

Pour servir ce site de documentation sur votre machine avec [`uv`](https://docs.astral.sh/uv/) :

```bash
uv sync --group docs
uv run --group docs mkdocs serve
```

Puis ouvrir <http://127.0.0.1:8000>.

### Valider les doctests MkDocs

Les exemples `>>>` dans `docs/api/*.md` sont exécutés comme des tests :

```bash
uv sync --group docs --group docs-test
uv run --group docs-test pytest docs/api -v
uv run --group docs mkdocs build --strict
```

## Documentation publiée (GitHub Pages + mike)

La doc est déployée automatiquement sur GitHub Pages à chaque push sur `master` :

**<https://noukpoherve.github.io/xtreme-programming/>**

[mike](https://github.com/jimporter/mike) gère le versionnement : chaque version est publiée dans un sous-dossier (`/0.1.0/`, `/latest/`, etc.) avec un sélecteur de version dans le thème Material.

### Déployer manuellement en local

```bash
uv sync --group docs
uv run --group docs mike deploy --push --update-aliases 0.1.0 latest
uv run --group docs mike set-default --push latest
```

### Prérequis GitHub (une seule fois)

Dans **Settings → Pages** du dépôt :

- **Source** : `Deploy from a branch`
- **Branch** : `gh-pages` / `/ (root)`

## Arrêter la plateforme

```bash
docker compose down
```

Pour supprimer également les volumes (base de données, Kafka, etc.) :

```bash
docker compose down -v
```
