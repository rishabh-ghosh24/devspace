import asyncio
from quart import Quart, jsonify
from db import get_db, seed

app = Quart(__name__)


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
