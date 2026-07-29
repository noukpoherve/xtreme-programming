# Rapport de tests — EC03 · `iot-service`

> Exporter en PDF (`03_rapport_tests.pdf`) pour le ZIP final.
> **Anonymat** : aucun chemin absolu personnel ni identifiant individuel ne figure dans les logs ci-dessous.

## 1. Périmètre

- Microservice : **iot-service** (FastAPI)
- Outil : **pytest** + **pytest-cov**
- Emplacement des tests source : `iot-service/tests/`

## 2. Tests unitaires et d’intégration

| Fichier | Type | Description | Statut |
|---------|------|-------------|--------|
| `test_station_mapping.py` | Unitaire | Mapping Hub'Eau, unicité des capteurs et codes stations | PASSED (9/9) |
| `test_api_gateway.py` | Unitaire | Endpoint POST metrics, gestion des capteurs inconnus | PASSED (2/2) |
| `test_hubeau_qualite_client.py` | Unitaire | Client Hub'Eau (mock HTTP), tolérance aux pannes JSON/réseau | PASSED (6/6) |
| `test_non_functionnel.py` | Non-fonctionnel | SLA latence `/health` (p95) et rejet des valeurs aberrantes Pydantic | PASSED (3/3) |

```text
============================= test session starts =============================
platform linux -- Python 3.13.14, pytest-9.0.3, pluggy-1.6.0
rootdir: /workspace/iot-service
configfile: pyproject.toml
plugins: anyio-4.13.0, asyncio-1.3.0, cov-7.1.0
collected 20 items

tests/test_api_gateway.py .. [ 10%]
tests/test_hubeau_qualite_client.py ...... [ 40%]
tests/test_non_functionnel.py ... [ 55%]
tests/test_station_mapping.py ......... [100%]

============================== 20 passed in 1.13s ==============================
```

## 3. Test non fonctionnel

- **SLA de latence `/health`** : vérification sur 20 requêtes consécutives que le centile p95 reste sous le seuil maximal de 500 ms.
- **Robustesse Pydantic** : vérification du rejet HTTP 422 Unprocessable Entity pour des métriques physiquement aberrantes (pH > 14 ou turbidité négative).

| Critère | Seuil | Résultat mesuré | Statut |
|---------|-------|------------------|--------|
| Latence p95 `/health` | ≤ 500 ms | **12.4 ms** | **CONFORME** |
| Rejet pH > 14 | HTTP 422 | **HTTP 422** | **CONFORME** |
| Rejet turbidité < 0 | HTTP 422 | **HTTP 422** | **CONFORME** |

## 4. Couverture (pytest-cov)

| Métrique | Valeur | Gate d'acceptation | Statut |
|----------|--------|---------------------|--------|
| Couverture globale `src/` | **56.24 %** | ≥ 50.00 % | **VALIDE** |

```text
-------------------------------------------------------------------------
Name Stmts Miss Cover Missing
-------------------------------------------------------------------------
src/iot_service/config.py 21 0 100%
src/iot_service/hubeau_qualite_client.py 100 11 89% 139-145, 175, 211-217, 239-240, 254-261
src/iot_service/kafka_producer.py 76 52 32% 37-41, 46, 51, 55-65, 69-71, 83-118, 123-131, 136-138
src/iot_service/main.py 64 23 64% 23, 29-61, 149
src/iot_service/quality_poller.py 80 48 40% 55-60, 63, 67, 71, 75, 80, 84-104, 108-109, 113-148
src/iot_service/simulator/__init__.py 0 0 100%
src/iot_service/simulator/generator.py 79 50 37% 50-57, 62-132, 158-179
src/iot_service/simulator/orchestrator.py 76 46 39% 31, 48-57, 61-67, 76-77, 81, 85, 89, 92, 95-128
src/iot_service/simulator/sensors.py 22 4 82% 193-196
src/iot_service/station_mapping.py 19 1 95% 97
-------------------------------------------------------------------------
TOTAL 537 235 56.24%
Required test coverage of 50% reached. Total coverage: 56.24%
```

## 5. Preuve pipeline complet au vert

Le pipeline d'intégration continue bloquant s'est exécuté avec succès sur la branche de rendu.

- Date d’exécution : **2026-07-29** (UTC)
- Pipeline ID / Commit : **`abf1583`** (`EC03-UrbanHub-iot-service`)
- Durée totale : **48 secondes** (SLA ≤ 10 min respecté)
- Résultat des jobs :
 1. `1 · INSTALL` → **SUCCESS**
 2. `2 · TEST` → **SUCCESS** (20/20 passed, coverage 56.24 %)
 3. `3 · QUALITY` → **SUCCESS** (Ruff OK, Mypy 0 error)
 4. `4 · SECURITY` → **SUCCESS** (Gitleaks 0 leak, Trivy 0 CRITICAL, Bandit 0 High/Medium)
 5. `5 · BUILD` → **SUCCESS** (Image non-root validée)
 6. `6 · DEPLOY` → **SUCCESS** (Smoke test HTTP 200 `/health`)

