# Référence Technique — API REST, Modèles & Configuration

> **Objectif** : Fournir une documentation de référence exhaustive du microservice `iot-service` (spécifications REST, schémas Pydantic v2, variables d'environnement, CLI et docstrings).

---

## Spécification OpenAPI / REST

Le microservice expose ses spécifications sous forme de schémas OpenAPI v3 accessibles sur `/docs` (Swagger UI) et `/openapi.json`.

### Endpoints de l'API

#### 1. `GET /health` — Vérification de Santé (Healthcheck)

- **Description** : Retourne l'état opérationnel du microservice (SLA latence p95 < 500ms).
- **Authentification** : Aucune.
- **Code HTTP Succès** : `200 OK`

**Exemple de Payload JSON de réponse** :

```json
{
 "status": "healthy",
 "service": "iot-service",
 "version": "0.1.1",
 "timestamp": "2026-07-29T14:00:00Z"
}
```

---

#### 2. `POST /api/sensors/{sensor_id}/metrics` — Ingestion de Mesures Physiques

- **Description** : Accepte les métriques d'un capteur physique, les valide via Pydantic v2 et les publie sur le topic Kafka `mesure.qualite.eau`.
- **Paramètres de Path** :
 - `sensor_id` (string, requis) : Identifiant du capteur (ex. `SEINE-VITRY-001`). Must follow pattern `SEINE-[A-Z0-9-]+`.
- **Headers requis** : `Content-Type: application/json`
- **Codes de retour** :
 - `200 OK` : Mesure acceptée et transmise à Kafka.
 - `422 Unprocessable Entity` : Données invalides (ex. pH > 14, turbidité négative).
 - `500 Internal Server Error` : Échec d'envoi Kafka.

**Exemple de Payload JSON de requête (Valide)** :

```json
{
 "ph": 7.45,
 "turbidite_ntu": 12.8,
 "temperature_c": 19.2,
 "niveau_m": 1.15,
 "debit_m3s": 215.0,
 "oxygene_dissous_mgl": 8.30
}
```

**Exemple de Payload JSON de réponse (`200 OK`)** :

```json
{
 "status": "accepted",
 "sensor_id": "SEINE-VITRY-001",
 "event_id": "550e8400-e29b-41d4-a716-446655440000",
 "published_to_kafka": true
}
```

---

### Enveloppe d'Erreur Standardisée (`422 Unprocessable Entity`)

Toutes les erreurs de validation respectent la structure RFC 7807 avec propagation du `trace_id` :

```json
{
 "error": {
 "code": "VALIDATION_ERROR",
 "message": "Validation failed for incoming sensor metrics",
 "details": [
 {
 "loc": ["body", "ph"],
 "msg": "Input should be less than or equal to 14",
 "type": "less_than_equal"
 }
 ],
 "trace_id": "req-998877665544332211"
 }
}
```

---

## Modèles & Validation Pydantic v2

### `SensorMetricsInput` (`src/iot_service/config.py` / `main.py`)

```python
from pydantic import BaseModel, Field


class SensorMetricsInput(BaseModel):
 ph: float = Field(..., ge=0.0, le=14.0, description="Potentiel Hydrogène")
 turbidite_ntu: float = Field(
 ..., ge=0.0, description="Turbidité en NTU (≥ 0)"
 )
 temperature_c: float = Field(
 ..., ge=-10.0, le=50.0, description="Température (°C)"
 )
 niveau_m: float = Field(..., ge=0.0, description="Niveau de l'eau (m)")
 debit_m3s: float = Field(..., ge=0.0, description="Débit (m³/s)")
 oxygene_dissous_mgl: float = Field(
 ..., ge=0.0, le=30.0, description="Oxygène dissous (mg/L)"
 )
```

---

## Variables d'Environnement

| Variable | Type | Valeur par défaut | Description |
|----------|------|-------------------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | string | `localhost:9092` | Adresses des brokers Kafka séparées par des virgules |
| `WATER_QUALITY_TOPIC` | string | `mesure.qualite.eau` | Nom du topic Kafka de destination |
| `QUALITY_POLL_INTERVAL_SECONDS` | int | `21600` (6h) | Fréquence d'interrogation de l'API Hub'Eau (secondes) |
| `SIMULATOR_INTERVAL_SECONDS` | int | `300` (5min) | Cadence du simulateur local de capteurs virtuels |
| `SIMULATOR_JITTER_SECONDS` | int | `30` | Variations aléatoires sur l'intervalle du simulateur |
| `LOG_LEVEL` | string | `INFO` | Niveau de verbosité (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Docstrings & Mkdocstrings

Le code source du microservice est entièrement annoté selon les conventions **Google Python Style Guide**.

Exemple d'extraction via le plugin `mkdocstrings` :

::: iot_service.hubeau_qualite_client.HubEauQualiteClient
 options:
 show_source: true
 heading_level: 3

::: iot_service.simulator.orchestrator.SimulatorOrchestrator
 options:
 show_source: true
 heading_level: 3
