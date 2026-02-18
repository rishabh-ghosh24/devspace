"""
otel_setup.py — OpenTelemetry configuration for OCI APM.

This file contains ALL tracing configuration. The application code
(app.py) has zero OTel imports — this is the "auto-instrumentation"
layer that can be added or removed without touching business logic.

Called once from asgi.py before the Quart app is imported.
"""

import os
import logging

import oracledb
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
from opentelemetry.instrumentation.dbapi import trace_integration

log = logging.getLogger(__name__)


def init_otel(service_name: str = "stayeasy-hotel-app") -> None:
    """Initialise OpenTelemetry SDK, OTLP exporter, and auto-instrumentors."""

    resource = Resource.create({
        "service.name": os.environ.get("OTEL_SERVICE_NAME", service_name),
        "deployment.environment": "demo",
        "service.version": "2.0",
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

    # --- Auto-instrument oracledb (DB-API 2.0) ---
    # This patches oracledb.connect() so every cursor.execute() becomes
    # a span with db.system=oracle, db.statement=<SQL>, db.operation=SELECT/INSERT, etc.
    trace_integration(
        connect_module=oracledb,
        connect_method_name="connect",
        database_system="oracle",
        tracer_provider=provider,
    )
    log.info("oracledb DB-API instrumentation active")
