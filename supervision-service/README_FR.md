# Service de Supervision IRVE

Service de **supervision en temps réel** des bornes de recharge électriques (IRVE) pour la plateforme UrbanHub.

## 🎯 Responsabilités

- **Consommer des événements OCPP** depuis le topic Kafka `charge.station.events`
- **Maintenir l'état en temps réel** de toutes les bornes et sessions en cache mémoire
- **Exposer des APIs REST** pour le tableau de bord et les applications tierces
- **Diffuser les mises à jour en temps réel** via WebSocket aux clients connectés
- **Détecter les incidents** et alertes (déconnexions, défaillances, anomalies)

## 📦 Structure du projet

```
supervision-service/
├── src/
│   └── supervision_service/
│       ├── __init__.py           # Package principal
│       ├── main.py               # Point d'entrée FastAPI
│       ├── contrats.py           # Modèles Pydantic (API contracts)
│       ├── gestion_etat.py       # Gestionnaire d'état en mémoire
│       ├── consommateur_kafka.py # Consumer Kafka pour OCPP
│       └── api.py                # Endpoints REST et WebSocket
├── tests/
│   └── test_*.py                 # Tests unitaires
├── requirements.txt              # Dépendances Python
├── Dockerfile                    # Image Docker
└── README_FR.md                  # Cette documentation
```

## 🚀 Démarrage rapide

### Prérequis

- Python 3.12+
- Kafka (accessible sur `localhost:9092`)
- pip

### Installation locale

```bash
cd supervision-service

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Démarrer le service
python -m uvicorn src.supervision_service.main:app --host 0.0.0.0 --port 8002 --reload
```

Le service est alors accessible à: **http://localhost:8002**

### Avec Docker

```bash
# Construire l'image
docker build -t supervision-service:latest .

# Lancer le conteneur
docker run -p 8002:8002 \
  -e KAFKA_SERVERS=kafka:9092 \
  supervision-service:latest
```

## 📡 API Endpoints

### Bornes (Charging Stations)

#### `GET /bornes`
Liste toutes les bornes avec filtres optionnels.

**Query Parameters:**
- `etat` (optional): Filtrer par état (disponible, reservee, en_charge, maintenance, hors_service)
- `limit` (default: 100): Nombre maximum de résultats

**Réponse:**
```json
[
  {
    "id": "FR-SOLAGNE-0001",
    "nom": "Square République",
    "adresse": "Place de la République, 41200 Sologne",
    "latitude": 47.5412,
    "longitude": 1.2345,
    "etat": "disponible",
    "sante": "ok",
    "connecteurs": [...],
    "nombre_connecteurs": 2,
    "sessions_actives": []
  }
]
```

#### `GET /bornes/{borne_id}`
Récupère les détails d'une borne spécifique.

**Exemple:**
```bash
curl http://localhost:8002/bornes/FR-SOLAGNE-0001
```

### Sessions de charge

#### `GET /sessions`
Liste les sessions de charge avec filtres.

**Query Parameters:**
- `etat` (optional): Filtrer par état (initiee, authentifiee, en_cours, terminee, facturee, echec)
- `borne_id` (optional): Filtrer par borne
- `limit` (default: 50)

#### `GET /sessions/{session_id}`
Détails d'une session.

### Tableau de bord

#### `GET /tableau-de-bord/resume`
Résumé temps réel de l'état du réseau.

**Réponse:**
```json
{
  "timestamp": "2025-01-20T14:30:00Z",
  "nombre_bornes_total": 50,
  "bornes_disponibles": 35,
  "bornes_reservees": 5,
  "bornes_en_charge": 8,
  "bornes_maintenance": 2,
  "sessions_actives": 8,
  "energie_total_kwh": 156.3,
  "chiffre_affaires_eur": 234.50,
  "nombre_incidents": 1,
  "sante_reseau": 96.0
}
```

#### `GET /tableau-de-bord/carte`
Positions et états des bornes pour affichage sur une carte.

