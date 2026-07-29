# 🏛️ Architecture & Choix de Conception

> **Objectif** : Expliquer les principes fondateurs de l'architecture du microservice `iot-service`, le respect des règles SOLID, du Domain-Driven Design (DDD) et illustrer les flux via des diagrammes UML Mermaid.js.

---

## 🎯 Vue d'Ensemble & Découpage

Le microservice `iot-service` agit en tant que **Producteur Événementiel Pur**. Il orchestre l'ingestion sans état (stateless) et la publication des événements de qualité de l'eau.

```mermaid
graph TD
    subgraph Ingestion ["Ingestion layer"]
        HQ["Hub'Eau Qualité Poller (6h)"]
        LS["Simulator Orchestrator (5min)"]
        REST["FastAPI Gateway (POST /metrics)"]
    end

    subgraph Domain ["Domain Layer & Validation"]
        Pydantic["SensorMetricsInput (Pydantic v2)"]
        StationMap["StationMapping (Seine 001-012)"]
    end

    subgraph EventBus ["Kafka Messaging"]
        Producer["AioKafkaProducer"]
        Topic["mesure.qualite.eau"]
    end

    HQ --> StationMap
    LS --> StationMap
    REST --> Pydantic
    Pydantic --> Producer
    StationMap --> Producer
    Producer --> Topic
```

---

## 📐 Principes SOLID appliqués

- **Single Responsibility Principle (SRP)** :
  - `HubEauQualiteClient` ne gère que les requêtes HTTP et le découpage JSON de l'API Hub'Eau.
  - `QualityPoller` s'occupe uniquement du cadencement d'interrogation (background task 6h).
  - `KafkaProducer` gère exclusivement la connexion et la sérialisation Kafka.
- **Open/Closed Principle (OCP)** :
  - Le système d'ingestion est ouvert à l'ajout de nouvelles sources (ex. un nouveau capteur ou API météo) sans modifier le moteur de publication Kafka.
- **Liskov Substitution Principle (LSP)** :
  - Les événements générés par le simulateur local ou issus de l'API réelle Hub'Eau respectent exactement le même modèle de domaine `WaterMeasurementEvent`.
- **Interface Segregation Principle (ISP)** :
  - Les clients interagissent avec des interfaces restreintes (ex. l'API REST FastAPI n'expose que les endpoints nécessaires sans révéler l'implémentation interne Kafka).
- **Dependency Inversion Principle (DIP)** :
  - La logique métier ne dépend pas directement des détails d'implémentation bas niveau (`urllib` ou `aiokafka`), mais d'abstractions de modèles.

---

## 📊 Diagramme de Classes UML (Mermaid.js)

Le diagramme ci-dessous illustre la structure des classes et des composants clés de `iot-service` :

```mermaid
classDiagram
    class HubEauQualiteClient {
        -float _timeout
        +get_latest(station_code: str) LatestQualityMeasurement
        -_fetch_latest_analysis(station_code, parameter_code) HubEauAnalysis
    }

    class QualityPoller {
        -HubEauQualiteClient _client
        -int _interval_seconds
        +start()
        +poll_all_stations()
    }

    class SimulatorOrchestrator {
        -int _interval_seconds
        -list~Sensor~ _sensors
        +run_loop()
        +generate_tick() list~WaterMeasurementEvent~
    }

    class MeasurementGenerator {
        +generate_measurement(sensor_id: str) WaterMeasurementEvent
    }

    class SensorMetricsInput {
        +float ph
        +float turbidite_ntu
        +float temperature_c
        +float niveau_m
        +float debit_m3s
        +float oxygene_dissous_mgl
    }

    class WaterMeasurementEvent {
        +str event_id
        +str trace_id
        +str capteur_id
        +datetime timestamp
        +dict mesures
        +str data_source
    }

    QualityPoller --> HubEauQualiteClient : utilise
    SimulatorOrchestrator --> MeasurementGenerator : orchestre
    MeasurementGenerator ..> WaterMeasurementEvent : crée
    SensorMetricsInput ..> WaterMeasurementEvent : convertit
```

---

## 🔄 Diagramme de Séquence UML (Mermaid.js)

Le diagramme de séquence suivant décrit le parcours complet d'une métrique reçue via l'API REST ou le Poller jusqu'à sa publication sur Kafka :

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client HTTP / Poller
    participant API as FastAPI Gateway
    participant Val as Validator Pydantic v2
    participant Map as Station Mapping
    participant Prod as AioKafkaProducer
    participant Kafka as Topic Kafka (mesure.qualite.eau)

    Client->>API: POST /api/sensors/{sensor_id}/metrics (JSON payload)
    API->>Val: Valider la charge utile (SensorMetricsInput)
    alt Données Invalides (ex. pH = 99.0)
        Val-->>API: ValidationError (Pydantic)
        API-->>Client: HTTP 422 Unprocessable Entity (Standardized Error + trace_id)
    else Données Valides
        Val-->>API: Modèle validé
        API->>Map: Résoudre la localisation & metadata station
        Map-->>API: Coordonnées GPS & point de référence
        API->>Prod: send_event(WaterMeasurementEvent)
        Prod->>Kafka: PUBLISH JSON payload (Headers: trace_id)
        Kafka-->>Prod: ACK Partition Offset
        Prod-->>API: Succès transmission
        API-->>Client: HTTP 200 OK (accepted, event_id)
    end
```

---

## 💡 Choix Techniques & Arbitrages

1. **Fusion du Simulateur dans `iot-service`** :
   - *Motivation* : Éliminer la complexité opérationnelle d'un conteneur simulateur séparé. Les tâches de fond `lifespan` FastAPI gèrent désormais à la fois le Poller Hub'Eau (6h) et le Simulateur (5min) au sein de la même instance Python.
2. **Standardisation Pydantic v2 & `trace_id`** :
   - *Motivation* : Garantie de la robustesse des données entrantes. Chaque événement transporte un `trace_id` propagé dans les en-têtes Kafka et les réponses HTTP pour assurer la traçabilité end-to-end de l'observabilité.
