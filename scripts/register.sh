#!/usr/bin/env bash
set -euo pipefail

BUS_URL="${SAHIIXX_BUS_URL:-http://sahiixx-bus:9000}"
SELF_URL="${CODEX_SELF_URL:-http://localhost:9001}"

echo "🔌 Registering codex-self with SAHIIXX bus at $BUS_URL ..."

curl -sf "$SELF_URL/bus/register" > /dev/null && echo "✅ Registered via self-service" || echo "⚠️ Self-service register failed"

echo ""
echo "📊 Current status:"
curl -sf "$SELF_URL/bus/status" | python3 -m json.tool 2>/dev/null || curl -sf "$SELF_URL/bus/status"
echo ""
