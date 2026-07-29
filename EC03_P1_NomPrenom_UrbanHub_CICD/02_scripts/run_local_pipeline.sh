#!/usr/bin/env bash
# EC03 — Exécution locale des 6 étapes (miroir du pipeline CI)
# Usage: depuis la racine du dépôt UrbanHub
#   bash EC03_P1_NomPrenom_UrbanHub_CICD/02_scripts/run_local_pipeline.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SERVICE="${ROOT}/iot-service"
EC03="${ROOT}/EC03_P1_NomPrenom_UrbanHub_CICD"
ART="${EC03}/artifacts"
IMAGE="urbanhub/iot-service:ec03-local"

mkdir -p "${ART}"

step() { echo ""; echo "========== $1 =========="; }

step "1 · INSTALL"
cd "${SERVICE}"
uv sync --frozen --all-groups --no-progress

step "2 · TEST"
uv run pytest tests/ -v \
  --cov=src \
  --cov-report=term-missing \
  --cov-fail-under=50 \
  2>&1 | tee "${ART}/logs-pytest-local.txt"

step "3 · QUALITY"
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/ 2>&1 | tee "${ART}/logs-mypy-local.txt"

step "4 · SECURITY (partiel — Gitleaks/Trivy via Docker si disponible)"
uv run bandit -r src/ -f screen -ll 2>&1 | tee "${ART}/logs-bandit-local.txt"

if command -v docker >/dev/null 2>&1; then
  docker run --rm -v "${ROOT}:/src" aquasec/trivy:0.28.0 fs \
    --severity CRITICAL --exit-code 1 --ignore-unfixed \
    --skip-dirs /src/iot-service/.venv \
    /src/iot-service 2>&1 | tee "${ART}/logs-trivy-local.txt" || true
fi

step "5 · BUILD"
docker build -t "${IMAGE}" "${SERVICE}"

step "6 · DEPLOY"
docker rm -f ec03-iot-smoke 2>/dev/null || true
docker run -d --name ec03-iot-smoke -p 18001:8001 \
  -e KAFKA_BOOTSTRAP_SERVERS=127.0.0.1:9092 \
  "${IMAGE}"
bash "${EC03}/02_scripts/smoke_test.sh" http://127.0.0.1:18001 \
  2>&1 | tee "${ART}/logs-smoke-local.txt"
docker rm -f ec03-iot-smoke

echo ""
echo "EC03 local pipeline finished OK"
