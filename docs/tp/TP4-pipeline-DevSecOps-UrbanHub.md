# TP 4 — Pipeline DevSecOps UrbanHub

> **Cours** : DevSecOps & outils d'analyse de vulnérabilités
> **Chapitre** : 4 — Pipeline CI/CD durci
> **Durée prévue** : 1 h 30
> **Projet** : `urbanhub-water-quality`
> **Public** : débutant — chaque étape du pipeline est expliquée

---

## Ce que demande le TP 4 (énoncé officiel)

La Direction IT n’accepte la prod UrbanHub **que si** un pipeline CI/CD durci existe.

### 6 étapes obligatoires

| # | Étape | Gate attendu |
|---|---|---|
| 1 | Lint + tests unitaires (coverage ≥ 60 %) | Fail si lint/tests KO ou coverage < 60 % |
| 2 | SAST (Semgrep + Bandit) sortie SARIF | Fail sur findings HIGH/CRITICAL (config progressive possible) |
| 3 | SCA Trivy fs + secrets Gitleaks | **Fail** sur CRITICAL ou secret trouvé |
| 4 | Build Docker multi-stage + Trivy image | Image durcie (slim/distroless, USER non-root), **Fail** CRITICAL |
| 5 | Push registry + Cosign keyless + SBOM | Image signée + SBOM CycloneDX publié |
| 6 | Déploiement staging + smoke test | Healthcheck OK |

### Livrables

- Fichier pipeline `.github/workflows/*.yml`
- Dockerfile multi-stage durci
- Captures run vert / run rouge
- Evidence pack (SARIF, SBOM, log Cosign)
- README des gates

---

## Fichiers de ce projet liés au TP 4

| Fichier | Rôle |
|---|---|
| `.github/workflows/devsecops.yml` | Pipeline TP4 (6 étapes) |
| `alert-service/Dockerfile` | Image multi-stage non-root |
| `iot-service/Dockerfile` | Image multi-stage non-root |
| `docs/tp/TP4-pipeline-DevSecOps-UrbanHub.md` | Ce guide |
| `evidence/tp4/README.md` | Evidence pack + comment produire les preuves |
| `evidence/tp4/GATES.md` | Décisions de configuration des gates |

---

# Avant de coder : qu’est-ce qu’un pipeline « durci » ?

Un pipeline classique fait : `build → test → deploy`.

Un pipeline **DevSecOps** ajoute des **portails de sécurité (gates)** :

```text
commit
  → lint/tests
  → SAST (code)
  → SCA + secrets (dépendances + fuites)
  → build image
  → scan image
  → signer + SBOM
  → deploy staging + smoke
  → (prod seulement si tout est vert)
```

**Gate** = règle automatique :
si la condition échoue → le pipeline **rouge** → pas de merge / pas de deploy.

Anti-pattern du cours à éviter : `continue-on-error: true` partout (« sécu-théâtre »).

---

# Étape 1 — Lint + tests + coverage ≥ 60 %

## Pourquoi ?

Sans qualité de base, la sécurité est inutile : un code qui plante n’a pas besoin d’être « sécurisé », il doit d’abord marcher.

## Outils UrbanHub (Python)

| Outil | Rôle |
|---|---|
| **Ruff** | Lint ultra-rapide |
| **Black** | Format |
| **pytest** | Tests |
| **pytest-cov** | Coverage |

## Ce que fait le pipeline

```yaml
- run: uv run ruff check src/ tests/
- run: uv run pytest tests/ --cov=src --cov-fail-under=60
```

### Explication débutant

- `ruff check` : « y a-t-il des erreurs de style / bugs évidents ? »
- `--cov-fail-under=60` : « au moins 60 % du code est testé, sinon **fail** »

### Comment valider en local

```bash
cd alert-service && uv sync --all-groups && uv run pytest tests/ --cov=src --cov-fail-under=60
cd ../iot-service && uv sync --all-groups && uv run pytest tests/ --cov=src --cov-fail-under=60
```

