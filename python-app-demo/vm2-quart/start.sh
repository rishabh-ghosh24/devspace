#!/bin/bash
# ---------------------------------------------------------------------------
# start.sh — Launch the Retail Quart app with OpenTelemetry auto-instrumentation
#
# Fill in APM_ENDPOINT and APM_DATA_KEY before running, or supply them via
# an EnvironmentFile when using the systemd service.
# ---------------------------------------------------------------------------

set -euo pipefail

# --- OCI APM connection ---
# Format: https://<apm-domain-prefix>.apm-agt.{region}.oci.oraclecloud.com
APM_ENDPOINT="${APM_ENDPOINT:?Set APM_ENDPOINT to your OCI APM data-upload endpoint}"
APM_DATA_KEY="${APM_DATA_KEY:?Set APM_DATA_KEY to your OCI APM private data key}"

# --- OCI APM connection (read by app.py directly) ---
export APM_ENDPOINT="${APM_ENDPOINT:?Set APM_ENDPOINT in .env}"
export APM_DATA_KEY="${APM_DATA_KEY:?Set APM_DATA_KEY in .env}"
export OTEL_SERVICE_NAME="retail-quart-app"

# --- Launch (OTel initialised inside app.py) ---
exec /home/opc/.local/bin/hypercorn app:app \
    --bind 0.0.0.0:8080 \
    --workers 1
