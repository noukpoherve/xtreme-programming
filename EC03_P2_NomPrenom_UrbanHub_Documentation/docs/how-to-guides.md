# Guides Pratiques — Exploitation & Déploiement

> **Objectif** : Fournir des procédures étape par étape pour les opérations courantes de déploiement, de test et d'administration du microservice `iot-service`.

---

## Guide 1 : Déploiement Local via Docker Compose

### 1. Lancement de la Pile Complète

Pour exécuter `iot-service` avec la pile d'infrastructure (Apache Kafka KRaft, PostgreSQL/TimescaleDB, Grafana) :

```bash
# Depuis la racine du monorepo UrbanHub
docker compose up --build -d
```

### 2. Vérification des Conteneurs en Cours d'Exécution

```bash
docker compose ps
```

| Service | Conteneur | Port Hôte | Rôle |
|---------|-----------|-----------|------|
| **iot-service** | `urbanhub-iot-service-1` | `8001` | Ingestion & Simulation Kafka |
| **alert-service** | `urbanhub-alert-service-1` | `8000` | Machine à états & Alerte REST/WS |
| **dashboard** | `urbanhub-dashboard-1` | `5173` | Interface Web React SPA |
| **kafka** | `urbanhub-kafka-1` | `9092` | Broker Kafka KRaft |
| **kafka-ui** | `urbanhub-kafka-ui-1` | `8080` | Supervision des topics Kafka |

### 3. Consultation des Logs du Service Ingestion

```bash
docker compose logs -f iot-service
```

---

## Guide 2 : Déploiement du Seul Microservice `iot-service` (Conteneur Non-Root)

Si vous souhaitez builder et exécuter l'image isolée de `iot-service` (identique au job `BUILD` du pipeline CI/CD) :

```bash
# 1. Build de l'image Docker multi-stage
docker build -t urbanhub/iot-service:local ./iot-service

# 2. Vérification du statut non-root du conteneur (Sécurité)
docker inspect --format='{{.Config.User}}' urbanhub/iot-service:local
# Output attendu: appuser (non-root)

# 3. Lancement du conteneur
docker run -d \
 --name ec03-iot-app \
 -p 8001:8001 \
 -e KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
 urbanhub/iot-service:local
```

---

## Guide 3 : Exécution des Smoke Tests Automatisés

Le script `smoke_test.sh` permet de valider la disponibilité et la conformité du contrat d'API après un déploiement :

```bash
# Rendre le script exécutable
chmod +x EC03_P1_NomPrenom_UrbanHub_CICD/02_scripts/smoke_test.sh

# Lancer le smoke test sur l'URL locale
./EC03_P1_NomPrenom_UrbanHub_CICD/02_scripts/smoke_test.sh http://127.0.0.1:8001
```

**Étapes exécutées par le script** :
1. Boucle d'attente active (polling jusqu'à 90s) de l'endpoint `GET /health`.
2. Validation du code de statut HTTP 200.
3. Analyse JSON du payload (`status == "healthy"` et présence de la clé `version`).

---

## Guide 4 : Exécution de la Chaîne Globale Locale (`run_local_pipeline.sh`)

Pour simuler localement les 6 étapes du pipeline CI/CD avant d'effectuer un `git push` :

```bash
chmod +x EC03_P1_NomPrenom_UrbanHub_CICD/02_scripts/run_local_pipeline.sh
./EC03_P1_NomPrenom_UrbanHub_CICD/02_scripts/run_local_pipeline.sh
```

Le script exécutera séquentiellement :
1. `uv sync --frozen` (**INSTALL**)
2. `pytest` avec couverture (**TEST**)
3. `ruff` & `mypy` (**QUALITY**)
4. `bandit` & `trivy` (**SECURITY**)
5. `docker build` (**BUILD**)
6. `docker run` + `smoke_test.sh` (**DEPLOY**)
