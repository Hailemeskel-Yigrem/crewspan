#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../apps/api"
echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations complete."
