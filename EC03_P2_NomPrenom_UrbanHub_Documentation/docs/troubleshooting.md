# 🛠️ Guide de Dépannage (Troubleshooting)

> **Objectif** : Fournir aux équipes de développement et d'exploitation une matrice de résolution rapide des 5 incidents les plus fréquents sur le microservice `iot-service`.

---

## 📋 Matrice des Incidents Courants

| # | Incident | Symptôme | Cause Racine Probable | Procédure de Résolution |
|---|----------|----------|----------------------|-------------------------|
| **1** | **Port 8001 Déjà Alloué** | Error `[Errno 98] Address already in use` au lancement. | Un processus Uvicorn ou un autre conteneur occupe le port 8001. | Identifier et stopper le processus occupant le port 8001, ou modifier le port via `--port 8002`. |
| **2** | **Rejet de Validation Pydantic (HTTP 422)** | L'API retourne `422 Unprocessable Entity` lors d'un `POST /metrics`. | Les métriques soumises dépassent les bornes valides (ex. pH > 14 ou turbidité < 0). | Corriger le payload JSON envoyé pour respecter le schéma `SensorMetricsInput` (ex. 0 ≤ pH ≤ 14). |
| **3** | **Timeout lors de l'Ingestion Hub'Eau** | Logs `WARNING: Hub'Eau quality fetch timed out (15.0s)`. | Indisponibilité temporaire ou lenteur de l'API gouvernementale Hub'Eau. | Aucune action requise. L'adapter `HubEauQualiteClient` gère le timeout en parallèle et réessaie au cycle suivant (6h). |
| **4** | **Échec de Build Docker Non-Root** | Le Job `BUILD` de la CI échoue sur l'assertion `test "$USER" != "root"`. | La directive `USER appuser` est manquante ou mal positionnée dans le Dockerfile. | Vérifier que `USER appuser` est bien déclaré à la fin du stage final de production dans `Dockerfile`. |
| **5** | **Erreur de Tag Action GitHub (Trivy)** | Échec du Job `SECURITY` avec `Unable to resolve action`. | Le tag utilisé dans la GitHub Action est mal formaté (ex. `0.28.0` au lieu de `@master` ou `v0.28.0`). | Remplacer `uses: aquasecurity/trivy-action@0.28.0` par `uses: aquasecurity/trivy-action@master` dans le fichier YAML. |

---

## 🔍 Procédures Détaillées de Diagnostic

### Incident 1 : Résolution d'un Port 8001 Conflit

Si le serveur refuse de démarrer avec l'erreur `Address already in use` :

```bash
# 1. Repérer le PID occupant le port 8001 (Linux / macOS)
lsof -i :8001  # ou netstat -ano | findstr 8001 sur Windows

# 2. Stopper le processus
kill -9 <PID>

# 3. Si l'occupation provient d'un ancien conteneur Docker
docker rm -f ec03-iot-smoke ec03-iot-app 2>/dev/null || true
```

---

### Incident 2 : Diagnostic des Erreurs de Validation HTTP 422

Lorsqu'un client reçoit une réponse `HTTP 422`, l'API retourne un champ `details` indiquant le composant invalide :

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
    "trace_id": "req-123456"
  }
}
```

**Action** : Consulter le schéma de référence [Reference API](reference.md#2-post-apisensorssensor_idmetrics-ingestion-de-mesures-physiques) et corriger la valeur soumise.

---

### Incident 3 : Vérification de la Connexion au Broker Kafka

Si les événements ne sont pas reçus par Kafka :

```bash
# 1. Vérifier la santé du broker Kafka
docker compose exec kafka kafka-topics.sh --bootstrap-server localhost:9092 --list

# 2. Vérifier la présence du topic de qualité de l'eau
# Output attendu: mesure.qualite.eau

# 3. Écouter en direct les messages publiés sur le topic
docker compose exec kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic mesure.qualite.eau \
  --from-beginning
```
