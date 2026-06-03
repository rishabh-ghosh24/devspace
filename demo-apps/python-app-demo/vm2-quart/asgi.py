"""
asgi.py — Hypercorn entry point.

Initialises OpenTelemetry BEFORE importing the Quart app so that
oracledb.connect() is patched and every DB call becomes a span.
The app code (app.py) contains zero OTel imports.

Usage:  hypercorn asgi:application --bind 0.0.0.0:8080
"""

from otel_setup import init_otel

# 1. Initialise tracing + instrument oracledb  (MUST happen first)
init_otel()

# 2. Import the Quart app (triggers db.py import, but get_db() is deferred)
from app import app  # noqa: E402

# 3. Wrap the ASGI interface with OTel middleware
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware  # noqa: E402

application = OpenTelemetryMiddleware(app.asgi_app)