```json
{
  "timestamp": "2025-01-20T14:30:00Z",
  "bornes": [
    {
      "id": "FR-SOLAGNE-0001",
      "nom": "Square République",
      "latitude": 47.5412,
      "longitude": 1.2345,
      "etat": "en_charge",
      "sante": "ok",
      "connecteurs_total": 2,
      "connecteurs_libres": 1,
      "sessions_actives": 1
    }
  ]
}
```

### Incidents

#### `GET /incidents`
Liste les incidents récents (limité à 20 par défaut).

**Query Parameters:**
- `limit` (default: 20)

### Santé & Métriques

#### `GET /sante`
Endpoint de healthcheck pour les orchestrateurs.

```json
{
  "statut": "sain",
  "timestamp": "2025-01-20T14:30:00Z",
  "bornes_chargees": true,
  "nombre_bornes": 50
}
```

#### `GET /metriques`
Toutes les métriques du réseau.

## 🔌 WebSocket

### Connexion

**Endpoint:** `ws://localhost:8002/ws/supervision/direct`

### Utilisation (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8002/ws/supervision/direct');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`Changement: ${message.type}`, message.donnees);
  
  // Types d'événements:
  // - borne_ajoutee
  // - etat_borne_change
  // - session_ajoutee
  // - session_terminee
  // - incident_detecte
};

// Garder la connection vivante (ping/pong)
setInterval(() => {
  ws.send('ping');
}, 30000);
```

## 🔄 Événements Kafka

### Topic consommé: `charge.station.events`

**Format des messages:**

```json
{
  "type_evenement": "borne_status_changed",
  "borne_id": "FR-SOLAGNE-0001",
  "connecteur_id": "CONN-001",
  "nouvel_etat": "charging",
  "ancien_etat": "available",
  "timestamp": "2025-01-20T14:23:45Z",
  "session_id": "SESSION-12345"
}
```

**Types d'événements supportés:**
- `borne_status_changed` → Changement d'état d'une borne
- `session_started` → Début d'une session de charge
- `session_ended` → Fin d'une session
- `borne_health_degraded` → Santé dégradée

## 🏗️ Architecture interne

### Gestionnaire d'état (gestion_etat.py)

Classe `GestionnaireEtat` qui maintient:
- **Bornes**: Dictionnaire en mémoire de tous les états de bornes
- **Sessions**: État de toutes les sessions actives/terminées
- **Incidents**: Enregistrement des incidents
- **Listeners**: Système d'observation pour notifier les changements

```python
gestionnaire = GestionnaireEtat()
gestionnaire.ajouter_borne(borne)
gestionnaire.mettre_a_jour_etat_borne("FR-SOLAGNE-0001", "charging")
```

### Consumer Kafka (consommateur_kafka.py)

Classe `ConsommateurEvenementsBorne` qui:
- Se connecte au cluster Kafka
- Consomme les événements du topic `charge.station.events`
- Traite chaque événement
- Met à jour le `GestionnaireEtat`

```python
consumer = ConsommateurEvenementsBorne(
    serveurs_kafka=["kafka:9092"],
    gestionnaire_etat=gestionnaire
)
consumer.demarrer()
consumer.consommer_boucle()  # Boucle infinie
```

### API (api.py)

Endpoints FastAPI utilisant le `GestionnaireEtat`:
- Endpoints REST pour interroger l'état
- Endpoints WebSocket pour les mises à jour temps réel
- Gestion centralisée des erreurs

## 🧪 Tests

```bash
# Lancer les tests
pytest tests/ -v

