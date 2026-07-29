# Extraits de code — `iot-service`

Copies pour le rendu EC03. Source canonique : `iot-service/` à la racine du monorepo UrbanHub.

| Dossier | Fichier | Rôle |
|---------|---------|------|
| `domain/` | `station_mapping.py` | Mapping Hub'Eau ↔ capteurs UrbanHub |
| `domain/` | `config.py` | Configuration (env, pas de secrets en dur) |
| `api/` | `main.py` | FastAPI : lifespan, `/health`, gateway HTTP |
| `tests/` | `test_station_mapping.py` | Tests unitaires domaine |
| `tests/` | `test_api_gateway.py` | Tests unitaires API (mock Kafka) |

Ces extraits ne sont **pas** exécutables seuls : ils documentent le périmètre industrialisé par le pipeline.
