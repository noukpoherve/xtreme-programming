# UrbanHub — Smart City Water Quality Platform

> Master project — Distributed architecture, event-driven microservices & Extreme Programming practices

## 🎯 Statut : Prêt évaluation (2 Juillet 2026)

✅ **Patterns de conception** (Strategy, Repository, State, Adapter)  
✅ **API REST CRUD complète** (3 microservices)  
✅ **Contrats API formalisés** (Pydantic + `CONTRATS_API.md`)  
✅ **Tests unitaires, mocks/stubs, CI GitHub Actions**  
✅ **Message bus Kafka** + persistance Redis  
✅ **Changelog** + documentation par service

---

## Architecture

UrbanHub is composed of independent microservices that communicate via REST and Kafka events.

```
                    +------------------+
                    |   Hub'Eau API    |
                    +--------+---------+
                             |
                             | (poll every 5 min)
                             v
                    +------------------+
                    |  IoT Ingestion   |  <-- Background scheduler fetches data
                    |    Service       |  <-- Publishes raw measurements to Kafka
                    |   (iot-service)  |
                    +--------+---------+
                             | Kafka: mesure.qualite.eau
                             v
                    +------------------+
                    |  Alert Service   |  <-- Consumes measurements from Kafka
                    | (alert-service)  |  <-- Analyses thresholds & publishes alerts
                    +--------+---------+
                             | Kafka: alerte.pollution.detectee
                             v
                    +------------------+
                    | Notification Svc |  <-- (future) Push / email / SMS
                    +------------------+
```

UrbanHub IRVE (bornes électriques) — branche supervision :

```
OCPP Gateway (futur) → Kafka: charge.station.events → supervision-service (8002)
                                                      → Dashboard WebSocket / REST
```

## Services

| Service | Role | Port | Tech |
|---------|------|------|------|
| **iot-service** | Ingestion & measurement publisher + Sensor CRUD | `8001` | FastAPI, aiokafka, Hub'Eau client, Redis |
| **alert-service** | Threshold analysis, alert publisher + Alert CRUD | `8000` | FastAPI, aiokafka, Strategy pattern, Redis |
| **supervision-service** | IRVE supervision, dashboard, WebSocket | `8002` | FastAPI, Kafka consumer, pattern Observer |
| **kafka** | Event bus (KRaft mode, no ZooKeeper) | `9092` | apache/kafka:3.7.1 |
| **redis** | Alerts & Sensors persistence | `6379` | redis:latest |
| **kafka-ui** | Topic inspection | `8080` | kafbat/kafka-ui |
| **prometheus** | Metrics collection | `9090` | prom/prometheus |
| **grafana** | Logs & metrics dashboards | `3000` | grafana/grafana |
| **loki** | Log aggregation | `3100` | grafana/loki |
| **promtail** | Docker log shipping | — | grafana/promtail |

## 🚀 Quick Start

### Services actuellement lancés

```bash
# Terminal 1 - Alert Service
cd alert-service
$env:PYTHONPATH='D:\...\alert-service\src'
python -m uvicorn alert_service.main:app --reload --port 8000

# Terminal 2 - IoT Service  
cd iot-service
$env:PYTHONPATH='D:\...\iot-service\src'
python -m uvicorn iot_service.main:app --reload --port 8001
```

### Accès aux APIs

- **Alert Service Swagger** : http://localhost:8000/docs
- **IoT Service Swagger** : http://localhost:8001/docs
- **Supervision Service Swagger** : http://localhost:8002/docs

---

## 📚 Documentation Complète

### Rapports & Guides
- **[RAPPORT_AMELIORATIONS.md](RAPPORT_AMELIORATIONS.md)** - Compte rendu détaillé des améliorations
- **[FICHIERS_MODIFICATIONS.md](FICHIERS_MODIFICATIONS.md)** - Liste des fichiers créés/modifiés
- **[docs/OUTILS.md](docs/OUTILS.md)** - Stack outillage (Docker, pytest, Swagger, CI…)
- **[docs/REFACTOR_EXAMPLES.md](docs/REFACTOR_EXAMPLES.md)** - Exemples de refactor avant/après
- **[docs/COMMUNICATION.md](docs/COMMUNICATION.md)** - Communication technique vs fonctionnelle
- **[docs/postman/](docs/postman/)** - Collection Postman pour tests API
- **[changelog.md](changelog.md)** - Historique des versions (Keep a Changelog)

### Contrats API
- **Alert Service** : [alert-service/src/alert_service/contracts.py](alert-service/src/alert_service/contracts.py)
- **IoT Service** : [iot-service/src/iot_service/sensor_contracts.py](iot-service/src/iot_service/sensor_contracts.py)

### Architecture
- **Alert Service** : [alert-service/README.md](alert-service/README.md)
- **IoT Service** : [iot-service/README.md](iot-service/README.md)
- **Supervision Service** : [supervision-service/README.md](supervision-service/README.md)

---

## 🏗️ Patterns de Conception Utilisés

### ✅ State Pattern (Capteur)
Comportement et transitions d'état encapsulés (`actif`, `maintenance`, `en_panne`, `inactif`)
```python
capteur = Capteur.from_sensor(sensor)
capteur.mettre_en_maintenance()  # capture bloquée tant que non réactivé
capteur.activer()
```
Fichiers : `iot-service/src/iot_service/capteur.py`, `capteur_state.py`

