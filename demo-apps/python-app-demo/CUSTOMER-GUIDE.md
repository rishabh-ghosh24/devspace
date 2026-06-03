# Monitoring Python Applications with OCI APM

Distributed tracing for Flask, Django, FastAPI, and Quart using OpenTelemetry and OCI Application Performance Monitoring.

## What This Guide Covers

This guide walks you through adding distributed tracing to a Python application using OpenTelemetry (OTel) and OCI APM. By the end, your application will:

- Automatically trace every HTTP request (route, status code, latency)
- Capture every database query with the actual SQL text
- Show a service topology map in the OCI APM Console
- Track errors and latency spikes — without modifying your application code

---

## How Instrumentation Works

OpenTelemetry provides several approaches to instrument a Python application. The key difference is how much your application code needs to change.

| Approach | Changes to app code | Entry point change | Best for |
|----------|--------------------|--------------------|----------|
| CLI auto-instrument | None | CLI wrapper | Flask, Django (WSGI) |
| SDK wrapper | None | Small wrapper file | Quart, FastAPI (ASGI) |
| Manual spans | Yes (import tracer) | Either | Custom business logic tracing |

For most applications, **you do not need manual spans**. The first two approaches capture HTTP requests and database queries automatically. Your application code (`app.py`, `views.py`, etc.) remains untouched — zero OpenTelemetry imports.

### Why two approaches?

The `opentelemetry-instrument` CLI works by wrapping your Python process and auto-detecting installed frameworks. This works well for WSGI frameworks (Flask, Django) where the framework manages the server lifecycle.

For ASGI frameworks (Quart, FastAPI, Starlette) running under servers like Hypercorn or Uvicorn, the CLI does not reliably apply the ASGI middleware. In this case, a small wrapper file (typically `asgi.py`, ~10 lines) initializes OTel and applies the middleware explicitly. The application code itself still has zero OTel imports.

---

## Prerequisites

- **OCI APM Domain** — Create one in the OCI Console (Observability & Management > APM)
- **APM Private Data Key** — Found in APM Domain > Data Keys
- **Python 3.8+** application with `pip` available

---

## Step 1: Install OpenTelemetry Packages

```bash
pip install \
  opentelemetry-distro \
  opentelemetry-exporter-otlp-proto-http \
  opentelemetry-instrumentation-dbapi
```

Then install framework-specific instrumentors:

| Your framework | Additional package |
|----------------|-------------------|
| Flask, Django (WSGI) | `opentelemetry-instrumentation-wsgi` |
| Quart, FastAPI, Starlette (ASGI) | `opentelemetry-instrumentation-asgi` |

For database auto-instrumentation, the `opentelemetry-instrumentation-dbapi` package supports any DB-API 2.0 driver:

| Database | Python driver | `database_system` value |
|----------|--------------|------------------------|
| Oracle DB | `oracledb` | `oracle` |
| PostgreSQL | `psycopg2` | `postgresql` |
| MySQL | `mysql-connector-python` | `mysql` |
| SQLite | `sqlite3` | `sqlite` |

> **Tip:** You can also run `opentelemetry-bootstrap -a install` to auto-detect installed frameworks and install matching instrumentors. However, this may pull in packages you don't need (e.g., the gRPC exporter). Installing explicitly gives you more control.

---

## Step 2: Configure the OCI APM Endpoint

Set these environment variables (or configure them in code):

```bash
export APM_ENDPOINT="https://<apm-domain>.apm-agt.<region>.oci.oraclecloud.com"
export APM_DATA_KEY="<your-private-data-key>"
export OTEL_SERVICE_NAME="my-python-app"
```

**Where to find these values:**
- OCI Console > Observability & Management > Application Performance Monitoring > APM Domains
- Select your domain > **Data Keys** tab > copy the Private Data Key
- The endpoint follows this pattern: `https://<domain-prefix>.apm-agt.<region>.oci.oraclecloud.com`

The full OTLP traces URL that OCI APM expects is:
```
{APM_ENDPOINT}/20200101/opentelemetry/v1/traces
```

Authentication is via the header: `Authorization: dataKey <your-private-data-key>`

---

## Step 3: Wire the Entry Point

Choose the option that matches your framework.

### Option A: Flask / Django (WSGI) — CLI auto-instrument

This is the simplest approach. No code changes needed.

