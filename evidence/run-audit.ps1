# TP2 UrbanHub - Lancement ordonne des scans de securite
# Usage: depuis la racine du projet
#   powershell -ExecutionPolicy Bypass -File evidence/run-audit.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path evidence)) {
    New-Item -ItemType Directory -Path evidence | Out-Null
}

function Write-Step {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 72) -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host ("=" * 72) -ForegroundColor Cyan
    Write-Host ""
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "[..] $Message" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  TP2 - Audit outillage UrbanHub" -ForegroundColor White
Write-Host "  Dossier projet : $Root" -ForegroundColor DarkGray
Write-Host ""

# Verifier Docker
Write-Info "Verification de Docker..."
docker info --format "{{.ServerVersion}}" | Out-Null
Write-Ok "Docker est pret"

# ---------------------------------------------------------------------------
# 1/3 BANDIT (SAST)
# ---------------------------------------------------------------------------
Write-Step "1/3 - Bandit (SAST Python)"
$banditLog = "evidence/logs-bandit.txt"

docker run --rm -v "${PWD}:/src" -w /src python:3.12-slim bash -c `
    "pip install -q bandit && bandit -r iot-service/src alert-service/src -f json -o evidence/bandit.json" `
    2>&1 | Tee-Object -FilePath $banditLog

if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 1) {
    throw "Bandit a echoue (code $LASTEXITCODE)"
}

$banditCount = (Get-Content evidence/bandit.json | ConvertFrom-Json).results.Count
Write-Ok "Bandit termine -> evidence/bandit.json ($banditCount finding(s))"
Write-Host "     Log terminal : $banditLog" -ForegroundColor DarkGray

# ---------------------------------------------------------------------------
# 2/3 TRIVY (SCA)
# ---------------------------------------------------------------------------
Write-Step "2/3 - Trivy (SCA dependances)"
$trivyLog = "evidence/logs-trivy.txt"

Write-Info "Scan iot-service..."
docker run --rm -v "${PWD}:/src" aquasec/trivy:latest fs `
    --quiet --no-progress `
    --severity HIGH,CRITICAL `
    --scanners vuln `
    --skip-dirs /src/iot-service/.venv,/src/.venv,/src/.git,/src/.idea,/src/site `
    --format table `
    /src/iot-service `
    2>&1 | Tee-Object -FilePath $trivyLog -Append

docker run --rm -v "${PWD}:/src" aquasec/trivy:latest fs `
    --quiet --no-progress `
    --severity HIGH,CRITICAL `
    --scanners vuln `
    --skip-dirs /src/iot-service/.venv,/src/.venv,/src/.git,/src/.idea,/src/site `
    --format json -o /src/evidence/trivy-iot.json `
    /src/iot-service | Out-Null

Write-Ok "Trivy iot-service -> evidence/trivy-iot.json"

Write-Info "Scan alert-service..."
docker run --rm -v "${PWD}:/src" aquasec/trivy:latest fs `
    --quiet --no-progress `
    --severity HIGH,CRITICAL `
    --scanners vuln `
    --skip-dirs /src/alert-service/.venv,/src/.venv,/src/.git,/src/.idea,/src/site `
    --format table `
    /src/alert-service `
    2>&1 | Tee-Object -FilePath $trivyLog -Append

docker run --rm -v "${PWD}:/src" aquasec/trivy:latest fs `
    --quiet --no-progress `
    --severity HIGH,CRITICAL `
    --scanners vuln `
    --skip-dirs /src/alert-service/.venv,/src/.venv,/src/.git,/src/.idea,/src/site `
    --format json -o /src/evidence/trivy-alert.json `
    /src/alert-service | Out-Null

Write-Ok "Trivy alert-service -> evidence/trivy-alert.json"
Write-Host "     Log terminal : $trivyLog" -ForegroundColor DarkGray

# ---------------------------------------------------------------------------
# 3/3 GITLEAKS (Secrets)
# ---------------------------------------------------------------------------
Write-Step "3/3 - Gitleaks (recherche de secrets)"
$gitleaksLog = "evidence/logs-gitleaks.txt"

docker run --rm -v "${PWD}:/src" -w /src zricethezav/gitleaks:latest detect `
    --no-banner `
    --report-format sarif `
    --report-path /src/evidence/gitleaks-git.sarif `
    2>&1 | Tee-Object -FilePath $gitleaksLog

if ($LASTEXITCODE -ne 0) {
    throw "Gitleaks a echoue (code $LASTEXITCODE)"
}

Write-Ok "Gitleaks termine -> evidence/gitleaks-git.sarif (0 secret confirme attendu)"
Write-Host "     Log terminal : $gitleaksLog" -ForegroundColor DarkGray

# ---------------------------------------------------------------------------
# RESUME FINAL
# ---------------------------------------------------------------------------
Write-Step "RESUME"
Write-Host "  Fichiers generes :" -ForegroundColor White
Write-Host "    - evidence/bandit.json"
Write-Host "    - evidence/trivy-iot.json"
Write-Host "    - evidence/trivy-alert.json"
Write-Host "    - evidence/gitleaks-git.sarif"
Write-Host ""
Write-Host "  Logs propres pour captures d'ecran :" -ForegroundColor White
Write-Host "    - evidence/logs-bandit.txt"
Write-Host "    - evidence/logs-trivy.txt"
Write-Host "    - evidence/logs-gitleaks.txt"
Write-Host ""
Write-Host "  Rapport PDF :" -ForegroundColor White
Write-Host "    - evidence/urbanhub-audit-report.pdf"
Write-Host ""
Write-Ok "Audit termine. Utilise les fichiers logs-*.txt pour des screenshots lisibles."
Write-Host ""
