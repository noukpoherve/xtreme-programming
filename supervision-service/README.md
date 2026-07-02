# Service de Supervision IRVE

> Supervision temps réel des bornes de recharge électriques — UrbanHub IRVE

Documentation complète : voir [README_FR.md](README_FR.md)

## Démarrage rapide

```bash
cd supervision-service
pip install -r requirements.txt
set PYTHONPATH=src
python -m uvicorn supervision_service.main:app --reload --port 8002
```

Swagger : http://localhost:8002/docs

## Endpoints principaux

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/bornes` | Liste des bornes |
| GET | `/sessions` | Sessions de charge |
| GET | `/tableau-de-bord/resume` | Résumé dashboard |
| GET | `/tableau-de-bord/carte` | Données carte |
| GET | `/incidents` | Incidents récents |
| GET | `/sante` | Healthcheck |
| WS | `/ws/supervision/direct` | Mises à jour temps réel |

## Tests

```bash
set PYTHONPATH=src
set DISABLE_KAFKA_CONSUMER=1
pytest tests/ -v
```

## Kafka

- Topic consommé : `charge.station.events`
- Variable : `KAFKA_BOOTSTRAP_SERVERS` (défaut `localhost:9092`)
- Désactiver le consumer en tests : `DISABLE_KAFKA_CONSUMER=1`
