#!/usr/bin/env bash
# Self-contained smoke test. Tool auth is OFF by owner decision (2026-11-22,
# see starter/AGENTS.md) — /api/* answers with no X-Kaayal-Tool-Token.
# Usage: bash scripts/smoke.sh [base_url]
set -euo pipefail

BASE="${1:-http://localhost:8000}"

echo "== GET /health =="
curl -sf "$BASE/health" && echo

echo "== POST /api/voice/reply (open demo — no token required) =="
code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/voice/reply" \
  -H 'Content-Type: application/json' \
  -d '{"utterance":"What can Kaayal do?","interaction_id":"smoke-1","language":"en-IN"}')
echo "status=$code"
[ "$code" = "200" ] || { echo "FAIL: expected 200 (tool auth is off in the demo)"; exit 1; }

echo "== GET /api/catalog/boats =="
curl -sf "$BASE/api/catalog/boats" && echo

echo "smoke done"
