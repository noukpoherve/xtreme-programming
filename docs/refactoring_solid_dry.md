# Rapport de refactoring — Principes SOLID & DRY
**Projet :** UrbanHub Water Quality
**Date :** 2026-06-29
**Portée :** `iot-service` et `alert-service`

---

## 1. Contexte du projet

Le projet est composé de deux micro-services Python (FastAPI + Kafka) :

| Service | Rôle |
|---|---|
| `iot-service` | Lit les données hydrologiques via l'API Hub'eau, les publie sur Kafka |
| `alert-service` | Consomme les mesures Kafka, génère et publie des alertes si les seuils sont dépassés |

```
[API Hub'eau] → iot-service → Kafka (mesure.qualite.eau) → alert-service → Kafka (alerte.pollution.detectee)
```

---

## 2. Violations identifiées avant refactoring

### 2.1 Violations SOLID

#### SRP — Single Responsibility Principle (Responsabilité unique)

**Violation 1 — `iot-service/sensor_service.py`**

Le fichier contenait deux choses de natures différentes dans le même module :
- `SensorMeasurement` : une **entité métier** (description d'une mesure physique)
- `IoTSensorSimulator` : un **comportement** (simulation d'un capteur)

Une entité de domaine ne devrait jamais partager son fichier avec une logique applicative.

**Violation 2 — `IoTSensorSimulator` ne portait pas l'état complet du capteur**

La classe `IoTSensorSimulator` n'avait qu'un attribut (`sensor_id`) et laissait les métadonnées du capteur (latitude, longitude, firmware_version, qualite_signal, temperature_c, oxygene_dissous_mgl) codées en dur dans le dataclass `SensorMeasurement`. Le capteur ne se connaissait pas lui-même.

```python
# AVANT — le capteur n'a pas d'état propre
class IoTSensorSimulator:
    def __init__(self, sensor_id: str):
        self.sensor_id = sensor_id  # un seul attribut

    def capture(self, ph, turbidity, level, flow) -> SensorMeasurement:
        return SensorMeasurement(
            sensor_id=self.sensor_id,
            ph=ph, turbidity=turbidity, level=level, flow=flow,
            # latitude/longitude/firmware... absents → valeurs par défaut du dataclass
        )
```

#### DIP — Dependency Inversion Principle (Inversion des dépendances)

**Violation 3 — `iot-service/main.py`**

La fonction `_poll_loop` dépendait directement du concret `MeasurementProducer` (implémentation Kafka). Impossible de substituer un writer vers un fichier ou une base de données sans modifier `main.py`.

```python
# AVANT — dépend du concret
async def _poll_loop(
    sensor_client: HubEauSensorClient,
    kafka_producer: MeasurementProducer  # ← concret Kafka
):
    await kafka_producer.send(measurement)  # méthode Kafka spécifique
```

**Violation 4 — `alert-service/kafka_consumer.py`**

`MeasurementConsumer` instanciait directement `AlertProducer` (Kafka) et le typait en concret. Impossible de substituer un autre canal d'envoi (webhook, email) sans toucher au consumer.

```python
# AVANT — dépend du concret
class MeasurementConsumer:
    def __init__(self, producer: AlertProducer | None = None):  # ← concret
        self._producer = producer or AlertProducer(...)
```

#### OCP — Open/Closed Principle (Ouvert/Fermé)

**Violation 5 — `alert-service/service.py`**

`AlertService.build_alerts_from_measurement()` contenait des chaînes `if/elif` codées en dur pour chaque paramètre (pH, turbidité). Ajouter un nouveau paramètre surveillé (oxygène dissous, température) imposait de **modifier** cette méthode existante au lieu d'étendre.

```python
# AVANT — ouvrir ce fichier pour ajouter un paramètre
def build_alerts_from_measurement(self, measurement):
    if ph < self.PH_CRITICAL_LOW or ph > self.PH_CRITICAL_HIGH:
        ...
    elif ph < self.PH_WARNING_LOW or ph > self.PH_WARNING_HIGH:
        ...
    if turbidity > self.TURBIDITY_CRITICAL:
        ...
    elif turbidity > self.TURBIDITY_WARNING:
        ...
    # Pour ajouter oxygène dissous → modifier cette méthode
```

> **Note :** La violation OCP n'a pas été corrigée dans ce refactoring car elle nécessite une refonte plus profonde de la logique de seuils (pattern Strategy ou table de règles). Elle reste identifiée pour une prochaine itération.

---

### 2.2 Violations DRY

**Violation 6 — `alert-service/models.py` : deux modèles identiques**

```python
# AVANT — deux classes strictement identiques
class Localisation(BaseModel):
    latitude: float
    longitude: float
    point_reference: str

class MeasurementLocalisation(BaseModel):  # copie exacte
    latitude: float
    longitude: float
    point_reference: str
```

`WaterMeasurementEvent` utilisait `MeasurementLocalisation` tandis que `AlertPayload` utilisait `Localisation`. La même structure était définie deux fois, risquant une divergence future.

**Violation 7 — `iot-service/main.py` : dict de réponse dupliqué**

Les endpoints `/ingest` et `/simulate` construisaient exactement le même dictionnaire de réponse HTTP, mot pour mot :

```python
# AVANT — dupliqué dans /ingest ET /simulate
return {
    "measurement": {
        "sensor_id": measurement.sensor_id,
        "uuid": measurement.uuid,
        "timestamp": measurement.timestamp.isoformat(),
        "ph": measurement.ph,
        "turbidity": measurement.turbidity,
        "level": measurement.level,
        "flow": measurement.flow,
        "latitude": measurement.latitude,
        "longitude": measurement.longitude,
    },
    "published": True,
}
```

---

## 3. Changements appliqués

### Tâche 1 — Extraire les entités métier immuables dans `domain/models.py`

**Fichier créé :** `iot-service/src/iot_service/domain/models.py`

`SensorMeasurement` a été déplacée du fichier `sensor_service.py` vers un module dédié `domain/`. Le dataclass est désormais `frozen=True` : **immuable** après création, hashable, et impossible à modifier accidentellement.

```python
# APRÈS — entité pure, isolée, immuable
@dataclass(frozen=True)
class SensorMeasurement:
    """Entité métier immuable — snapshot d'une mesure physique à un instant T."""
    sensor_id: str
    ph: float
    turbidity: float      # NTU
    level: float          # mètres
    flow: float           # m³/s
    uuid: str             = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime   = field(default_factory=lambda: datetime.now(timezone.utc))
    latitude: float       = 0.0
    longitude: float      = 0.0
    temperature_c: float  = 14.3
    oxygene_dissous_mgl: float = 7.1
    qualite_signal: str   = "GOOD"
    firmware_version: str = "2.4.1"
```

**Pourquoi `frozen=True` ?**
Une mesure physique passée ne se modifie pas. `frozen=True` impose cette invariant au niveau du langage : toute tentative de `measurement.ph = 6.0` lève une `FrozenInstanceError` à l'exécution. Cela empêche les bugs subtils où une mesure serait altérée après sa création.

---

### Tâche 2 — Classe `Sensor` responsable uniquement de l'état de son capteur (SRP)

**Fichier modifié :** `iot-service/src/iot_service/sensor_service.py`

`IoTSensorSimulator` a été remplacée par `Sensor`, un dataclass qui porte **toutes les métadonnées du capteur physique** : identifiant, coordonnées GPS, version firmware, qualité du signal, valeurs par défaut de température et d'oxygène.

```python
# APRÈS — le capteur connaît son propre état
@dataclass
class Sensor:
    """Responsabilité unique : modéliser l'état d'un capteur physique."""
    sensor_id: str
    latitude: float        = 0.0
    longitude: float       = 0.0
    firmware_version: str  = "2.4.1"
    qualite_signal: str    = "GOOD"
    temperature_c: float   = 14.3
    oxygene_dissous_mgl: float = 7.1

    def capture(self, ph, turbidity, level, flow,
                latitude=None, longitude=None) -> SensorMeasurement:
        """Produit une mesure immuable à partir des relevés bruts fournis."""
        return SensorMeasurement(
            sensor_id=self.sensor_id,
            ph=ph, turbidity=turbidity, level=level, flow=flow,
            latitude=latitude if latitude is not None else self.latitude,
            longitude=longitude if longitude is not None else self.longitude,
            temperature_c=self.temperature_c,
            oxygene_dissous_mgl=self.oxygene_dissous_mgl,
            qualite_signal=self.qualite_signal,
            firmware_version=self.firmware_version,
        )
```

**Ce que `Sensor` ne fait PAS (SRP respecté) :**
- Il ne sait pas ce qu'est Kafka
- Il ne sait pas écrire dans un fichier
- Il ne déclenche pas d'alertes
- Il ne fait pas de requêtes HTTP

`HubEauSensorClient` a aussi été mis à jour pour créer un `Sensor` en interne et déléguer la production de la mesure à celui-ci.

---

### Tâche 3 — Interfaces abstraites pour l'écriture et l'envoi d'alertes

#### `MeasurementWriter` — iot-service

**Fichier créé :** `iot-service/src/iot_service/domain/ports.py`

```python
class MeasurementWriter(ABC):
    """Port — abstrait tout canal d'écriture de mesures."""

    @abstractmethod
    async def write(self, measurement: SensorMeasurement) -> None: ...

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...
```

`MeasurementProducer` (Kafka) implémente désormais cette interface :

```python
class MeasurementProducer(MeasurementWriter):
    async def write(self, measurement: SensorMeasurement) -> None:
        # ... envoi Kafka
```

`_poll_loop` et les endpoints dépendent de l'abstraction, pas du concret :

```python
# APRÈS — dépend de l'abstraction
async def _poll_loop(sensor_client: HubEauSensorClient, writer: MeasurementWriter):
    await writer.write(measurement)
```

Pour ajouter un writer vers un fichier CSV, il suffit maintenant de créer :

```python
class CsvMeasurementWriter(MeasurementWriter):
    async def write(self, measurement: SensorMeasurement) -> None:
        # écriture dans un fichier CSV
        ...
```

Aucun autre fichier n'a besoin d'être modifié.

#### `AlertSender` — alert-service

**Fichier créé :** `alert-service/src/alert_service/ports.py`

```python
class AlertSender(ABC):
    """Port — abstrait tout canal d'envoi d'alertes."""

    @abstractmethod
    async def send(self, alert: AlertPayload) -> None: ...

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...
```

`AlertProducer` (Kafka) implémente `AlertSender`. `MeasurementConsumer` reçoit désormais un `AlertSender` en injection de dépendance :

```python
class MeasurementConsumer:
    def __init__(self, producer: AlertSender | None = None):
        self._producer: AlertSender = producer or AlertProducer(...)
```

---

### Corrections DRY

**DRY 1 — Suppression de `MeasurementLocalisation`**

`MeasurementLocalisation` a été supprimée d'`alert-service/models.py`. `WaterMeasurementEvent` utilise désormais `Localisation` (le seul modèle de localisation). Le test `test_measurement_bridge.py` a été mis à jour en conséquence.

**DRY 2 — Extraction de `_measurement_response()`**

La construction du dict de réponse HTTP est centralisée dans une fonction privée :

```python
def _measurement_response(measurement: SensorMeasurement) -> dict:
    return {
        "measurement": { ... },
        "published": True,
    }

@app.post("/ingest")
async def ingest():
    ...
    return _measurement_response(measurement)  # ← une seule source de vérité

@app.post("/simulate")
async def simulate(...):
    ...
    return _measurement_response(measurement)  # ← idem
```

---

## 4. Architecture avant / après

### Avant

```
iot-service/
  sensor_service.py   ← SensorMeasurement + IoTSensorSimulator (mélangés)
  hubeau_client.py    ← importe SensorMeasurement depuis sensor_service
  kafka_producer.py   ← MeasurementProducer (concret, pas d'interface)
  main.py             ← _poll_loop(kafka_producer: MeasurementProducer)

alert-service/
  models.py           ← Localisation + MeasurementLocalisation (dupliquées)
  kafka_producer.py   ← AlertProducer (concret, pas d'interface)
  kafka_consumer.py   ← producer: AlertProducer (dépend du concret)
```

### Après

```
iot-service/
  domain/
    models.py         ← SensorMeasurement (frozen dataclass, immuable)   ★ NOUVEAU
    ports.py          ← MeasurementWriter (ABC)                           ★ NOUVEAU
  sensor_service.py   ← Sensor (SRP — état capteur uniquement)            ✎ REFACTORISÉ
  hubeau_client.py    ← utilise Sensor en interne                         ✎ MIS À JOUR
  kafka_producer.py   ← MeasurementProducer(MeasurementWriter)            ✎ IMPLÉMENTE PORT
  main.py             ← _poll_loop(writer: MeasurementWriter) + DRY       ✎ MIS À JOUR

alert-service/
  ports.py            ← AlertSender (ABC)                                  ★ NOUVEAU
  models.py           ← MeasurementLocalisation supprimée (DRY)            ✎ MIS À JOUR
  kafka_producer.py   ← AlertProducer(AlertSender)                         ✎ IMPLÉMENTE PORT
  kafka_consumer.py   ← producer: AlertSender (DIP)                        ✎ MIS À JOUR
```

---

## 5. Tests

Tous les tests existants passent. Deux nouveaux cas de test ont été ajoutés pour couvrir les nouveaux comportements de `Sensor` :

| Fichier | Tests | Résultat |
|---|---|---|
| `iot-service/tests/test_hubeau_client.py` | 8 | ✅ PASS |
| `iot-service/tests/test_sensor_service.py` | 6 (dont 2 nouveaux) | ✅ PASS |
| `alert-service/tests/test_service.py` | 1 | ✅ PASS |
| `alert-service/tests/test_measurement_bridge.py` | 2 | ✅ PASS |

**Nouveaux tests ajoutés (`test_sensor_service.py`) :**

```python
def test_sensor_utilise_ses_metadonnees_par_defaut():
    # Vérifie que le Sensor injecte bien ses métadonnées dans la mesure

def test_capture_accepte_override_lat_lon():
    # Vérifie que les coordonnées GPS peuvent être surchargées (cas Hub'eau)
```

---

## 6. Tableau de synthèse

| Principe | Violation | Correction | Fichier(s) |
|---|---|---|---|
| **SRP** | Entité métier et simulateur mélangés | `SensorMeasurement` → `domain/models.py` | `sensor_service.py`, `domain/models.py` |
| **SRP** | Capteur sans état complet | `IoTSensorSimulator` → `Sensor` (dataclass) | `sensor_service.py` |
| **DIP** | `_poll_loop` dépend du concret Kafka | Interface `MeasurementWriter` + injection | `domain/ports.py`, `main.py` |
| **DIP** | `MeasurementConsumer` dépend du concret Kafka | Interface `AlertSender` + injection | `ports.py`, `kafka_consumer.py` |
| **DRY** | `Localisation` ≡ `MeasurementLocalisation` | Suppression du doublon | `models.py`, `test_measurement_bridge.py` |
| **DRY** | Dict réponse dupliqué × 2 | Fonction `_measurement_response()` | `main.py` |
| **OCP** | Chaînes `if/elif` par paramètre | *Non corrigé — itération suivante* | `service.py` |
