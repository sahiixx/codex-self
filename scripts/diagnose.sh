#!/usr/bin/env bash
set -euo pipefail

SELF_URL="${CODEX_SELF_URL:-http://localhost:9001}"

echo "🏥 Codex Self Diagnostics"
echo "========================"

echo ""
echo "-- Quick Health --"
curl -sf "$SELF_URL/health" | python3 -m json.tool 2>/dev/null || curl -sf "$SELF_URL/health"

echo ""
echo "-- Full Diagnose --"
curl -sf "$SELF_URL/diagnose" | python3 -m json.tool 2>/dev/null || curl -sf "$SELF_URL/diagnose"

echo ""
echo "-- Identity --"
curl -sf "$SELF_URL/identity" | python3 -m json.tool 2>/dev/null || curl -sf "$SELF_URL/identity"

echo ""
echo "-- Bus Status --"
curl -sf "$SELF_URL/bus/status" | python3 -m json.tool 2>/dev/null || curl -sf "$SELF_URL/bus/status"

echo ""
echo "-- Skills --"
curl -sf "$SELF_URL/skills" | python3 -m json.tool 2>/dev/null || curl -sf "$SELF_URL/skills"
