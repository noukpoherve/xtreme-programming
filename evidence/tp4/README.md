# Evidence pack — TP 4 Pipeline DevSecOps

Dossier de preuves pour le rendu du TP 4.

## Contenu attendu

| Fichier | Origine | Statut |
|---|---|---|
| `GATES.md` | Décisions de configuration | ✅ présent |
| `bandit.json` / `*.sarif` | Job SAST du workflow | produit par CI |
| `semgrep.sarif` | Job SAST | produit par CI |
| `trivy-fs.json` | Job SCA | produit par CI |
| `trivy-image-*.json` | Job scan image | produit par CI |
| `gitleaks.sarif` | Job secrets | produit par CI (ou TP2) |
| `sbom-*.json` | Job SBOM / Cosign | produit par CI |
| `cosign-verify.txt` | Sortie `cosign verify` | produit par CI |
| `captures/run-vert.png` | Screenshot Actions | à ajouter |
| `captures/run-rouge.png` | Screenshot fail volontaire | à ajouter |

## Comment remplir ce pack après un run GitHub Actions

1. Ouvrir l’onglet **Actions** → workflow **DevSecOps Pipeline (TP4)**
2. Télécharger les artefacts `evidence-pack-*`
3. Dézipper ici (`evidence/tp4/`)
4. Faire 2 captures d’écran :
   - run **vert** complet
   - run **rouge** (fail Gitleaks ou Trivy volontaire)

## Commandes locales de secours

```bash
# SAST
docker run --rm -v "$PWD:/src" -w /src python:3.13-slim \
  bash -c "pip install -q bandit && bandit -r alert-service/src iot-service/src -f json -o evidence/tp4/bandit.json"

# SCA
docker run --rm -v "$PWD:/src" aquasec/trivy fs \
  --severity CRITICAL,HIGH --format json \
  -o /src/evidence/tp4/trivy-fs.json /src

# Secrets
docker run --rm -v "$PWD:/src" zricethezav/gitleaks:latest \
  detect --source /src --report-format sarif --report-path /src/evidence/tp4/gitleaks.sarif --no-banner

# SBOM (déjà fait en TP3)
cp evidence/tp3/sbom-iot.json evidence/tp4/sbom-iot.json
cp evidence/tp3/sbom-alert.json evidence/tp4/sbom-alert.json
```

## Lien documentation

- Guide pédagogique : `docs/tp/TP4-pipeline-DevSecOps-UrbanHub.md`
- Pipeline : `.github/workflows/devsecops.yml`