# Avec couverture de code
pytest tests/ --cov=supervision_service --cov-report=html
```

## 📊 Modèles de données

Voir `contrats.py` pour la définition complète de:

- `BorneRecharge`: État d'une borne de recharge
- `SessionCharge`: État d'une session de charge
- `Connecteur`: État d'un connecteur individuel
- `ResumeDashboard`: Résumé agrégé du réseau
- `Incident`: Enregistrement d'incident
- `EvenementBorne`: Événement OCPP reçu

Tous utilisen **Pydantic v2** avec `ConfigDict` pour la validation et sérialisation.

## 🔐 Sécurité

### À implémenter

- [ ] Authentification API (JWT ou OAuth2)
- [ ] Rate limiting par utilisateur/IP
- [ ] Validation stricte des inputs Pydantic
- [ ] Logs d'accès centralisés
- [ ] Chiffrement des données sensibles en transit (TLS)
- [ ] CORS restrictif

## 📈 Observabilité

### Logs structurés

```python
import logging
logger = logging.getLogger(__name__)
logger.info("Borne mise à jour", extra={
    "borne_id": "FR-SOLAGNE-0001",
    "ancien_etat": "disponible",
    "nouvel_etat": "en_charge"
})
```

### Métriques Prometheus (à implémenter)

```python
from prometheus_client import Counter, Histogram

sessions_counter = Counter('sessions_demarrees_total', 'Total sessions started')
latence_api = Histogram('api_latency_seconds', 'API request latency')
```

### Traces distribuées (à implémenter)

Utiliser OpenTelemetry pour les traces cross-services.

## 🚦 Statuts et codes d'erreur

### États de borne
- `disponible`: Prête à la charge
- `reservee`: Réservée par un utilisateur
- `en_charge`: Charge en cours
- `maintenance`: Maintenance programmée
- `hors_service`: Hors service temporaire

### États de session
- `initiee`: Session créée
- `authentifiee`: Paiement autorisé
- `en_cours`: Charge en cours
- `terminee`: Charge stoppée
- `facturee`: Paiement débité
- `echec`: Erreur pendant la charge

### Codes d'erreur HTTP
- `200`: OK
- `404`: Ressource non trouvée (borne, session, etc.)
- `400`: Requête invalide
- `500`: Erreur serveur

## 🔗 Intégration avec UrbanHub

Le Service de Supervision s'intègre à:

1. **Event Bus (Kafka)**
   - Consomme: `charge.station.events`
   - Pourrait publier: `charge.supervision.status_change` (si nécessaire)

2. **Data Warehouse**
   - Pourait synchroniser l'historique des sessions pour l'analytique

3. **API Gateway**
   - Le Service de Supervision devrait être derrière l'API Gateway pour:
     - Authentification centralisée
     - Rate limiting
     - Routing

4. **Autres services IRVE** (à venir)
   - Service Réservation
   - Service Paiement
   - Service Énergie
   - Service Incidents

## 📝 Variables d'environnement

```bash
KAFKA_SERVERS=kafka:9092           # Serveurs Kafka (comma-separated)
KAFKA_GROUP=supervision-service    # Groupe de consumer Kafka
SERVICE_PORT=8002                  # Port du service
LOG_LEVEL=INFO                     # Niveau de logging
```

## 🐛 Dépannage

### "Impossible de se connecter à Kafka"
```bash
# Vérifier que Kafka est en cours d'exécution
docker-compose ps

# Vérifier la connectivité
telnet localhost 9092
```

### "Aucun événement reçu"
```bash
# Vérifier les topics Kafka
kafka-topics --bootstrap-server localhost:9092 --list

# Vérifier les messages dans le topic
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic charge.station.events --from-beginning
```

### "WebSocket disconnecte immédiatement"
- Vérifier les logs du serveur
- Vérifier la connectivité réseau
- Essayer avec `wscat` pour debug

```bash
npm install -g wscat
wscat -c ws://localhost:8002/ws/supervision/direct
```

## 📚 Références

- [EC02 Architecture Document](../EC02_ANALYSIS_AND_PLAN.md)
- [OCPP Specification](https://www.openchargealliance.org/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Kafka Documentation](https://kafka.apache.org/documentation/)

## 📄 License

Confidentiel EADL - RNCP39765

---

**Version:** 0.1.0  
**Dernier mise à jour:** Janvier 2025
