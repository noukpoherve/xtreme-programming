# Guide rapide - lancer les scans proprement

## Probleme frequent

Si tu lances plusieurs commandes Docker en meme temps, le terminal devient illisible :
- barres de progression Trivy qui se melangent ;
- telechargements d'images Docker ;
- sorties qui s'empilent.

## Solution recommandee : un seul script

Depuis la racine du projet :

```powershell
cd "D:\EADL-2025-IMIE\Usine Logiciel\xtreme-programming"
powershell -ExecutionPolicy Bypass -File evidence/run-audit.ps1
```

Le script :
1. lance les outils **dans l'ordre** ;
2. affiche des **etapes numerotees** (1/3, 2/3, 3/3) ;
3. ecrit des **logs propres** dans `evidence/logs-*.txt`.

## Fichiers a ouvrir pour tes captures

| Outil | Fichier a capturer |
|---|---|
| Bandit | `evidence/logs-bandit.txt` |
| Trivy | `evidence/logs-trivy.txt` |
| Gitleaks | `evidence/logs-gitleaks.txt` |

## Alternative : une commande a la fois

Ne lance **jamais** toutes les commandes en parallele.

### Bandit

```powershell
docker run --rm -v "${PWD}:/src" -w /src python:3.12-slim bash -c "pip install -q bandit && bandit -r iot-service/src alert-service/src"
```

### Trivy (sortie lisible)

```powershell
docker run --rm -v "${PWD}:/src" aquasec/trivy:latest fs --quiet --no-progress --severity HIGH,CRITICAL --scanners vuln --format table /src/iot-service
```

```powershell
docker run --rm -v "${PWD}:/src" aquasec/trivy:latest fs --quiet --no-progress --severity HIGH,CRITICAL --scanners vuln --format table /src/alert-service
```

### Gitleaks

```powershell
docker run --rm -v "${PWD}:/src" -w /src zricethezav/gitleaks:latest detect --no-banner
```

## Astuce capture Windows

1. Lance **une seule** etape.
2. Attends la fin.
3. `Win + Shift + S` pour capturer la zone.
4. Colle dans Word ou PowerPoint.

## Livrables finaux

- Rapport : `evidence/urbanhub-audit-report.pdf`
- Preuves : dossier `evidence/` (JSON, SARIF, logs)
- Captures : 3 screenshots (Bandit, Trivy, Gitleaks)