### ✅ Strategy Pattern
Permettre des règles d'alerte extensibles sans modifier le service
```python
class AlertRule(Protocol):
    def evaluate(self, measurement: WaterMeasurementEvent) -> list[AlertPayload]:
        ...
```

### ✅ Repository Pattern
Abstraction complète de la persistance (Redis)
```python
class AlertRepository:
    async def save(self, alert: AlertPayload) -> None
    async def get(self, alert_id: str) -> Optional[AlertPayload]
    async def get_all(self, limit: int, offset: int) -> list[AlertPayload]
```

### ✅ Dependency Injection
Services reçoivent leurs dépendances
```python
service = AlertService(rules=custom_rules, repository=custom_repo)
```

### ✅ State Management
Cycle de vie explicite du composant
```python
class ProducerState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
```

---

## 📊 Endpoints de l'API

### Alert Service (Port 8000)

#### Créer une alerte
```bash
POST /alerts
Content-Type: application/json

{
  "alert_id": "a1b2c3d4",
  "event_id": "e1e2e3e4",
  "sensor_id": "SEINE-001",
  "timestamp": "2026-06-30T12:00:00Z",
  "severity": "CRITICAL",
  "type": "ph",
---

## 📊 API Endpoints

Legacy alias: `POST /alertes`

### Alert Service (Port 8000)

```
POST   /alerts                      # Create alert
GET    /alerts?limit=10&offset=0    # List alerts
GET    /alerts?option=stats         # Get statistics
GET    /alerts/{alert_id}           # Get alert details
GET    /alerts/sensor/{sensor_id}   # Get alerts by sensor
PUT    /alerts/{alert_id}           # Update alert
DELETE /alerts/{alert_id}           # Delete alert
```

### IoT Service (Port 8001)

```
POST   /sensors                     # Register sensor
GET    /sensors                     # List sensors
GET    /sensors?option=stats        # Get statistics
GET    /sensors/{sensor_id}         # Get sensor details
PUT    /sensors/{sensor_id}         # Update sensor
DELETE /sensors/{sensor_id}         # Delete sensor
POST   /ingest                      # Fetch from Hub'eau
POST   /simulate?ph=7.0&turbidity=75.0  # Simulate measurement
POST   /sensors/{id}/activer            # State: activer capteur
POST   /sensors/{id}/maintenance        # State: maintenance
POST   /sensors/{id}/panne              # State: panne
POST   /sensors/{id}/desactiver         # State: désactiver
```

### Supervision Service (Port 8002)

```
GET    /bornes
GET    /bornes/{borne_id}
GET    /sessions
GET    /tableau-de-bord/resume
GET    /tableau-de-bord/carte
GET    /incidents
GET    /sante
WS     /ws/supervision/direct
```

Legacy aliases: `/capteurs`, `/capteurs/{id}`, `/capteurs-stats`.

---

## 🗄️ Persistence

### Redis
- **Alerts** : Key `alert:{alert_id}`, Index `alerts:index`
- **Sensors** : Key `sensor:{sensor_id}`, Set `sensors:all`

---

## Development

Each service is fully autonomous with its own `pyproject.toml`, tests and configuration.

```bash
cd alert-service
python -m pytest tests/ -v

cd ../iot-service
python -m pytest tests/ -v
```

## Kafka Topics

| Topic | Producer | Consumer | Purpose |
|-------|----------|----------|---------|
| `mesure.qualite.eau` | iot-service | alert-service | Raw water quality measurements |
| `alerte.pollution.detectee` | alert-service | (future) | Generated alerts after threshold analysis |

## Event Format

Raw measurements use a structured `WaterMeasurementEvent`:

```json
{
  "event_type": "mesure.qualite.eau",
  "event_id": "uuid-v4",
  "trace_id": "uuid-v4",
  "capteur_id": "F700000103",
  "timestamp": "2026-05-06T14:52:01Z",
  "localisation": {
    "latitude": 48.8447,
    "longitude": 2.3655,
    "point_reference": "Station F700000103"
  },
  "mesures": {
    "ph": 7.4,
    "turbidite_ntu": 8.0,
    "temperature_c": 0.0,
    "niveau_m": 0.93,
    "debit_m3s": 252.0,
    "oxygene_dissous_mgl": 0.0
  }
}
```

## Thresholds

| Parameter | Warning | Critical |
|-----------|---------|----------|
| pH | < 6.5 or > 8.5 | < 6.0 or > 9.0 |
| Turbidity | > 10 NTU | > 50 NTU |

## CI / Tests

- `black` for formatting
- `pytest` for unit and integration tests (~40 tests)
- `unittest.mock` for mocks/stubs (Hub'Eau client, DummyRule, DummyProducer)
- GitHub Actions matrix CI (alert, iot, supervision) + Docker build
- Collection Postman : `docs/postman/UrbanHub.postman_collection.json`

## Project structure

```
urbanhub/
├── alert-service/          # Alert REST API + Kafka consumer/producer
├── iot-service/            # Ingestion + Capteur State pattern + Kafka producer
├── supervision-service/    # IRVE supervision + WebSocket + Kafka consumer
├── docs/                   # Postman, outils, refactors, communication
├── monitoring/             # Prometheus, Grafana, Loki, Promtail configs
├── docker-compose.yml      # Local orchestration (3 services + infra)
├── changelog.md            # Keep a Changelog
└── README.md               # This file
```
