#!/usr/bin/env bash
# EC03 — Smoke tests après docker run (iot-service)
# Usage: ./smoke_test.sh [BASE_URL]
# Exemple: ./smoke_test.sh http://127.0.0.1:18001

set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:18001}"
HEALTH_URL="${BASE_URL%/}/health"
MAX_WAIT_SEC="${SMOKE_MAX_WAIT_SEC:-90}"
INTERVAL_SEC=3

echo "== EC03 smoke test =="
echo "Target: ${HEALTH_URL}"

elapsed=0
while [ "$elapsed" -lt "$MAX_WAIT_SEC" ]; do
  if curl -sf --max-time 5 "${HEALTH_URL}" -o /tmp/ec03-health.json; then
    echo "HTTP 200 received after ${elapsed}s"
    break
  fi
  sleep "$INTERVAL_SEC"
  elapsed=$((elapsed + INTERVAL_SEC))
done

if [ "$elapsed" -ge "$MAX_WAIT_SEC" ]; then
  echo "FAIL: /health not reachable within ${MAX_WAIT_SEC}s"
  exit 1
fi

python3 - <<'PY'
import json
import sys

with open("/tmp/ec03-health.json", encoding="utf-8") as f:
    body = json.load(f)

status = body.get("status")
if status != "healthy":
    print(f"FAIL: expected status=healthy, got {status!r}")
    sys.exit(1)

version = body.get("version")
if not version:
    print("FAIL: missing version field")
    sys.exit(1)

print(f"OK: status={status}, version={version}")
PY

echo "Smoke test PASSED"
