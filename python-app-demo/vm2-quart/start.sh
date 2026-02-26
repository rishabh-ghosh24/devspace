#!/bin/bash
# ---------------------------------------------------------------------------
# start.sh — Launch the StayEasy Hotel Booking app
#
# OTel tracing is initialised inside asgi.py / otel_setup.py.
# APM_ENDPOINT and APM_DATA_KEY are read from the .env EnvironmentFile.
# DB_DSN, DB_USER, DB_PASSWORD are read from the same .env file.
# ---------------------------------------------------------------------------

set -euo pipefail

# --- Validate APM connection vars (loaded from .env by systemd) ---
export APM_ENDPOINT="${APM_ENDPOINT:?Set APM_ENDPOINT in /opt/quart-demo/.env}"
export APM_DATA_KEY="${APM_DATA_KEY:?Set APM_DATA_KEY in /opt/quart-demo/.env}"
export OTEL_SERVICE_NAME="stayeasy-hotel-app"

# --- Validate ADB connection vars ---
export DB_DSN="${DB_DSN:?Set DB_DSN in /opt/quart-demo/.env}"
export DB_USER="${DB_USER:-stayeasy}"
export DB_PASSWORD="${DB_PASSWORD:?Set DB_PASSWORD in /opt/quart-demo/.env}"

# --- Launch via asgi.py entry point (OTel wired there) ---
exec /home/opc/.local/bin/hypercorn asgi:application \
    --bind 0.0.0.0:8080 \
    --workers 1