```bash
OTEL_SERVICE_NAME=my-app \
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="https://<apm-domain>.apm-agt.<region>.oci.oraclecloud.com/20200101/opentelemetry/v1/traces" \
OTEL_EXPORTER_OTLP_TRACES_HEADERS="Authorization=dataKey <your-private-data-key>" \
opentelemetry-instrument python app.py
```

That's it. The CLI detects Flask/Django, applies the WSGI middleware, and exports spans to OCI APM.

> **Note:** Use `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` (with `_TRACES_`) to set the full URL including the `/20200101/opentelemetry/v1/traces` path. If you use `OTEL_EXPORTER_OTLP_ENDPOINT` (without `_TRACES_`), the SDK appends `/v1/traces` which is not the correct OCI APM path.

### Option B: Quart / FastAPI / Starlette (ASGI) — SDK wrapper

Create two files alongside your application:

**`otel_setup.py`** — All OTel configuration in one place:

```python
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator

def init_otel(service_name="my-python-app"):
    resource = Resource.create({
        "service.name": os.environ.get("OTEL_SERVICE_NAME", service_name),
    })

    provider = TracerProvider(resource=resource)

    apm_endpoint = os.environ.get("APM_ENDPOINT", "")
    apm_key = os.environ.get("APM_DATA_KEY", "")

    if apm_endpoint and apm_key:
        exporter = OTLPSpanExporter(
            endpoint=f"{apm_endpoint}/20200101/opentelemetry/v1/traces",
            headers={"Authorization": f"dataKey {apm_key}"},
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)

    set_global_textmap(CompositePropagator([
        TraceContextTextMapPropagator(),
        W3CBaggagePropagator(),
    ]))
```

**`asgi.py`** — Entry point wrapper (~5 lines of glue):

```python
from otel_setup import init_otel

# 1. Initialize OTel BEFORE importing the app
init_otel()

# 2. Import your app
from app import app  # your Quart/FastAPI app

# 3. Wrap with ASGI middleware
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

application = OpenTelemetryMiddleware(app.asgi_app)  # Quart
# For FastAPI: application = OpenTelemetryMiddleware(app)
```

Launch with the wrapper as the entry point:

```bash
# Quart / Hypercorn
hypercorn asgi:application --bind 0.0.0.0:8080

# FastAPI / Uvicorn
uvicorn asgi:application --host 0.0.0.0 --port 8080
```

> **Important:** `init_otel()` must run BEFORE your app module is imported. This ensures database drivers are patched before any code calls `connect()`. The import order in `asgi.py` guarantees this.

---

## Step 4: Add Database Instrumentation

Add this to your `otel_setup.py` (inside `init_otel()`, after the TracerProvider is set):

```python
from opentelemetry.instrumentation.dbapi import trace_integration
import oracledb  # or psycopg2, mysql.connector, sqlite3

trace_integration(
    connect_module=oracledb,       # your DB driver module
    connect_method_name="connect",
    database_system="oracle",      # see table in Step 1
    tracer_provider=provider,
)
```

This single call patches the driver's `connect()` method. Every subsequent `cursor.execute()` call automatically generates a span with:
- `db.system` — database type (oracle, postgresql, etc.)
- `db.statement` — the actual SQL query text
- `db.operation` — SELECT, INSERT, UPDATE, DELETE

No changes needed in your application code — your existing `cursor.execute("SELECT ...")` calls are traced transparently.

### Enriching the APM topology with peer.service

OCI APM uses the `peer.service` span attribute to label database nodes in the topology view. Add a custom SpanProcessor to tag database spans:

```python
from opentelemetry.sdk.trace import SpanProcessor

class DbPeerServiceEnricher(SpanProcessor):
    def on_start(self, span, parent_context=None):
        if span.kind == trace.SpanKind.CLIENT:
            span.set_attribute("peer.service", "my-database")
    def on_end(self, span): pass
    def shutdown(self): pass
    def force_flush(self, timeout_millis=None): pass

# Add to provider BEFORE the BatchSpanProcessor:
provider.add_span_processor(DbPeerServiceEnricher())
```

This labels all CLIENT-kind spans (database calls) with `peer.service`. ASGI middleware creates SERVER-kind spans, so HTTP requests are unaffected.

---

## Step 5: Configure APM Span Enrichment Rules

Even with `peer.service` set on your spans, the APM topology may show the database as "External Unknown" until you create a Span Enrichment Rule.

