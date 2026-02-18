"""
otel_setup.py — OpenTelemetry configuration for OCI APM.

This file contains ALL tracing configuration. The application code
(app.py) has zero OTel imports — this is the "auto-instrumentation"
layer that can be added or removed without touching business logic.

Called once from asgi.py before the Quart app is imported.
"""

import os
import logging

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

log = logging.getLogger(__name__)


def init_otel(service_name: str = "stayeasy-hotel-app") -> None:
    """Initialise OpenTelemetry SDK, OTLP exporter, and auto-instrumentors."""

    resource = Resource.create({
        "service.name": os.environ.get("OTEL_SERVICE_NAME", service_name),
        "deployment.environment": "demo",
        "service.version": "1.0",
    })

    provider = TracerProvider(resource=resource)

    # --- OCI APM OTLP/HTTP exporter ---
    apm_endpoint = os.environ.get("APM_ENDPOINT", "")
    apm_key = os.environ.get("APM_DATA_KEY", "")

    if apm_endpoint and apm_key:
        exporter = OTLPSpanExporter(
            endpoint=f"{apm_endpoint}/20200101/opentelemetry/v1/traces",
            headers={"Authorization": f"dataKey {apm_key}"},
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        log.info("OTel exporter configured → %s", apm_endpoint)
    else:
        log.warning("APM_ENDPOINT / APM_DATA_KEY not set — traces will not be exported")

    trace.set_tracer_provider(provider)

    # --- W3C Trace Context propagation ---
    set_global_textmap(CompositePropagator([
        TraceContextTextMapPropagator(),
        W3CBaggagePropagator(),
    ]))

    # --- Auto-instrument SQLite ---
    SQLite3Instrumentor().instrument()
    log.info("SQLite3 instrumentation active")
