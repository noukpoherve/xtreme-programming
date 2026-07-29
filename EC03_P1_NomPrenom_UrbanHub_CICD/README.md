# EC03 — Partie 1 · UrbanHub · CI/CD local

Archive de rendu pour l’industrialisation du microservice **Python FastAPI** du fil rouge **UrbanHub** (Smart City — **qualité de l’eau**).

> **Anonymat** : le dossier ZIP final doit s’appeler `EC03_P1_NomPrenom_UrbanHub_CICD.zip` avec le nom/prénom fourni par le centre. Aucun identifiant personnel ne doit figurer dans les fichiers du ZIP (voir [Règles de conformité](#règles-de-conformité)).

---

## Microservice retenu (étape 1)

| Critère | Décision |
|--------|----------|
| **Service** | `iot-service` |
| **Rôle** | Ingestion qualité de l’eau : passerelle HTTP, simulateur local, poll Hub'Eau, publication Kafka |
| **Stack** | FastAPI, Pydantic, aiokafka, `uv` + `uv.lock` (install déterministe, équivalent lockfile / `poetry install`) |
| **Périmètre EC03** | **Un seul** microservice Python ; `alert-service` et `dashboard` restent hors archive EC03 (monorepo source uniquement) |

**Pourquoi `iot-service` et pas `alert-service` ?**

- Correspond au domaine **qualité de l’eau** (fil rouge).
- API REST claire (`/health`, `POST /api/sensors/{id}/metrics`) pour tests et smoke tests.
- Déploiement local plus simple pour l’étape **DEPLOY** (`docker run` sans Postgres obligatoire pour un smoke minimal sur `/health`).
- Le code source complet vit dans `iot-service/` du dépôt ; les extraits de démonstration sont dans `00_extraits_code/`.

---

## Arborescence de rendu (étape 2)

```text
EC03_P1_NomPrenom_UrbanHub_CICD/
├── 00_extraits_code/          ← domaine, API, tests (iot-service)
├── 01_pipeline.yml            ← pipeline 6 étapes (étape 3 — en cours)
├── 02_scripts/                ← smoke / scans (complété avec le pipeline)
├── 03_rapport_tests.md        ← preuves tests + coverage (à finaliser après pipeline vert)
├── 04_analyse_qualite_securite.md
└── README.md                    ← ce fichier (+ section IA)
```

Les versions PDF (`03_*.pdf`, `04_*.pdf`) seront générées à partir des `.md` avant envoi du ZIP.

---

## Règles de conformité

Checklist à respecter **dans tout le contenu du ZIP** (code, YAML, logs collés, captures).

| Règle | Application |
|-------|-------------|
| **Anonymat strict** | Pas de nom, prénom, e-mail, identifiant GitHub, URL de repo personnel, ni chemin absolu (`C:\...`, `/Users/...`). Utiliser `NomPrenom`, `registry.example.com`, `localhost`. |
| **Secrets** | Aucune clé API ou mot de passe en clair. Variables via `${{ secrets.* }}` ou `.env` **exclu** du ZIP. Vérifier avec Gitleaks avant rendu. |
| **Feedback rapide** | Lint + tests unitaires du **seul** `iot-service` ciblés **≤ 10 min** (matrice réduite, pas de build dashboard dans le pipeline EC03). |
| **Preuve d’exécution** | Logs ou capture d’un **pipeline complet au vert** à intégrer dans `03_rapport_tests.md` (étape après `01_pipeline.yml`). |
| **Pipeline bloquant** | Si une étape échoue, les suivantes ne s’exécutent pas (`needs:` + `fail-fast` / exit code non nul). |

### Contrôle avant zip

1. Rechercher dans le dossier EC03 : `@`, `github.com/`, `\Users\`, `D:\`, adresses e-mail.
2. Relire `01_pipeline.yml` et les scripts : pas de token en dur.
3. Exporter les PDF sans métadonnées personnelles (auteur générique si possible).

---

## Lien avec le dépôt source

- Service canonique : répertoire `iot-service/` (Dockerfile multi-stage, non-root, tests sous `iot-service/tests/`)
- Les fichiers sous `00_extraits_code/` sont des **copies pédagogiques** ; en cas d’écart, la source dans `iot-service/` fait foi.

---

## Section IA (obligatoire)

### Outils IA et plateformes

| Outil | Usage |
|-------|--------|
| Cursor (agent Composer) | Audit EC03 vs dépôt existant, structuration du dossier de rendu, rédaction des squelettes README / rapports |
| *(À compléter)* | Ex. Copilot, ChatGPT web, etc. si utilisés pour le pipeline ou les tests |

### Périmètre d’utilisation

- Analyse de conformité par rapport à l’énoncé EC03 (6 étapes, livrables ZIP).
- Choix et justification du microservice `iot-service`.
- Rédaction de la structure `EC03_P1_NomPrenom_UrbanHub_CICD/` et des modèles de rapports.
- *(À compléter après étape 3)* : syntaxe YAML du pipeline, test non fonctionnel, script smoke.

### Prompts majeurs

1. *« Examiner le repo, vérifier qu’il est à jour, créer la branche hans-kemka »*
2. *« Analyser le cahier des charges EC03 (pipeline, livrables, IA, anonymat) et faire un retour fait / à faire »*
3. *« Se concentrer sur les étapes 1 et 2 et les règles, puis préparer l’étape 3 (pipeline) »*

*(Ajouter ici les prompts exacts utilisés pour le pipeline et les tests.)*

### Audit et justification

- **Microservice** : proposition IA = `iot-service` pour deploy/smoke plus simple ; validé car aligné fil rouge eau + API testable sans stack complète.
- **Extraits** : reprise manuelle de fichiers existants déjà revus en cours ; pas de génération de logique métier par l’IA dans cette phase.
- **Anonymat** : les chemins personnels repérés ailleurs dans le monorepo (`evidence/GUIDE-CAPTURES.md`, etc.) **ne doivent pas** être recopiés dans ce dossier EC03.
- **Pipeline (à venir)** : chaque étape YAML et script smoke sera relu (gates sécurité, `USER` non-root Docker, absence de `|| true` sur les jobs bloquants) avant validation.

---

## Prochaine étape (3)

Rédiger `01_pipeline.yml` : **INSTALL → TEST → QUALITY → SECURITY → BUILD → DEPLOY** (100 % bloquant, cible `iot-service` uniquement).
