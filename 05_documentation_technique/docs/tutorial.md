# Tutoriel — Prise en main rapide de `iot-service`

> **Objectif** : Installer, exécuter et vérifier le microservice `iot-service` sur votre poste local en moins de 5 minutes.

---

## Prérequis

Avant de commencer, vérifiez que votre environnement dispose des outils suivants :

- **Python** : `3.13.0` ou plus récent.
- **`uv`** : Gestionnaire de paquets et d'environnements Python ultra-rapide ([astral.sh/uv](https://docs.astral.sh/uv/)).
- **Docker & Docker Compose** : (Facultatif pour l'exécution purement Python, requis pour la pile Kafka).

```bash
# Vérification des versions
python --version # -> Python 3.13.x
uv --version # -> uv 0.5.x ou +
docker --version # -> Docker version 27.x ou +
```

---

## Étape 1 : Récupération du Code & Installation

 Positionnez-vous dans le répertoire du microservice `iot-service` :

```bash
cd iot-service
```

 Exécutez l'installation déterministe des dépendances avec `uv` (en s'appuyant sur le fichier verrouillé `uv.lock`) :

```bash
uv sync --frozen --all-groups
```

> **Note** : `uv` va automatiquement télécharger l'interpréteur Python 3.13 si nécessaire et créer un environnement virtuel isolé sous `.venv/`.

---

## Étape 2 : Lancement du Microservice en Mode Développement

Démarrez le serveur FastAPI avec rechargement automatique :

```bash
PYTHONPATH=src uv run uvicorn iot_service.main:app --reload --port 8001
```

Vous devez obtenir un affichage similaire à celui-ci :

```text
INFO: Will watch for changes in these directories: ['/workspace/iot-service/src']
INFO: Uvicorn running on http://127.0.0.1:8001 (Press CTRL+C to quit)
INFO: Started reloader process [12345] using WatchFiles
INFO: Started server process [12346]
INFO: Waiting for application startup.
INFO: Starting background tasks: Hub'Eau poller + Local simulator
INFO: Application startup complete.
```

---

## Étape 3 : Vérification du Fonctionnement

### 1. Test du Healthcheck HTTP

Ouvrez un second terminal et interrogez l'endpoint de santé `/health` :

```bash
curl -s http://127.0.0.1:8001/health | jq .
```

**Réponse attendue (HTTP 200)** :

```json
{
 "status": "healthy",
 "service": "iot-service",
 "version": "0.1.1",
 "timestamp": "2026-07-29T14:00:00Z"
}
```

### 2. Injection d'une Mesure via l'API REST Gateway

Simulez l'envoi d'une mesure physico-chimique pour la station `SEINE-VITRY-001` :

```bash
curl -X POST http://127.0.0.1:8001/api/sensors/SEINE-VITRY-001/metrics \
 -H "Content-Type: application/json" \
 -d '{
 "ph": 7.4,
 "turbidite_ntu": 15.2,
 "temperature_c": 19.5,
 "niveau_m": 1.25,
 "debit_m3s": 210.0,
 "oxygene_dissous_mgl": 8.1
 }' | jq .
```

**Réponse attendue (HTTP 200)** :

```json
{
 "status": "accepted",
 "sensor_id": "SEINE-VITRY-001",
 "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
 "published_to_kafka": true
}
```

---

## Étape 4 : Exécution des Tests Unitaires

Pour vérifier la conformité du code et la couverture de tests :

```bash
PYTHONPATH=src uv run pytest tests/ -v --cov=src
```

**Résultat attendu** : 20 tests passés avec un taux de couverture ≥ 50 %.

---

## Prochaine Étape

Félicitations ! Votre environnement local est fonctionnel.
Pour découvrir comment déployer l'ensemble de la plateforme via Docker Compose, consultez le [Guide Pratique de Déploiement](how-to-guides.md).
