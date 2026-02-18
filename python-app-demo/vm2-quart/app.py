import asyncio
import os
from quart import Quart, jsonify
from db import get_db, seed

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator

# --- OTel setup ---
resource = Resource.create({
    "service.name": os.environ.get("OTEL_SERVICE_NAME", "retail-quart-app"),
    "deployment.environment": "demo",
    "service.version": "1.0",
})

provider = TracerProvider(resource=resource)

apm_endpoint = os.environ.get("APM_ENDPOINT", "")
apm_key = os.environ.get("APM_DATA_KEY", "")

if apm_endpoint and apm_key:
    otlp_exporter = OTLPSpanExporter(
        endpoint=f"{apm_endpoint}/20200101/opentelemetry/v1/traces",
        headers={"Authorization": f"dataKey {apm_key}"},
    )
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Always add console exporter so we can see spans in logs
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

trace.set_tracer_provider(provider)
set_global_textmap(CompositePropagator([
    TraceContextTextMapPropagator(),
    W3CBaggagePropagator(),
]))

# --- SQLite instrumentation ---
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
SQLite3Instrumentor().instrument()

app = Quart(__name__)
app.asgi_app = OpenTelemetryMiddleware(app.asgi_app)


@app.before_serving
async def startup():
    seed()


@app.route("/")
async def index():
    return jsonify({
        "service": "retail-demo",
        "status": "ok",
        "routes": [
            "/products",
            "/products/<id>",
            "/products/category/<category>",
            "/customers",
            "/orders",
            "/orders/slow",
        ],
    })


@app.route("/products")
async def list_products():
    db = get_db()
    rows = db.execute("SELECT * FROM products").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/products/<int:product_id>")
async def get_product(product_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "product not found"}), 404
    return jsonify(dict(row))


@app.route("/products/category/<category>")
async def products_by_category(category):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM products WHERE category = ?", (category,)
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/customers")
async def list_customers():
    db = get_db()
    rows = db.execute("SELECT * FROM customers").fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/orders")
async def list_orders():
    db = get_db()
    rows = db.execute("""
        SELECT
            o.id,
            c.name  AS customer,
            p.name  AS product,
            o.quantity,
            o.total,
            o.status
        FROM orders   o
        JOIN customers c ON o.customer_id = c.id
        JOIN products  p ON o.product_id  = p.id
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@app.route("/orders/slow")
async def slow_order():
    """Intentionally slow endpoint to demonstrate latency in OCI APM."""
    await asyncio.sleep(2)
    db = get_db()
    rows = db.execute(
        "SELECT * FROM orders WHERE status = 'pending'"
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])
