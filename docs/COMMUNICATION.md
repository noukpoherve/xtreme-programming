# Communication technique vs fonctionnelle

Exemples tirés du projet UrbanHub pour l'atelier 6.

---

## Exemple fonctionnel (métier / utilisateur)

> Lorsque la qualité de l'eau dépasse un seuil critique (pH ou turbidité), le système génère automatiquement une alerte et la rend visible pour les opérateurs via l'API Alert Service. Les capteurs en panne ou en maintenance ne peuvent plus publier de mesures tant qu'ils ne sont pas réactivés.

**Public** : responsable métier, élu, opérateur  
**Documents** : `README.md`, `RAPPORT_AMELIORATIONS.md`, `changelog.md`

---

## Exemple technique (développeur / architecture)

> Le `iot-service` publie des événements `mesure.qualite.eau` sur Kafka via `MeasurementProducer` (état `ProducerState.RUNNING`). Le `alert-service` consomme ce topic avec `KafkaAlertConsumer`, applique les règles `AlertRule` (Strategy), persiste via `AlertRepository` (Redis) et republie sur `alerte.pollution.detectee`. Les contrats sont définis en Pydantic v2 (`WaterMeasurementEvent`, `AlertPayload`).

**Public** : développeur, architecte, jury technique  
**Documents** : `CONTRATS_API.md`, `docs/REFACTOR_EXAMPLES.md`, Swagger `/docs`

---

## Tableau comparatif

| Aspect | Fonctionnel | Technique |
|--------|-------------|-----------|
| Vocabulaire | capteur, alerte, qualité de l'eau | Kafka, Pydantic, Repository, pytest |
| Objectif | valeur métier, cas d'usage | implémentation, intégration, tests |
| Format | prose, changelog, rapport | contrats JSON, code, OpenAPI |
| Exemple capteur | « le capteur est en maintenance » | `POST /sensors/{id}/maintenance` → `CapteurTransitionResponse` |

---

## Documentation auto-générée

| Type | Outil | Fichier / URL |
|------|-------|---------------|
| Changelog (obligatoire) | Keep a Changelog | `changelog.md` |
| API REST | FastAPI Swagger | `http://localhost:8000/docs`, `:8001/docs`, `:8002/docs` |
| Contrats formels | Pydantic + markdown | `CONTRATS_API.md` |
| Plateforme doc unifiée | Optionnel | non déployée (MkDocs/Sphinx possibles en extension) |
