# Collection Postman — UrbanHub

## Import

1. Ouvrir Postman
2. **Import** → sélectionner `UrbanHub.postman_collection.json`
3. Vérifier les variables de collection :
   - `alert_base` = `http://localhost:8000`
   - `iot_base` = `http://localhost:8001`
   - `supervision_base` = `http://localhost:8002`

## Prérequis

```bash
docker compose up -d
```

Ou lancer les services localement sur les ports indiqués.

## Scénario de démonstration (évaluation)

1. **Alert Service** → `Health` puis `Create Alert` puis `List Alerts`
2. **IoT Service** → `Register Sensor` → `Simulate Measurement` → `Put Sensor In Maintenance` → `Activate Sensor`
3. **Supervision Service** → `Health` → `Dashboard Resume` → `Dashboard Carte`

## Captures d'écran attendues

Pour le livrable évaluation, exporter des captures Postman montrant :

- statut `200 OK` sur les requêtes CRUD
- le corps JSON de réponse (alertes, capteurs, dashboard)
- la transition d'état capteur (`maintenance` → `actif`)

Conseil : créer un dossier `docs/postman/screenshots/` et y déposer les PNG après exécution manuelle.

## Captures à réaliser (manuel)

| Fichier suggéré | Requête Postman | Ce qu'il faut montrer |
|-----------------|-----------------|------------------------|
| `01-alert-health.png` | Alert → Health | Statut `200 OK` |
| `02-alert-create-list.png` | Create Alert + List Alerts | Corps JSON alerte |
| `03-iot-register-simulate.png` | Register Sensor + Simulate | Mesure publiée |
| `04-iot-state-transition.png` | Maintenance → Activer | Transition d'état capteur |
| `05-supervision-dashboard.png` | Dashboard Resume + Carte | JSON tableau de bord |

Déposer les fichiers dans `docs/postman/screenshots/` puis committer avec un message du type `docs: add Postman screenshots`.
