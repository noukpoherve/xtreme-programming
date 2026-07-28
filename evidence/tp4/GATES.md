# Décisions de configuration des gates — TP 4 UrbanHub
# =====================================================

Ce fichier explique **pourquoi** chaque gate est configuré ainsi.
C’est le README « décisions » demandé par la grille d’évaluation.

## Politique globale

| Famille | Outil | Mode | Justification |
|---|---|---|---|
| Qualité | Ruff + pytest-cov | **BLOQUANT** | Coverage < 60 % = fail (énoncé TP4) |
| SAST | Bandit + Semgrep | Artefacts + warn→fail HIGH | Rodage puis durcissement (cours ch.2) |
| Secrets | Gitleaks | **BLOQUANT** | 1 secret = fail immédiat |
| SCA deps | Trivy fs | **BLOQUANT** sur CRITICAL | Exigence TP4 |
| Image | Trivy image | **BLOQUANT** sur CRITICAL | Exigence TP4 |
| Signature | Cosign keyless | Obligatoire sur push GHCR | Supply-chain |
| SBOM | Trivy CycloneDX | Artefact publié | Continuité TP3 |
| Staging | docker compose + curl health | **BLOQUANT** | Smoke test |

## Pourquoi CRITICAL et pas HIGH tout de suite ?

Sur ce dépôt, Trivy remonte aujourd’hui des CVE **HIGH** (`starlette`).
Si on mettait `exit-code=1` sur HIGH dès le jour 1, le pipeline serait **toujours rouge**
et bloquerait tout le travail d’équipe.

Approche recommandée par le cours :

1. Semaine 1–2 : secrets hard-fail
2. Semaine 3–4 : Trivy en warn sur HIGH
3. Semaine 5–6 : break sur CRITICAL, puis break-new sur HIGH

Pour le TP, le gate **CRITICAL** satisfait l’énoncé.
Le plan de remédiation TP3 traite les HIGH Starlette sous 48 h.

## Exceptions

Toute exception à un gate doit avoir :

- un ticket
- un propriétaire
- une date d’expiration < 30 jours

Sans ça, la matrice devient poreuse (anti-pattern cours).

## Secrets GitHub utilisés

| Secret / permission | Usage |
|---|---|
| `GITHUB_TOKEN` | checkout, push GHCR, upload artefacts |
| `id-token: write` | Cosign keyless (OIDC) |
| `packages: write` | Push `ghcr.io` |

Aucun secret applicatif (DB password, API key) n’est stocké dans le YAML.
