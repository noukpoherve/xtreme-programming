# Rapport de tests — EC03 · `iot-service`

> Exporter en PDF (`03_rapport_tests.pdf`) pour le ZIP final.  
> **Anonymat** : ne pas coller de chemins absolus ni d’URL de compte personnel dans les logs.

## 1. Périmètre

- Microservice : **iot-service** (FastAPI)
- Outil : **pytest** + **pytest-cov**
- Emplacement des tests source : `iot-service/tests/`

## 2. Tests unitaires et d’intégration

| Fichier | Type | Description |
|---------|------|-------------|
| `test_station_mapping.py` | Unitaire | Mapping Hub'Eau, unicité des capteurs |
| `test_api_gateway.py` | Unitaire | POST metrics, capteur inconnu |
| `test_hubeau_qualite_client.py` | Unitaire | Client Hub'Eau (mock HTTP) |

*(Compléter après exécution du pipeline avec le nombre de tests et le statut.)*

```text
# Coller ici la sortie pytest -v (pipeline au vert)
```

## 3. Test non fonctionnel

*(À ajouter à l’étape 3 — ex. temps de réponse `/health` < seuil, ou robustesse valeurs extrêmes.)*

| Critère | Seuil | Résultat |
|---------|-------|----------|
| *(ex. latence /health)* | *(ex. < 500 ms)* | *(à mesurer)* |

## 4. Couverture (pytest-cov)

| Métrique | Valeur |
|----------|--------|
| Couverture `src/` | *(à remplir)* |
| Seuil pipeline | *(ex. ≥ 60 % si gate EC03)* |

```text
# Coller ici pytest --cov=src --cov-report=term-missing
```

## 5. Preuve pipeline complet au vert

*(Capture ou extrait de log GitHub Actions / exécution locale après étape 3.)*

- Date d’exécution : *(UTC, sans identifiant personnel)*
- Commit / tag : *(hash anonymisé ou libellé générique)*
- Durée totale : *(objectif lint+unitaires ≤ 10 min)*
