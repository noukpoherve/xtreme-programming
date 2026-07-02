# Exemples de refactor — UrbanHub

Ce document illustre des refactors réalisés dans le projet, avec comparaison avant/après.

---

## 1. Kafka Producer : booléen → machine à états explicite

### Avant (état implicite)

```python
class MeasurementProducer:
    def __init__(self, ...):
        self._ready = False

    async def start(self):
        self._ready = True

    async def send(self, measurement):
        if not self._ready:
            return False
        ...
```

**Problème** : un booléen ne distingue pas `STARTING`, `FAILED`, ni les transitions intermédiaires. Difficile à tester et à observer.

### Après (enum `ProducerState`)

```python
class ProducerState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"

class MeasurementProducer:
    def __init__(self, ...):
        self._state = ProducerState.STOPPED

    @property
    def state(self) -> ProducerState:
        return self._state

    async def start(self):
        self._state = ProducerState.STARTING
        ...
        self._state = ProducerState.RUNNING
```

**Bénéfices** : traçabilité, testabilité, respect du principe **Single Responsibility** (la classe gère son cycle de vie de façon explicite).

Fichiers : `iot-service/src/iot_service/kafka_producer.py`, `alert-service/src/alert_service/kafka_producer.py`

---

## 2. Alert Service : logique métier extraite (Strategy)

### Avant

Les seuils pH/turbidité étaient mélangés dans le service principal, rendant l'extension difficile.

### Après

```python
class AlertRule(Protocol):
    def evaluate(self, measurement: WaterMeasurementEvent) -> list[AlertPayload]: ...

class DefaultAlertRule:
    def evaluate(self, measurement): ...

class AlertService:
    def __init__(self, rules: list[AlertRule] | None = None, ...):
        self.rules = rules or [DefaultAlertRule()]
```

**Bénéfices** : **Open/Closed** — nouvelles règles sans modifier `AlertService`. Testable via `DummyRule` (stub).

Fichier : `alert-service/src/alert_service/service.py`

---

## 3. Capteur : DTO passif → entité avec pattern State

### Avant

```python
@dataclass
class Sensor:
    sensor_id: str
    active: bool = True
```

Le champ `active` ne modélise pas maintenance, panne, ni les comportements associés.

### Après

```python
class Capteur:
    def capturer(self, ph, turbidity, level, flow):
        return self._etat.capturer(self, ph, turbidity, level, flow)

    def mettre_en_maintenance(self):
        self._etat.mettre_en_maintenance(self)
```

Chaque état (`ActifState`, `MaintenanceState`, `EnPanneState`, `InactifState`) encapsule ses transitions et son comportement de capture.

**Bénéfices** : **encapsulation**, **isolation des responsabilités**, transitions métier explicites.

Fichiers : `iot-service/src/iot_service/capteur.py`, `iot-service/src/iot_service/capteur_state.py`

---

## 4. Persistance : accès direct Redis → Repository

### Avant

Logique Redis dispersée dans les handlers API.

### Après

```python
class SensorRepository:
    def save(self, sensor: Sensor) -> None: ...
    def get(self, sensor_id: str) -> Optional[Sensor]: ...
```

**Bénéfices** : **DIP** — le domaine ne dépend pas de Redis ; fallback mémoire pour les tests locaux.

Fichiers : `iot-service/src/iot_service/sensor_repository.py`, `alert-service/src/alert_service/repository.py`
