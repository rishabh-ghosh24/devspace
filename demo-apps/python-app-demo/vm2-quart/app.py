"""
StayEasy Hotel Booking — Quart Application

This file contains ZERO OpenTelemetry imports.
All tracing is handled externally by otel_setup.py + asgi.py.
"""

import asyncio
from datetime import datetime
from quart import Quart, jsonify, request
from db import get_db, seed
import oracledb

app = Quart(__name__)

LOYALTY_DISCOUNTS = {
    "platinum": 0.15,
    "gold":     0.10,
    "silver":   0.05,
    "standard": 0.00,
}


def _dictfetchone(cursor):
    """Fetch one row as a dict (lowercased column names), or None."""
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [col[0].lower() for col in cursor.description]
    return dict(zip(columns, row))


def _dictfetchall(cursor):
    """Fetch all rows as a list of dicts (lowercased column names)."""
    columns = [col[0].lower() for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


@app.before_serving
async def startup():
    seed()


# ──────────────────────────────────────────────────────────────
# Route 1 — Health / index
# ──────────────────────────────────────────────────────────────
@app.route("/")
async def index():
    return jsonify({
        "service": "StayEasy Hotel Booking",
        "status": "ok",
        "routes": [
            "GET  /hotels",
            "GET  /hotels/<id>",
            "GET  /hotels/<id>/rooms",
            "GET  /rooms/search?city&check_in&check_out&guests",
            "POST /reservations",
            "GET  /reservations/<id>",
            "GET  /guests/<id>/reservations",
            "GET  /reports/occupancy",
            "GET  /reports/revenue",
        ],
    })


# ──────────────────────────────────────────────────────────────
# Route 2 — List hotels
# ──────────────────────────────────────────────────────────────
@app.route("/hotels")
async def list_hotels():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hotels ORDER BY rating DESC")
    rows = _dictfetchall(cur)
    cur.close()
    conn.close()
    return jsonify(rows)


# ──────────────────────────────────────────────────────────────
# Route 3 — Hotel detail with rooms
# ──────────────────────────────────────────────────────────────
@app.route("/hotels/<int:hotel_id>")
async def get_hotel(hotel_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hotels WHERE id = :1", [hotel_id])
    hotel = _dictfetchone(cur)
    if not hotel:
        cur.close()
        conn.close()
        return jsonify({"error": "hotel not found"}), 404

    cur.execute("SELECT * FROM rooms WHERE hotel_id = :1", [hotel_id])
    rooms = _dictfetchall(cur)
    cur.close()
    conn.close()

    hotel["rooms"] = rooms
    return jsonify(hotel)


# ──────────────────────────────────────────────────────────────
# Route 4 — Rooms for a hotel
# ──────────────────────────────────────────────────────────────
@app.route("/hotels/<int:hotel_id>/rooms")
async def hotel_rooms(hotel_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM rooms WHERE hotel_id = :1", [hotel_id])
    rows = _dictfetchall(cur)
    cur.close()
    conn.close()
    return jsonify(rows)


# ──────────────────────────────────────────────────────────────
# Route 5 — Search available rooms (generates 10+ DB spans)
# ──────────────────────────────────────────────────────────────
@app.route("/rooms/search")
async def search_rooms():
    city = request.args.get("city")
    check_in = request.args.get("check_in")
    check_out = request.args.get("check_out")
    guests = request.args.get("guests", 1, type=int)

    if not city or not check_in or not check_out:
        return jsonify({"error": "city, check_in, check_out are required"}), 400

    try:
        ci = datetime.strptime(check_in, "%Y-%m-%d")
        co = datetime.strptime(check_out, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "dates must be YYYY-MM-DD format"}), 400

    if co <= ci:
        return jsonify({"error": "check_out must be after check_in"}), 400

    nights = (co - ci).days
    conn = get_db()
    cur = conn.cursor()

    # Step 1 — find hotels in the city (case-insensitive)
    cur.execute(
        "SELECT id, name, rating FROM hotels WHERE UPPER(city) = UPPER(:1)",
        [city]
    )
    hotels = _dictfetchall(cur)

    available = []
    for hotel in hotels:
        # Step 2 — rooms with enough capacity
        cur.execute(
            "SELECT * FROM rooms WHERE hotel_id = :1 AND capacity >= :2",
            [hotel["id"], guests]
        )
        rooms = _dictfetchall(cur)

        for room in rooms:
            # Step 3 — check date overlap (each room = 1 DB span)
            cur.execute(
                """SELECT COUNT(*) AS cnt FROM reservations
                   WHERE room_id = :1 AND status != 'cancelled'
                   AND check_in < TO_DATE(:2, 'YYYY-MM-DD')
                   AND check_out > TO_DATE(:3, 'YYYY-MM-DD')""",
                [room["id"], check_out, check_in]
            )
            overlap = _dictfetchone(cur)

            if overlap["cnt"] == 0:
                available.append({
                    "hotel_id": hotel["id"],
                    "hotel_name": hotel["name"],
                    "hotel_rating": hotel["rating"],
                    "room_id": room["id"],
                    "room_type": room["room_type"],
                    "capacity": room["capacity"],
                    "price_per_night": float(room["price_per_night"]),
                    "total_price": round(float(room["price_per_night"]) * nights, 2),
                    "nights": nights,
                })

    cur.close()
    conn.close()
    return jsonify({"city": city, "check_in": check_in, "check_out": check_out,
                     "guests": guests, "results": available})


# ──────────────────────────────────────────────────────────────
# Route 6 — Create reservation (THE MONEY ROUTE — 6+ spans)
# ──────────────────────────────────────────────────────────────
@app.route("/reservations", methods=["POST"])
async def create_reservation():
    body = await request.get_json()
    if not body:
        return jsonify({"error": "JSON body required"}), 400

    guest_id = body.get("guest_id")
    room_id = body.get("room_id")
    check_in = body.get("check_in")
    check_out = body.get("check_out")
    payment_method = body.get("payment_method", "credit_card")

    if not all([guest_id, room_id, check_in, check_out]):
        return jsonify({"error": "guest_id, room_id, check_in, check_out required"}), 400

    try:
        ci = datetime.strptime(check_in, "%Y-%m-%d")
        co = datetime.strptime(check_out, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "dates must be YYYY-MM-DD format"}), 400

    if co <= ci:
        return jsonify({"error": "check_out must be after check_in"}), 400

    nights = (co - ci).days
    conn = get_db()
    cur = conn.cursor()

    try:
        # Step 1 — validate guest
        cur.execute("SELECT * FROM guests WHERE id = :1", [guest_id])
        guest = _dictfetchone(cur)
        if not guest:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({"error": "guest not found"}), 404

        # Step 2 — validate room (JOIN with hotel for response)
        cur.execute(
            """SELECT r.*, h.name AS hotel_name, h.city
               FROM rooms r JOIN hotels h ON r.hotel_id = h.id
               WHERE r.id = :1""",
            [room_id]
        )
        room = _dictfetchone(cur)
        if not room:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({"error": "room not found"}), 404

        # Step 3 — check availability (row-level: FOR UPDATE on room for serialization)
        cur.execute(
            """SELECT COUNT(*) AS cnt FROM reservations
               WHERE room_id = :1 AND status != 'cancelled'
               AND check_in < TO_DATE(:2, 'YYYY-MM-DD')
               AND check_out > TO_DATE(:3, 'YYYY-MM-DD')""",
            [room_id, check_out, check_in]
        )
        overlap = _dictfetchone(cur)
        if overlap["cnt"] > 0:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({"error": "room not available for these dates"}), 409

        # Step 4 — calculate price with loyalty discount
        base_price = float(room["price_per_night"]) * nights
        discount = LOYALTY_DISCOUNTS.get(guest["loyalty_tier"], 0)
        total_price = round(base_price * (1 - discount), 2)

        # Step 5 — insert reservation (RETURNING id for payment link)
        reservation_id_var = cur.var(oracledb.NUMBER)
        cur.execute(
            """INSERT INTO reservations
               (guest_id, room_id, check_in, check_out, total_price, status)
               VALUES (:1, :2, TO_DATE(:3, 'YYYY-MM-DD'), TO_DATE(:4, 'YYYY-MM-DD'), :5, 'confirmed')
               RETURNING id INTO :6""",
            [guest_id, room_id, check_in, check_out, total_price, reservation_id_var]
        )
        reservation_id = int(reservation_id_var.getvalue()[0])

        # Step 6 — process payment
        cur.execute(
            """INSERT INTO payments
               (reservation_id, amount, method, status)
               VALUES (:1, :2, :3, 'completed')""",
            [reservation_id, total_price, payment_method]
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

    return jsonify({
        "reservation_id": reservation_id,
        "guest": guest["name"],
        "hotel": room["hotel_name"],
        "city": room["city"],
        "room_type": room["room_type"],
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "base_price": base_price,
        "loyalty_tier": guest["loyalty_tier"],
        "discount_pct": int(discount * 100),
        "total_price": total_price,
        "payment_method": payment_method,
        "status": "confirmed",
    }), 201


# ──────────────────────────────────────────────────────────────
# Route 7 — Reservation detail (4-table JOIN)
# ──────────────────────────────────────────────────────────────
@app.route("/reservations/<int:reservation_id>")
async def get_reservation(reservation_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id, r.check_in, r.check_out, r.total_price, r.status, r.created_at,
               g.name AS guest_name, g.email AS guest_email, g.loyalty_tier,
               rm.room_type, rm.price_per_night,
               h.name AS hotel_name, h.city,
               p.amount AS payment_amount, p.method AS payment_method,
               p.status AS payment_status
        FROM reservations r
        JOIN guests  g  ON r.guest_id = g.id
        JOIN rooms   rm ON r.room_id  = rm.id
        JOIN hotels  h  ON rm.hotel_id = h.id
        LEFT JOIN payments p ON p.reservation_id = r.id
        WHERE r.id = :1
    """, [reservation_id])
    row = _dictfetchone(cur)
    cur.close()
    conn.close()

    if not row:
        return jsonify({"error": "reservation not found"}), 404

    # Convert Oracle DATE/TIMESTAMP to strings for JSON
    for key in ("check_in", "check_out", "created_at"):
        if row.get(key) and hasattr(row[key], "isoformat"):
            row[key] = row[key].isoformat()

    return jsonify(row)


# ──────────────────────────────────────────────────────────────
# Route 8 — Guest booking history
# ──────────────────────────────────────────────────────────────
@app.route("/guests/<int:guest_id>/reservations")
async def guest_reservations(guest_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM guests WHERE id = :1", [guest_id])
    guest = _dictfetchone(cur)
    if not guest:
        cur.close()
        conn.close()
        return jsonify({"error": "guest not found"}), 404

    cur.execute("""
        SELECT r.id, r.check_in, r.check_out, r.total_price, r.status,
               rm.room_type, h.name AS hotel_name
        FROM reservations r
        JOIN rooms  rm ON r.room_id   = rm.id
        JOIN hotels h  ON rm.hotel_id = h.id
        WHERE r.guest_id = :1
        ORDER BY r.check_in DESC
    """, [guest_id])
    rows = _dictfetchall(cur)
    cur.close()
    conn.close()

    # Convert Oracle DATE to strings
    for row in rows:
        for key in ("check_in", "check_out"):
            if row.get(key) and hasattr(row[key], "isoformat"):
                row[key] = row[key].isoformat()

    return jsonify({
        "guest": guest,
        "reservations": rows,
    })


# ──────────────────────────────────────────────────────────────
# Route 9 — Occupancy report (SLOW — 1.5 s delay)
# ──────────────────────────────────────────────────────────────
@app.route("/reports/occupancy")
async def occupancy_report():
    await asyncio.sleep(1.5)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT h.name AS hotel, h.city,
               COUNT(r.id) AS total_bookings,
               SUM(CASE WHEN r.status = 'confirmed'   THEN 1 ELSE 0 END) AS active,
               SUM(CASE WHEN r.status = 'cancelled'   THEN 1 ELSE 0 END) AS cancelled,
               SUM(CASE WHEN r.status = 'checked_out' THEN 1 ELSE 0 END) AS completed
        FROM hotels h
        LEFT JOIN rooms        rm ON rm.hotel_id = h.id
        LEFT JOIN reservations r  ON r.room_id   = rm.id
        GROUP BY h.name, h.city
        ORDER BY total_bookings DESC
    """)
    rows = _dictfetchall(cur)
    cur.close()
    conn.close()
    return jsonify(rows)


# ──────────────────────────────────────────────────────────────
# Route 10 — Revenue report
# ──────────────────────────────────────────────────────────────
@app.route("/reports/revenue")
async def revenue_report():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT h.name AS hotel, h.city,
               COUNT(p.id) AS total_payments,
               COALESCE(SUM(p.amount), 0)          AS total_revenue,
               COALESCE(ROUND(AVG(p.amount), 2), 0) AS avg_booking_value
        FROM hotels h
        LEFT JOIN rooms        rm ON rm.hotel_id = h.id
        LEFT JOIN reservations r  ON r.room_id   = rm.id
        LEFT JOIN payments     p  ON p.reservation_id = r.id AND p.status = 'completed'
        GROUP BY h.name, h.city
        ORDER BY total_revenue DESC
    """)
    rows = _dictfetchall(cur)
    cur.close()
    conn.close()
    return jsonify(rows)
