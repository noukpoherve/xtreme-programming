# TP 4 — Pipeline CI/CD DevSecOps UrbanHub

> **Objectif du cours** : transformer la politique sécurité en **automatisme bloquant** dans la CI/CD.
> **Livrables** : workflow `.yml` · Dockerfiles durcis · evidence pack · captures run vert / rouge.

---

## 1. Quels problèmes essayons-nous de résoudre ?

Même avec un bon triage (TP3), sans pipeline les problèmes suivants restent :

| # | Problème | Ce qui se passe sans TP4 |
|---|---|---|
| P1 | Un secret est re-commité demain | Personne ne s’en aperçoit avant l’incident |
| P2 | Une CVE CRITICAL revient | Merge puis prod avec la faille |
| P3 | Image Docker tournant en **root** | Escalade plus facile si le conteneur est compromis |
| P4 | Pas de preuve de provenance | On ne sait pas si l’image vient bien de notre CI |
| P5 | Deploy sans smoke test | Staging cassé découvert trop tard |
| P6 | « Sécu-théâtre » | Scans en `continue-on-error: true` → badge vert inutile |

En une phrase :
**« Comment empêcher automatiquement qu’UrbanHub parte en staging/prod s’il est dangereux ? »**

---

## 2. Pourquoi les résoudre ?

| Pourquoi | Explication débutant |
|---|---|
| **Condition Direction IT** | Pas de prod sans pipeline durci (énoncé TP4) |
| **Vitesse** | Un gate CI bloque en minutes ; un audit manuel prend des jours |
| **Répétabilité** | Chaque commit subit les **mêmes** contrôles |
| **Preuve d’audit** | Artefacts SARIF / SBOM / signature Cosign |
| **Continuité TP3** | Le SBOM n’est plus un one-shot : il est généré à chaque build |

Un pipeline durci = une **politique exécutable**, pas un document PDF oublié.

---

## 3. Comment on s’y prend pour les résoudre ?

Le cours exige **6 étapes minimum**.

### Étape 1 — Lint + tests (coverage ≥ 60 %)

```text
Ruff + pytest --cov-fail-under=60
```

Problème résolu : code cassé / non testé ne passe pas.

### Étape 2 — SAST (Bandit + Semgrep) → SARIF

Problème résolu : patterns dangereux dans **notre** code détectés tôt.

### Étape 3 — SCA Trivy fs + Gitleaks

Gates **bloquants** :

- secret trouvé → **fail**
- CVE **CRITICAL** → **fail**

### Étape 4 — Build Docker multi-stage + scan image

Durcissement :

- multi-stage (`builder` / `runtime`)
- `USER` non-root (`uid 10001`)
- Trivy image gate CRITICAL

Fichiers : `alert-service/Dockerfile`, `iot-service/Dockerfile`.

### Étape 5 — Push registry + Cosign + SBOM

- push `ghcr.io`
- signature **Cosign keyless** (OIDC GitHub)
- SBOM CycloneDX en artefact

### Étape 6 — Staging + smoke test

```bash
docker compose up -d …
curl -f http://127.0.0.1:8000/health
curl -f http://127.0.0.1:8001/health
```

Fichier pipeline : `.github/workflows/devsecops.yml`
Décisions gates : `evidence/tp4/GATES.md`

### Schéma mental

```text
commit
  → 1 lint/tests
  → 2 SAST
  → 3 SCA + secrets   } gates durs
  → 4 build + scan image
  → 5 push + cosign + SBOM
  → 6 staging smoke
  → OK seulement si tout vert
```

---

## 4. Comment le tester ?

### A. Tests locaux (avant de pousser)

| Étape | Comment tester | OK si… |
|---|---|---|
| 1 Tests | `cd alert-service && uv run pytest --cov=src --cov-fail-under=60` | Exit code 0 |
| 2 Bandit | `uvx bandit -r alert-service/src iot-service/src` | Rapport généré |
| 3 Secrets | `docker run … gitleaks detect` | 0 secret |
| 3 SCA | `trivy fs --severity CRITICAL --exit-code 1 .` | Pas de CRITICAL (ou fail attendu) |
| 4 Image | `docker build …` puis `docker run --rm IMAGE id` | `uid=10001` |
| 6 Smoke | `docker compose up -d` + `curl /health` | HTTP 200 |

### B. Tests GitHub Actions

1. Pousser une branche
2. Ouvrir **Actions** → workflow **DevSecOps Pipeline (TP4)**
3. Vérifier que les 6 jobs tournent
4. Télécharger les artefacts → copier dans `evidence/tp4/`

| Run | Comment le provoquer | OK si… |
|---|---|---|
| **Vert** | Branche saine, pas de secret, pas de CRITICAL | Tous les jobs success |
| **Rouge** (exigé) | Injecter un faux secret **jetable** OU forcer un seuil Trivy | Job secrets/SCA **failed** + capture |

⚠️ Ne jamais committer un **vrai** secret pour le run rouge.

### C. Checklist de validation du rendu

| Critère grille | Comment vérifier |
|---|---|
| 6 étapes présentes | Lire `devsecops.yml` (jobs 1→6) |
| Gates bloquants | `exit-code: "1"` + Gitleaks sans `continue-on-error` |
| Dockerfile durci | `USER appuser` + multi-stage |
| Cosign + SBOM | Job 5 + fichiers evidence |
| Evidence pack | `evidence/tp4/` rempli |
| Doc gates | `evidence/tp4/GATES.md` |

### Mini auto-test

1. Pourquoi un scan en `continue-on-error: true` est un anti-pattern ? → il ne bloque rien
2. Que signe Cosign ? → l’image (provenance CI)
3. Différence Trivy fs / Trivy image ? → dépendances projet vs layers de l’image
4. Coverage 55 % → ? → job 1 rouge (`--cov-fail-under=60`)

### Preuve de rendu

- `.github/workflows/devsecops.yml`
- Dockerfiles multi-stage non-root
- `evidence/tp4/` (SARIF, SBOM, cosign, captures)
- captures `run-vert` + `run-rouge`

---

## Lien avec les TP précédents

| TP | Apport | Dans le pipeline |
|---|---|---|
| TP1 | Risques prioritaires | Justifie *pourquoi* ces gates |
| TP2 | Combo Bandit/Trivy/Gitleaks | Outils réutilisés en CI |
| TP3 | Priorisation + SBOM | SBOM généré à chaque build ; CRITICAL bloqué |
| TP4 | Automatisation | Politique = code YAML exécutable |
