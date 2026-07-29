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
├── 00_extraits_code/ ← domaine, API, tests (iot-service)
├── 01_pipeline.yml ← pipeline 6 étapes (étape 3 — en cours)
├── 02_scripts/ ← smoke / scans (complété avec le pipeline)
├── 03_rapport_tests.md ← preuves tests + coverage (à finaliser après pipeline vert)
├── 04_analyse_qualite_securite.md
└── README.md ← ce fichier (+ section IA)
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
| Antigravity (agent AI) | Rédaction et débogage du pipeline YAML 6 étapes, création du test non fonctionnel, correction des gates DevSecOps (Bandit/Trivy) et audit d'anonymisation |
| ChatGPT / Claude | Assistance à la vérification des règles de conformité et syntaxe Gitleaks / Trivy |

### Périmètre d’utilisation

- Analyse de conformité par rapport à l'énoncé EC03 (6 étapes, livrables ZIP).
- Choix et justification du microservice `iot-service`.
- Rédaction de la structure `EC03_P1_NomPrenom_UrbanHub_CICD/` et des modèles de rapports.
- Écriture de la chaîne CI/CD bloquante `01_pipeline.yml` (INSTALL → TEST → QUALITY → SECURITY → BUILD → DEPLOY).
- Création du test non fonctionnel `iot-service/tests/test_non_functionnel.py` (SLA latence `/health` ≤ 500 ms + validation Pydantic).
- Écriture du script Bash de smoke test `02_scripts/smoke_test.sh` et d'exécution locale `run_local_pipeline.sh`.
- Remédiation sécurité et résolution des erreurs de tags GitHub Actions (Bandit `# nosec B310`, Trivy-action).

### Prompts majeurs

1. *« Examiner tout mon projet et donner les étapes à suivre pour l'épreuve EC03. »*
2. *« Configurer le pipeline CI/CD bloquant en 6 étapes (INSTALL -> TEST -> QUALITY -> SECURITY -> BUILD -> DEPLOY) pour iot-service. »*
3. *« Ajouter des tests non fonctionnels pour mesurer le temps de réponse de /health et valider le rejet des valeurs métriques aberrantes. »*
4. *« Auditer l'anonymat dans tout le dossier EC03, supprimer les chemins locaux et compléter les rapports 03 et 04 avec les preuves d'exécution. »*

### Audit et justification

- **Microservice** : proposition IA = `iot-service` pour deploy/smoke plus simple ; validé car aligné fil rouge eau + API testable sans stack complète.
- **Pipeline CI/CD** : L'IA proposait initialement `aquasecurity/trivy-action@0.28.0`. Lors de l'exécution, GitHub Actions a rejeté l'action en raison d'un tag sans préfixe `v`. Après audit des logs de la CI, l'action a été basculée vers `aquasecurity/trivy-action@master` pour garantir une résolution valide des dépendances internes sur les runners GitHub.
- **Sécurité (Bandit)** : L'IA a révélé une alerte Medium `B310` sur `urllib.request.urlopen`. Après revue manuelle du code dans `hubeau_qualite_client.py`, nous avons confirmé que l'URL est construite de façon sécurisée à partir d'une constante d'API fixe (`_BASE_URL`). Le tag `# nosec B310` a donc été appliqué pour éliminer le faux positif sans compromettre la sécurité.
- **Anonymat** : Les logs locaux contenant des chemins absolus Windows (ex: `D:\...`) ont été nettoyés et anonymisés avec des chemins relatifs avant leur intégration finale dans les rapports.
- **Image non-root** : L'IA a généré l'étape d'inspection Docker `docker inspect --format='{{.Config.User}}'`, ce qui a permis de valider formellement le respect de la consigne d'exécution sous un utilisateur non-root.

---

## État des livrables

| Livrable | Fichier | Statut |
|----------|---------|--------|
| Code source | `00_extraits_code/` | Complet |
| Pipeline CI/CD | `01_pipeline.yml` & `.github/workflows/ec03-iot-service.yml` | 6/6 étapes OK (Bloquant) |
| Scripts locaux | `02_scripts/` (`run_local_pipeline.sh`, `smoke_test.sh`) | Opérationnels |
| Rapport de tests | `03_rapport_tests.md` | Complété + anonymisé |
| Rapport Qualité & Sécurité | `04_analyse_qualite_securite.md` | Complété + anonymisé |
| Notice & IA | `README.md` | Conforme |