---

# Étape 2 — SAST (Semgrep + Bandit) → SARIF

## Pourquoi ?

Le **SAST** lit le **code source** sans l’exécuter.
Il cherche des patterns dangereux (injections, `eval`, secrets hardcodés, etc.).

| Outil | Spécialité |
|---|---|
| **Bandit** | SAST Python (très adapté FastAPI) |
| **Semgrep** | SAST multi-langages + règles OWASP |

## Sortie SARIF

SARIF = format standard que GitHub Code Scanning comprend.
Ça permet d’afficher les failles **dans l’onglet Security** du dépôt.

### Commandes locales

```bash
# Bandit JSON/SARIF-like
uv run bandit -r alert-service/src iot-service/src -f json -o evidence/tp4/bandit.json

# Semgrep SARIF (via Docker)
docker run --rm -v "$PWD:/src" returntocorp/semgrep \
  semgrep --config=auto --sarif --output=/src/evidence/tp4/semgrep.sarif /src/alert-service /src/iot-service
```

### Gate pédagogique

- En rodage : warn
- En durci (TP4) : fail sur HIGH si politique « break-new »

Dans `devsecops.yml`, Bandit/Semgrep publient des artefacts ; le **blocage dur** est sur secrets + CVE CRITICAL (exigence explicite du cours).

---

# Étape 3 — SCA (Trivy fs) + Secrets (Gitleaks)

## 3.1 SCA = Software Composition Analysis

Trivy lit `uv.lock` / `package-lock.json` et compare aux CVE connues.

```bash
docker run --rm -v "$PWD:/src" aquasec/trivy \
  fs --severity CRITICAL --exit-code 1 \
  --scanners vuln /src/iot-service /src/alert-service
```

- `--severity CRITICAL` : on regarde les plus graves
- `--exit-code 1` : **fail** si trouvé → c’est le gate

## 3.2 Secrets = Gitleaks

Cherche clés API, tokens, mots de passe commités.

```bash
docker run --rm -v "$PWD:/src" zricethezav/gitleaks:latest \
  detect --source /src --no-banner
```

**Règle cours** : 1 secret trouvé = pipeline rouge. Aucune négociation.

---

# Étape 4 — Build Docker multi-stage + scan image

## 4.1 Pourquoi multi-stage ?

| Stage | Rôle |
|---|---|
| `builder` | Installe les deps, compile si besoin |
| `runtime` | Ne garde **que** le nécessaire pour tourner |

Résultat : image plus petite, moins de CVE OS, surface d’attaque réduite.

## 4.2 Durcissement demandé

| Exigence | Implémentation UrbanHub |
|---|---|
| Multi-stage | ✅ `builder` + `runtime` |
| Base minimale | ✅ `python:3.13-slim` (pragmatique ; distroless possible en bonus) |
| USER non-root | ✅ `USER appuser` (uid 10001) |
| Pas de secrets dans l’image | ✅ variables d’env au runtime |
| Scan Trivy image | ✅ gate CRITICAL |

### Exemple de logique Dockerfile

```dockerfile
FROM python:3.13-slim AS builder
# install deps...

FROM python:3.13-slim AS runtime
RUN useradd -u 10001 -m appuser
COPY --from=builder /app /app
USER appuser
CMD ["uvicorn", "..."]
```

## 4.3 Scan image

```bash
docker build -t urbanhub/iot-service:local ./iot-service
docker run --rm aquasec/trivy image --severity CRITICAL --exit-code 1 urbanhub/iot-service:local
```

---

# Étape 5 — Push registry + Cosign + SBOM

## 5.1 Push (GHCR)

GHCR = GitHub Container Registry (`ghcr.io/org/image:tag`).

Le pipeline pousse uniquement si les jobs sécurité sont OK.

## 5.2 Signature Cosign keyless

