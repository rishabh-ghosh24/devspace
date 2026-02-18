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

# --- OpenTelemetry resource / exporter config ---
export OTEL_SERVICE_NAME="retail-quart-app"
export OTEL_RESOURCE_ATTRIBUTES="deployment.environment=demo,service.version=1.0,host.name=$(hostname)"

# OCI APM OTLP/HTTP endpoint (append the traces path)
export OTEL_EXPORTER_OTLP_ENDPOINT="${APM_ENDPOINT}/20200101/opentelemetry"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=dataKey ${APM_DATA_KEY}"

export OTEL_TRACES_EXPORTER="otlp_proto_http"
export OTEL_METRICS_EXPORTER="none"
export OTEL_LOGS_EXPORTER="none"

# W3C Trace Context propagation — required for cross-service trace stitching
export OTEL_PROPAGATORS="tracecontext,baggage"

# Correlate Python log records with trace/span IDs
export OTEL_PYTHON_LOG_CORRELATION="true"

# --- Launch ---
exec /home/opc/.local/bin/opentelemetry-instrument \
    /home/opc/.local/bin/hypercorn app:app \
    --bind 0.0.0.0:8080 \
    --workers 1
