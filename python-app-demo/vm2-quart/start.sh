#!/bin/bash
# ---------------------------------------------------------------------------
# start.sh — Launch the StayEasy Hotel Booking app
#
# OTel tracing is initialised inside asgi.py / otel_setup.py.
# APM_ENDPOINT and APM_DATA_KEY are read from the .env EnvironmentFile.
# ---------------------------------------------------------------------------

set -euo pipefail

# --- Validate APM connection vars (loaded from .env by systemd) ---
export APM_ENDPOINT="${APM_ENDPOINT:?Set APM_ENDPOINT in /opt/quart-demo/.env}"
export APM_DATA_KEY="${APM_DATA_KEY:?Set APM_DATA_KEY in /opt/quart-demo/.env}"
export OTEL_SERVICE_NAME="stayeasy-hotel-app"

# --- Launch via asgi.py entry point (OTel wired there) ---
exec /home/opc/.local/bin/hypercorn asgi:application \
    --bind 0.0.0.0:8080 \
    --workers 1
