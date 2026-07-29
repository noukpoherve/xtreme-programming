# Diagramme de Sequence UML — Flux d'ingestion iot-service

Le diagramme de sequence suivant decrit le parcours complet d'une metrique recue via l'API REST ou le Poller Hub'Eau jusqu'a sa publication sur Kafka.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client HTTP / Poller
    participant API as FastAPI Gateway
    participant Val as Validator Pydantic v2
    participant Map as Station Mapping
    participant Prod as MeasurementProducer
    participant Kafka as Topic Kafka (mesure.qualite.eau)

    Client->>API: POST /api/sensors/{sensor_id}/metrics (JSON payload)
    API->>Val: Valider la charge utile (SensorMetricsPayload)
    alt Donnees Invalides (ex. pH = 99.0)
        Val-->>API: ValidationError (Pydantic)
        API-->>Client: HTTP 422 Unprocessable Entity (trace_id)
    else Donnees Valides
        Val-->>API: Modele valide
        API->>Map: Resoudre la localisation et metadata station
        Map-->>API: Coordonnees GPS et point de reference
        API->>Prod: send(WaterMeasurementEvent)
        Prod->>Kafka: PUBLISH JSON payload (Headers: trace_id)
        Kafka-->>Prod: ACK Partition Offset
        Prod-->>API: Succes transmission
        API-->>Client: HTTP 202 Accepted (event_id, sensor_id)
    end
```
