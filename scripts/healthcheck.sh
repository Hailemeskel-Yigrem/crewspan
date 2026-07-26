#!/usr/bin/env bash
set -euo pipefail

API_URL="${CREWSPAN_API_URL:-http://localhost:8000}"
WEB_URL="${CREWSPAN_WEB_URL:-http://localhost:3000}"

echo "Checking Crewspan services..."
echo

check() {
  local name="$1" url="$2"
  if curl -sf "$url" > /dev/null 2>&1; then
    echo "  ✓ $name ($url)"
  else
    echo "  ✗ $name ($url) — FAILED"
    return 1
  fi
}

fail=0
check "API health" "$API_URL/health" || fail=1
check "API ready"  "$API_URL/ready"  || fail=1
check "Web UI"     "$WEB_URL/"       || fail=1

if command -v pg_isready > /dev/null 2>&1; then
  pg_isready -h localhost -p 5432 > /dev/null 2>&1 && echo "  ✓ PostgreSQL" || { echo "  ✗ PostgreSQL"; fail=1; }
fi

if command -v redis-cli > /dev/null 2>&1; then
  redis-cli ping > /dev/null 2>&1 && echo "  ✓ Redis" || { echo "  ✗ Redis"; fail=1; }
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "All checks passed."
else
  echo "Some checks failed."
  exit 1
fi
