# 🔄 Guide de Maintenance & Journal des Versions (Changelog)

> **Objectif** : Fournir une procédure guidée pour faire évoluer le microservice (ajout de règles métier, modification des stations) et suivre l'historique des releases.

---

## 🛠️ Guide de Maintenance (Procédure d'Évolution)

### 1. Procédure pour Ajouter une Nouvelle Station Physico-Chimique

Si une nouvelle station physique Hub'Eau doit être supervisée (ex. `SEINE-NEUILLY-013`) :

1. **Ouvrir le fichier de mapping** : `iot-service/src/iot_service/station_mapping.py`.
2. **Ajouter la station au dictionnaire `STATION_MAPPINGS`** :

```python
# Extrait station_mapping.py
STATION_MAPPINGS["SEINE-NEUILLY-013"] = StationMapping(
    sensor_id="SEINE-NEUILLY-013",
    hubeau_station_code="03000015",  # Code Sandre Hub'Eau
    label="Neuilly-sur-Seine",
    latitude=48.8845,
    longitude=2.2687,
)
```

3. **Mettre à jour les tests unitaires** : `iot-service/tests/test_station_mapping.py`.
4. **Valider les tests** : `PYTHONPATH=src uv run pytest tests/`.

---

### 2. Procédure pour Modifier une Borne de Validation (Pydantic v2)

Pour modifier les seuils de validation d'un paramètre (ex. passer la température max autorisée de 50°C à 45°C) :

1. **Éditer le schéma Pydantic** dans `iot-service/src/iot_service/config.py` (ou `main.py`).
2. **Ajuster le champ** :

```python
temperature_c: float = Field(..., ge=-10.0, le=45.0, description="Température (°C)")
```

3. **Lancer les vérifications de qualité et de tests** :

```bash
uv run ruff check src/ tests/
uv run mypy src/
uv run pytest tests/
```

---

## 🚀 Stratégie de Publication Multi-Versions avec `mike`

Le portail de documentation est configuré pour supporter le versionnement multi-versions via l'outil **`mike`** intégré à MkDocs Material :

```bash
# 1. Déployer une nouvelle version de la documentation (ex. v0.1.1)
uv run mike deploy --push --update-aliases 0.1.1 latest

# 2. Définir la version par défaut du portail
uv run mike set-default --push latest
```

---

## 📜 Journal des Versions (Changelog)

Le journal des modifications s'appuie sur la convention internationale **Conventional Commits** (`feat:`, `fix:`, `ci:`, `docs:`, `refactor:`).

### [0.4.0] — 2026-07-02

#### Added
- Restauration de l'état de la machine à états au démarrage depuis la base PostgreSQL (`state_transitions`).
- Architecture Domain-Driven Design (DDD) avec `SensorStreamProcessor` comme Aggregate Root.

#### Changed
- Suppression des anciens endpoints synchrone HTTP pour renforcer l'architecture événementielle asynchrone via Kafka.

---

### [0.3.0] — 2026-07-01

#### Added
- Intégration de l'API réelle Hub'Eau (`qualite_rivieres`) pour 6 stations de la Seine (`SEINE-VITRY-001` à `SEINE-COLOMBES-012`).
- Poller automatique avec fréquence d'interrogation fixée à 6 heures (`QUALITY_POLL_INTERVAL_SECONDS=21600`).

---

### [0.2.0] — 2026-06-15

#### Added
- Panneau d'analyse détaillé (drawer) par capteur sur le tableau de bord React SPA.
- Endpoints REST de consultation de métriques historiques et d'alertes.

---

### [0.1.1] — 2026-05-20

#### Added
- Initialisation du microservice `iot-service` avec Gateway FastAPI, simulateur de capteurs virtuels et publication Kafka.
- Pipeline CI/CD 6 étapes bloquantes avec scans DevSecOps (Gitleaks, Bandit, Trivy, CycloneDX).