1. OCI Console > Observability & Management > APM > **APM Domains**
2. Select your domain > Resources > **Span Enrichment**
3. Create a new Span Enrichment Group
4. Add Rule > select the Oracle-provided template: **"OpenTelemetry to APM naming conversion"**
5. Save

This pre-built rule maps OpenTelemetry attributes (like `peer.service`, `db.system`) to the APM internal schema that drives the topology view.

> **Note:** Span enrichment only applies to new spans. Existing traces still show the old labels.

---

## Step 6: Verify in OCI APM

1. Generate some traffic to your application
2. OCI Console > Observability & Management > APM > **Trace Explorer**
3. Verify:
   - Your service name appears in the topology
   - HTTP spans show `http.method`, `http.target`, `http.status_code`
   - Database spans show `db.statement` with actual SQL text
   - The topology shows your app connected to the database

---

## Auto-Captured Span Attributes

These attributes are captured automatically with no application code changes:

| Attribute | Source | Example |
|-----------|--------|---------|
| `service.name` | Resource config | `my-python-app` |
| `http.method` | ASGI/WSGI middleware | `GET`, `POST` |
| `http.target` | ASGI/WSGI middleware | `/api/users` |
| `http.status_code` | ASGI/WSGI middleware | `200`, `404`, `500` |
| `http.scheme` | ASGI/WSGI middleware | `http`, `https` |
| `db.system` | DB-API instrumentor | `oracle`, `postgresql` |
| `db.statement` | DB-API instrumentor | `SELECT * FROM users WHERE id = :1` |
| `db.operation` | DB-API instrumentor | `SELECT`, `INSERT` |
| `peer.service` | Custom SpanProcessor | `my-database` |

---

## Adding a Frontend Web Server (Optional)

If your application sits behind Apache or Nginx, you can instrument the web server as a separate service for a richer topology (e.g., `my-webserver` > `my-app` > `my-database`).

For Apache httpd, the [OpenTelemetry Apache module](https://github.com/open-telemetry/opentelemetry-cpp-contrib/tree/main/instrumentation/httpd) adds tracing and auto-injects `traceparent` headers when proxying requests. It exports spans via gRPC to a local OTel Collector, which then forwards them to OCI APM via OTLP/HTTP.

This is optional — the application-level instrumentation described above works without it.

---

## Working Example: StayEasy Hotel Booking Demo

The `python-app-demo/` directory in this repository contains a complete working example:

- **`vm2-quart/app.py`** — 10-route Quart application with ZERO OpenTelemetry imports
- **`vm2-quart/otel_setup.py`** — All OTel configuration (TracerProvider, OTLP exporter, DB instrumentor, peer.service enricher)
- **`vm2-quart/asgi.py`** — ASGI wrapper entry point (5 lines)
- **`vm2-quart/db.py`** — Oracle ADB connection via oracledb thin mode

Verify the zero-import claim: `grep -c opentelemetry vm2-quart/app.py` returns **0**.

See `README.md` for full deployment instructions.

---

## Troubleshooting

**No traces appearing in APM**
- Verify `APM_ENDPOINT` and `APM_DATA_KEY` are set correctly
- Ensure outbound HTTPS (port 443) is open to `*.apm-agt.<region>.oci.oraclecloud.com`
- Check application logs for OTel exporter errors
- For Hypercorn: use `--workers 1` (multi-worker forks break the BatchSpanProcessor flush thread)

**Database spans missing**
- `init_otel()` must run BEFORE the app imports the DB module — check your import order in `asgi.py`
- Use `cursor.execute()` (not `conn.execute()`) — some instrumentors only patch cursor-level calls
- Verify the DB instrumentor package is installed: `pip list | grep instrumentation-dbapi`

**"External Unknown" in APM topology**
- Add `peer.service` attribute to DB spans (see Step 4)
- Create the "OpenTelemetry to APM naming conversion" Span Enrichment Rule (see Step 5)
- Enrichment only applies to new spans — generate fresh traffic after creating the rule

**`opentelemetry-instrument` CLI not working with ASGI**
- This is a known limitation. Use the SDK wrapper approach (Option B in Step 3) instead.
- The wrapper approach gives identical tracing results with more control.

**gRPC exporter error when using HTTP**
- If you see `RuntimeError: Requested component 'otlp_proto_grpc' not found`, set `OTEL_TRACES_EXPORTER=otlp_proto_http` explicitly, or use the programmatic setup in `otel_setup.py` which avoids this issue entirely.
