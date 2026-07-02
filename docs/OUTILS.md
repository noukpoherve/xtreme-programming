# Stack outillage — UrbanHub

| Outil | Rôle | Où le voir dans le projet |
|-------|------|---------------------------|
| **Docker** | Conteneurisation des services | `docker-compose.yml`, `*/Dockerfile` |
| **FastAPI / Swagger** | API REST + doc auto OpenAPI | `/docs` sur chaque service (8000, 8001, 8002) |
| **pytest** | Tests unitaires et API | `*/tests/`, CI GitHub Actions |
| **unittest.mock** | Mocks et stubs (équivalent pymock) | `iot-service/tests/test_hubeau_client.py`, `alert-service/tests/test_service.py` |
| **uv** | Gestion des dépendances Python (équivalent Poetry) | `uv.lock`, `pyproject.toml`, CI `setup-uv` |
| **black** | Formatage du code | `pyproject.toml`, `.pre-commit-config.yaml`, CI |
| **pre-commit** | Hooks qualité avant commit | `.pre-commit-config.yaml` |
| **Kafka** | Message bus événementiel | `docker-compose.yml`, producers/consumers dans chaque service |
| **Redis** | Persistance alertes et capteurs | `docker-compose.yml`, repositories |
| **Prometheus / Grafana / Loki** | Observabilité | `monitoring/` |
| **GitHub Actions** | CI/CD (tests, build Docker, releases) | `.github/workflows/ci.yml` |
| **Postman** | Tests manuels API | `docs/postman/UrbanHub.postman_collection.json` |
| **Pydantic** | Contrats API typés | `contracts.py`, `sensor_contracts.py`, `contrats.py` |

## Notes

- **Poetry** : non utilisé ; **uv** remplit le même rôle (lockfile, sync, CI).
- **pymock** : non utilisé ; la stdlib **unittest.mock** est utilisée (même objectif).
- **ruff** : non intégré ; le lint/format repose sur **black** + revue manuelle. Ajout possible en CI si requis.
- **DataAxe** : non présent dans ce dépôt (outil externe non requis pour l'exécution locale).

## Commandes utiles

```bash
# Tests alert + iot
cd alert-service && uv run pytest tests/ -v
cd iot-service && uv run pytest tests/ -v

# Tests supervision
cd supervision-service
set PYTHONPATH=src
set DISABLE_KAFKA_CONSUMER=1
pytest tests/ -v

# Stack complète
docker compose up -d
```