**Cosign** signe l’image.
**Keyless** = pas de clé privée à stocker : identité OIDC GitHub Actions.

But : en prod, n’accepter **que** les images signées par ton pipeline.

```bash
# Exemple conceptuel (fait dans GitHub Actions)
cosign sign --yes ghcr.io/OWNER/urbanhub-iot-service:TAG
```

## 5.3 SBOM à chaque build

```bash
trivy image --format cyclonedx -o sbom.json urbanhub/iot-service:TAG
```

Lien avec TP3 : le SBOM n’est plus un fichier « une fois », il devient un **artefact de pipeline**.

---

# Étape 6 — Déploiement staging + smoke test

## Staging local (docker-compose)

```bash
docker compose up -d --build
curl -f http://localhost:8000/health   # alert-service
curl -f http://localhost:8001/health   # iot-service
```

Si le healthcheck échoue → pipeline rouge → pas de promotion prod.

### Option AWS Academy (bonus cours)

Push ECR via OIDC + deploy ECS + smoke sur l’ALB.

---

# Bonus (+2 pts) — DAST OWASP ZAP

Une fois staging UP :

```bash
docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
  -t http://host.docker.internal:8000 -r evidence/tp4/zap-report.html
```

Gate : fail si finding HIGH (profil baseline CI).

---

## Comment produire un run rouge (exigence du cours)

Le cours demande **1 run vert** + **1 run rouge volontaire**.

Méthode simple et pédagogique :

1. Créer une branche `demo-fail-cve`
2. Dans le workflow, baisser temporairement le seuil à `HIGH` **ou** ajouter une dépendance volontairement vulnérable
3. Pousser → le job Trivy échoue → capture d’écran
4. Revenir en arrière / fermer la PR

Alternative secrets :

1. Ajouter un faux token dans un fichier (ex. `AKIA...` AWS-like) **uniquement** sur une branche jetable
2. Gitleaks échoue
3. Supprimer immédiatement

⚠️ Ne jamais pousser un **vrai** secret.

---

## Evidence pack — où mettre les preuves

Voir `evidence/tp4/README.md` :

```text
evidence/tp4/
  README.md
  GATES.md
  bandit.sarif / bandit.json
  semgrep.sarif
  trivy-fs.json
  trivy-image.json
  gitleaks.sarif
  sbom-iot.json
  sbom-alert.json
  cosign-verify.txt
  captures/   # screenshots run vert / run rouge
```

---

## Grille d’évaluation (rappel cours)

| Critère | Points |
|---|---|
| Pipeline exécute les 6 étapes | 5 |
| Gates bloquants (secrets, CVE crit) | 3 |
| Dockerfile durci | 3 |
| Cosign + SBOM | 3 |
| Gestion secrets (GH Secrets / OIDC) | 2 |
| Evidence pack | 2 |
| Documentation README | 2 |
| Bonus DAST / OIDC AWS / Falco | +2 |

---

## Mini-parcours débutant « je valide mon TP 4 »

1. Lire `evidence/tp4/GATES.md` (comprendre ce qui bloque)
2. Lancer tests locaux (étape 1)
3. Lancer Bandit + Trivy + Gitleaks en local (étapes 2–3)
4. `docker build` les 2 services (étape 4)
5. Pousser la branche → vérifier Actions `DevSecOps Pipeline`
6. Télécharger les artefacts = evidence pack
7. Remplir `evidence/tp4/captures/` avec 2 screenshots

---

## Lien avec le TP 3

| TP 3 | TP 4 |
|---|---|
| On **trie** les CVE à la main | On **bloque** automatiquement les pires |
| On produit un SBOM ponctuel | On produit un SBOM **à chaque build** |
| Plan de remédiation humain | Gate CI = politique exécutable |

👉 Revenir au TP 3 : [`TP3-gestion-vulnerabilites-UrbanHub.md`](./TP3-gestion-vulnerabilites-UrbanHub.md)
