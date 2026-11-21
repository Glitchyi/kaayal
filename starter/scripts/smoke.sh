#!/usr/bin/env bash
# Self-contained Phase 1 smoke test. Usage:
#   bash scripts/smoke.sh [base_url] [tool_secret]
set -euo pipefail

BASE="${1:-http://localhost:8000}"
SECRET="${2:-}"

echo "== GET /health =="
curl -sf "$BASE/health" && echo

echo "== POST /api/voice/reply without token (expect 401) =="
code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/voice/reply" \
  -H 'Content-Type: application/json' -d '{"utterance":"smoke"}')
echo "status=$code"
[ "$code" = "401" ] || { echo "FAIL: expected 401"; exit 1; }

if [ -n "$SECRET" ]; then
  echo "== POST /api/voice/reply with token =="
  curl -s -X POST "$BASE/api/voice/reply" \
    -H 'Content-Type: application/json' \
    -H "X-Kaayal-Tool-Token: $SECRET" \
    -d '{"utterance":"What can Kaayal do?","interaction_id":"smoke-1","language":"en-IN"}'
  echo
else
  echo "No secret provided; skipping authenticated reply check."
fi
echo "smoke done"
