# Scripts EC03

Scripts prévus avec l’étape 3 (`01_pipeline.yml`) :

| Script | Rôle |
|--------|------|
| `smoke_test.sh` | Après `docker run` : vérifie `/health` (HTTP 200, JSON `status`) |
| *(optionnel)* `run_local_pipeline.sh` | Enchaînement local des mêmes étapes que le CI (hors GitHub) |

Contraintes :

- Chemins **relatifs** uniquement (pas de `C:\...` / `/Users/...`).
- Pas de secrets en argument en clair ; variables d’environnement documentées dans le README racine du ZIP.
