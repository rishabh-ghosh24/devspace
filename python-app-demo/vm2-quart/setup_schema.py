#!/usr/bin/env python3
"""
setup_schema.py — One-time ADB schema setup for StayEasy Hotel Booking.

Connects as ADMIN to:
  1. Create the STAYEASY user with necessary grants
  2. Create all 5 tables (hotels, rooms, guests, reservations, payments)
  3. Insert seed data

Usage:
  python3 setup_schema.py \
    --dsn '(description=(...))' \
    --admin-password 'YourAdminPassword'

Or set environment variables:
  DB_DSN=...  ADMIN_PASSWORD=...  python3 setup_schema.py
"""

import argparse
import os
import sys

import oracledb


# ── Seed SQL (run as STAYEASY) ──────────────────────────────────────────────

TABLES_DDL = """
-- Hotels
CREATE TABLE hotels (
    id     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name   VARCHAR2(200) NOT NULL,
    city   VARCHAR2(100) NOT NULL,
    rating NUMBER(2,1)   NOT NULL
)
--SPLIT--
-- Rooms
CREATE TABLE rooms (
    id              NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hotel_id        NUMBER        NOT NULL,
    room_type       VARCHAR2(50)  NOT NULL,
    price_per_night NUMBER(10,2)  NOT NULL,
    capacity        NUMBER(3)     NOT NULL,
    CONSTRAINT fk_rooms_hotel FOREIGN KEY (hotel_id) REFERENCES hotels(id)
)
--SPLIT--
-- Guests
CREATE TABLE guests (
    id           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name         VARCHAR2(200) NOT NULL,
    email        VARCHAR2(200) NOT NULL UNIQUE,
    phone        VARCHAR2(30),
    loyalty_tier VARCHAR2(20)  DEFAULT 'standard' NOT NULL
)
--SPLIT--
-- Reservations
CREATE TABLE reservations (
    id          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guest_id    NUMBER        NOT NULL,
    room_id     NUMBER        NOT NULL,
    check_in    DATE          NOT NULL,
    check_out   DATE          NOT NULL,
    total_price NUMBER(10,2)  NOT NULL,
    status      VARCHAR2(20)  DEFAULT 'confirmed' NOT NULL,
    created_at  TIMESTAMP     DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT fk_res_guest FOREIGN KEY (guest_id) REFERENCES guests(id),
    CONSTRAINT fk_res_room  FOREIGN KEY (room_id)  REFERENCES rooms(id)
)
--SPLIT--
-- Payments
CREATE TABLE payments (
    id             NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reservation_id NUMBER       NOT NULL UNIQUE,
    amount         NUMBER(10,2) NOT NULL,
    method         VARCHAR2(30) NOT NULL,
    status         VARCHAR2(20) DEFAULT 'completed' NOT NULL,
    processed_at   TIMESTAMP    DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT fk_pay_res FOREIGN KEY (reservation_id) REFERENCES reservations(id)
)
"""

SEED_SQL = [
    # Hotels (use MERGE for idempotent re-runs)
    """MERGE INTO hotels h USING (SELECT 1 AS id, 'Grand Palace Hotel' AS name, 'London' AS city, 4.8 AS rating FROM dual) s
       ON (h.name = s.name AND h.city = s.city)
       WHEN NOT MATCHED THEN INSERT (name, city, rating) VALUES (s.name, s.city, s.rating)""",
    """MERGE INTO hotels h USING (SELECT 'Seaside Resort' AS name, 'Brighton' AS city, 4.5 AS rating FROM dual) s
       ON (h.name = s.name AND h.city = s.city)
       WHEN NOT MATCHED THEN INSERT (name, city, rating) VALUES (s.name, s.city, s.rating)""",
    """MERGE INTO hotels h USING (SELECT 'City Central Inn' AS name, 'London' AS city, 4.2 AS rating FROM dual) s
       ON (h.name = s.name AND h.city = s.city)
       WHEN NOT MATCHED THEN INSERT (name, city, rating) VALUES (s.name, s.city, s.rating)""",
    """MERGE INTO hotels h USING (SELECT 'Highland Lodge' AS name, 'Edinburgh' AS city, 4.6 AS rating FROM dual) s
       ON (h.name = s.name AND h.city = s.city)
       WHEN NOT MATCHED THEN INSERT (name, city, rating) VALUES (s.name, s.city, s.rating)""",

    # Rooms — need hotel IDs from above, use subquery
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='Grand Palace Hotel') AS hid, 'Standard' AS rt, 120.00 AS ppn, 2 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='Grand Palace Hotel') AS hid, 'Deluxe' AS rt, 200.00 AS ppn, 2 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='Grand Palace Hotel') AS hid, 'Suite' AS rt, 350.00 AS ppn, 4 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='Seaside Resort') AS hid, 'Standard' AS rt, 90.00 AS ppn, 2 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='Seaside Resort') AS hid, 'Ocean View' AS rt, 150.00 AS ppn, 2 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='Seaside Resort') AS hid, 'Family' AS rt, 180.00 AS ppn, 4 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='City Central Inn') AS hid, 'Single' AS rt, 70.00 AS ppn, 1 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='City Central Inn') AS hid, 'Double' AS rt, 100.00 AS ppn, 2 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='City Central Inn') AS hid, 'Executive' AS rt, 160.00 AS ppn, 2 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='Highland Lodge') AS hid, 'Cabin' AS rt, 110.00 AS ppn, 2 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='Highland Lodge') AS hid, 'Lodge Room' AS rt, 140.00 AS ppn, 3 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",
    """MERGE INTO rooms r USING (SELECT (SELECT id FROM hotels WHERE name='Highland Lodge') AS hid, 'Premium' AS rt, 220.00 AS ppn, 4 AS cap FROM dual) s
       ON (r.hotel_id = s.hid AND r.room_type = s.rt)
       WHEN NOT MATCHED THEN INSERT (hotel_id, room_type, price_per_night, capacity) VALUES (s.hid, s.rt, s.ppn, s.cap)""",

    # Guests
    """MERGE INTO guests g USING (SELECT 'Alice Martin' AS name, 'alice@example.com' AS email, '+44-7700-100001' AS phone, 'gold' AS tier FROM dual) s
       ON (g.email = s.email)
       WHEN NOT MATCHED THEN INSERT (name, email, phone, loyalty_tier) VALUES (s.name, s.email, s.phone, s.tier)""",
    """MERGE INTO guests g USING (SELECT 'Bob Singh' AS name, 'bob@example.com' AS email, '+44-7700-100002' AS phone, 'standard' AS tier FROM dual) s
       ON (g.email = s.email)
       WHEN NOT MATCHED THEN INSERT (name, email, phone, loyalty_tier) VALUES (s.name, s.email, s.phone, s.tier)""",
    """MERGE INTO guests g USING (SELECT 'Clara Doe' AS name, 'clara@example.com' AS email, '+44-7700-100003' AS phone, 'platinum' AS tier FROM dual) s
       ON (g.email = s.email)
       WHEN NOT MATCHED THEN INSERT (name, email, phone, loyalty_tier) VALUES (s.name, s.email, s.phone, s.tier)""",
    """MERGE INTO guests g USING (SELECT 'David Chen' AS name, 'david@example.com' AS email, '+44-7700-100004' AS phone, 'silver' AS tier FROM dual) s
       ON (g.email = s.email)
       WHEN NOT MATCHED THEN INSERT (name, email, phone, loyalty_tier) VALUES (s.name, s.email, s.phone, s.tier)""",
    """MERGE INTO guests g USING (SELECT 'Emma Wilson' AS name, 'emma@example.com' AS email, '+44-7700-100005' AS phone, 'standard' AS tier FROM dual) s
       ON (g.email = s.email)
       WHEN NOT MATCHED THEN INSERT (name, email, phone, loyalty_tier) VALUES (s.name, s.email, s.phone, s.tier)""",

    # Reservations (use subqueries to get IDs since IDENTITY-generated)
    """MERGE INTO reservations rv
       USING (
           SELECT (SELECT id FROM guests WHERE email='alice@example.com') AS gid,
                  (SELECT r.id FROM rooms r JOIN hotels h ON r.hotel_id=h.id WHERE h.name='Grand Palace Hotel' AND r.room_type='Standard') AS rid,
                  DATE '2025-03-10' AS ci, DATE '2025-03-14' AS co, 432.00 AS tp, 'checked_out' AS st
           FROM dual
       ) s ON (rv.guest_id = s.gid AND rv.room_id = s.rid AND rv.check_in = s.ci)
       WHEN NOT MATCHED THEN INSERT (guest_id, room_id, check_in, check_out, total_price, status)
            VALUES (s.gid, s.rid, s.ci, s.co, s.tp, s.st)""",
    """MERGE INTO reservations rv
       USING (
           SELECT (SELECT id FROM guests WHERE email='bob@example.com') AS gid,
                  (SELECT r.id FROM rooms r JOIN hotels h ON r.hotel_id=h.id WHERE h.name='Seaside Resort' AND r.room_type='Ocean View') AS rid,
                  DATE '2025-03-20' AS ci, DATE '2025-03-23' AS co, 450.00 AS tp, 'confirmed' AS st
           FROM dual
       ) s ON (rv.guest_id = s.gid AND rv.room_id = s.rid AND rv.check_in = s.ci)
       WHEN NOT MATCHED THEN INSERT (guest_id, room_id, check_in, check_out, total_price, status)
            VALUES (s.gid, s.rid, s.ci, s.co, s.tp, s.st)""",
    """MERGE INTO reservations rv
       USING (
           SELECT (SELECT id FROM guests WHERE email='clara@example.com') AS gid,
                  (SELECT r.id FROM rooms r JOIN hotels h ON r.hotel_id=h.id WHERE h.name='Grand Palace Hotel' AND r.room_type='Suite') AS rid,
                  DATE '2025-04-01' AS ci, DATE '2025-04-05' AS co, 1190.00 AS tp, 'confirmed' AS st
           FROM dual
       ) s ON (rv.guest_id = s.gid AND rv.room_id = s.rid AND rv.check_in = s.ci)
       WHEN NOT MATCHED THEN INSERT (guest_id, room_id, check_in, check_out, total_price, status)
            VALUES (s.gid, s.rid, s.ci, s.co, s.tp, s.st)""",
    """MERGE INTO reservations rv
       USING (
           SELECT (SELECT id FROM guests WHERE email='david@example.com') AS gid,
                  (SELECT r.id FROM rooms r JOIN hotels h ON r.hotel_id=h.id WHERE h.name='City Central Inn' AND r.room_type='Double') AS rid,
                  DATE '2025-03-25' AS ci, DATE '2025-03-28' AS co, 285.00 AS tp, 'cancelled' AS st
           FROM dual
       ) s ON (rv.guest_id = s.gid AND rv.room_id = s.rid AND rv.check_in = s.ci)
       WHEN NOT MATCHED THEN INSERT (guest_id, room_id, check_in, check_out, total_price, status)
            VALUES (s.gid, s.rid, s.ci, s.co, s.tp, s.st)""",
    """MERGE INTO reservations rv
       USING (
           SELECT (SELECT id FROM guests WHERE email='emma@example.com') AS gid,
                  (SELECT r.id FROM rooms r JOIN hotels h ON r.hotel_id=h.id WHERE h.name='Highland Lodge' AND r.room_type='Cabin') AS rid,
                  DATE '2025-04-10' AS ci, DATE '2025-04-13' AS co, 330.00 AS tp, 'confirmed' AS st
           FROM dual
       ) s ON (rv.guest_id = s.gid AND rv.room_id = s.rid AND rv.check_in = s.ci)
       WHEN NOT MATCHED THEN INSERT (guest_id, room_id, check_in, check_out, total_price, status)
            VALUES (s.gid, s.rid, s.ci, s.co, s.tp, s.st)""",
    """MERGE INTO reservations rv
       USING (
           SELECT (SELECT id FROM guests WHERE email='alice@example.com') AS gid,
                  (SELECT r.id FROM rooms r JOIN hotels h ON r.hotel_id=h.id WHERE h.name='Seaside Resort' AND r.room_type='Family') AS rid,
                  DATE '2025-04-15' AS ci, DATE '2025-04-20' AS co, 810.00 AS tp, 'confirmed' AS st
           FROM dual
       ) s ON (rv.guest_id = s.gid AND rv.room_id = s.rid AND rv.check_in = s.ci)
       WHEN NOT MATCHED THEN INSERT (guest_id, room_id, check_in, check_out, total_price, status)
            VALUES (s.gid, s.rid, s.ci, s.co, s.tp, s.st)""",

    # Payments (one per reservation — link by guest+room+checkin)
    """MERGE INTO payments p
       USING (
           SELECT rv.id AS rid, 432.00 AS amt, 'credit_card' AS meth, 'completed' AS st
           FROM reservations rv
           JOIN guests g ON rv.guest_id = g.id
           JOIN rooms r ON rv.room_id = r.id
           JOIN hotels h ON r.hotel_id = h.id
           WHERE g.email='alice@example.com' AND h.name='Grand Palace Hotel' AND r.room_type='Standard' AND rv.check_in = DATE '2025-03-10'
       ) s ON (p.reservation_id = s.rid)
       WHEN NOT MATCHED THEN INSERT (reservation_id, amount, method, status) VALUES (s.rid, s.amt, s.meth, s.st)""",
    """MERGE INTO payments p
       USING (
           SELECT rv.id AS rid, 450.00 AS amt, 'debit_card' AS meth, 'completed' AS st
           FROM reservations rv
           JOIN guests g ON rv.guest_id = g.id
           JOIN rooms r ON rv.room_id = r.id
           JOIN hotels h ON r.hotel_id = h.id
           WHERE g.email='bob@example.com' AND h.name='Seaside Resort' AND r.room_type='Ocean View' AND rv.check_in = DATE '2025-03-20'
       ) s ON (p.reservation_id = s.rid)
       WHEN NOT MATCHED THEN INSERT (reservation_id, amount, method, status) VALUES (s.rid, s.amt, s.meth, s.st)""",
    """MERGE INTO payments p
       USING (
           SELECT rv.id AS rid, 1190.00 AS amt, 'credit_card' AS meth, 'completed' AS st
           FROM reservations rv
           JOIN guests g ON rv.guest_id = g.id
           JOIN rooms r ON rv.room_id = r.id
           JOIN hotels h ON r.hotel_id = h.id
           WHERE g.email='clara@example.com' AND h.name='Grand Palace Hotel' AND r.room_type='Suite' AND rv.check_in = DATE '2025-04-01'
       ) s ON (p.reservation_id = s.rid)
       WHEN NOT MATCHED THEN INSERT (reservation_id, amount, method, status) VALUES (s.rid, s.amt, s.meth, s.st)""",
    """MERGE INTO payments p
       USING (
           SELECT rv.id AS rid, 285.00 AS amt, 'credit_card' AS meth, 'refunded' AS st
           FROM reservations rv
           JOIN guests g ON rv.guest_id = g.id
           JOIN rooms r ON rv.room_id = r.id
           JOIN hotels h ON r.hotel_id = h.id
           WHERE g.email='david@example.com' AND h.name='City Central Inn' AND r.room_type='Double' AND rv.check_in = DATE '2025-03-25'
       ) s ON (p.reservation_id = s.rid)
       WHEN NOT MATCHED THEN INSERT (reservation_id, amount, method, status) VALUES (s.rid, s.amt, s.meth, s.st)""",
    """MERGE INTO payments p
       USING (
           SELECT rv.id AS rid, 330.00 AS amt, 'bank_transfer' AS meth, 'completed' AS st
           FROM reservations rv
           JOIN guests g ON rv.guest_id = g.id
           JOIN rooms r ON rv.room_id = r.id
           JOIN hotels h ON r.hotel_id = h.id
           WHERE g.email='emma@example.com' AND h.name='Highland Lodge' AND r.room_type='Cabin' AND rv.check_in = DATE '2025-04-10'
       ) s ON (p.reservation_id = s.rid)
       WHEN NOT MATCHED THEN INSERT (reservation_id, amount, method, status) VALUES (s.rid, s.amt, s.meth, s.st)""",
    """MERGE INTO payments p
       USING (
           SELECT rv.id AS rid, 810.00 AS amt, 'credit_card' AS meth, 'completed' AS st
           FROM reservations rv
           JOIN guests g ON rv.guest_id = g.id
           JOIN rooms r ON rv.room_id = r.id
           JOIN hotels h ON r.hotel_id = h.id
           WHERE g.email='alice@example.com' AND h.name='Seaside Resort' AND r.room_type='Family' AND rv.check_in = DATE '2025-04-15'
       ) s ON (p.reservation_id = s.rid)
       WHEN NOT MATCHED THEN INSERT (reservation_id, amount, method, status) VALUES (s.rid, s.amt, s.meth, s.st)""",
]


def main():
    parser = argparse.ArgumentParser(description="Setup StayEasy ADB schema")
    parser.add_argument("--dsn", default=os.environ.get("DB_DSN", ""),
                        help="ADB TLS connect string")
    parser.add_argument("--admin-password", default=os.environ.get("ADMIN_PASSWORD", ""),
                        help="ADMIN password for ADB")
    parser.add_argument("--app-password", default=os.environ.get("APP_PASSWORD", ""),
                        help="Password to set for STAYEASY user")
    parser.add_argument("--drop", action="store_true",
                        help="Drop and recreate STAYEASY user (destroys all data)")
    args = parser.parse_args()

    dsn = args.dsn
    admin_pw = args.admin_password
    app_pw = args.app_password

    if not dsn or not admin_pw or not app_pw:
        print("ERROR: --dsn, --admin-password, and --app-password are required")
        print("       (or set DB_DSN, ADMIN_PASSWORD, APP_PASSWORD env vars)")
        sys.exit(1)

    # ── Connect as ADMIN ─────────────────────────────────────────────────
    print(f"Connecting to ADB as ADMIN...")
    admin_conn = oracledb.connect(user="ADMIN", password=admin_pw, dsn=dsn)
    admin_cur = admin_conn.cursor()

    # ── Drop user if --drop flag ─────────────────────────────────────────
    if args.drop:
        print("Dropping STAYEASY user (--drop flag)...")
        try:
            admin_cur.execute("DROP USER stayeasy CASCADE")
            print("  Dropped existing STAYEASY user")
        except oracledb.DatabaseError as e:
            if "ORA-01918" in str(e):  # user does not exist
                print("  STAYEASY user did not exist, skipping drop")
            else:
                raise

    # ── Create STAYEASY user ─────────────────────────────────────────────
    print("Creating STAYEASY user...")
    try:
        admin_cur.execute(f"CREATE USER stayeasy IDENTIFIED BY \"{app_pw}\"")
        print("  Created user STAYEASY")
    except oracledb.DatabaseError as e:
        if "ORA-01920" in str(e):  # user name already exists
            print("  STAYEASY user already exists, skipping creation")
        else:
            raise

    # ── Grant privileges ─────────────────────────────────────────────────
    grants = [
        "GRANT CONNECT TO stayeasy",
        "GRANT RESOURCE TO stayeasy",
        "GRANT UNLIMITED TABLESPACE TO stayeasy",
    ]
    for g in grants:
        admin_cur.execute(g)
    print("  Grants applied")

    admin_conn.commit()
    admin_cur.close()
    admin_conn.close()

    # ── Connect as STAYEASY ──────────────────────────────────────────────
    print("Connecting as STAYEASY...")
    app_conn = oracledb.connect(user="stayeasy", password=app_pw, dsn=dsn)
    app_cur = app_conn.cursor()

    # ── Create tables ────────────────────────────────────────────────────
    print("Creating tables...")
    for ddl in TABLES_DDL.split("--SPLIT--"):
        ddl = ddl.strip()
        if not ddl:
            continue
        # Extract table name for logging
        table_name = ddl.split("CREATE TABLE ")[-1].split("(")[0].strip() if "CREATE TABLE" in ddl else "?"
        try:
            app_cur.execute(ddl)
            print(f"  Created table: {table_name}")
        except oracledb.DatabaseError as e:
            if "ORA-00955" in str(e):  # name already used
                print(f"  Table {table_name} already exists, skipping")
            else:
                raise

    # ── Seed data ────────────────────────────────────────────────────────
    print("Inserting seed data...")
    for i, sql in enumerate(SEED_SQL):
        app_cur.execute(sql)
    app_conn.commit()
    print(f"  Executed {len(SEED_SQL)} MERGE statements")

    # ── Verify ───────────────────────────────────────────────────────────
    print("\nVerification:")
    for table in ["hotels", "rooms", "guests", "reservations", "payments"]:
        app_cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = app_cur.fetchone()[0]
        print(f"  {table}: {count} rows")

    app_cur.close()
    app_conn.close()
    print("\nDone! Schema is ready.")


if __name__ == "__main__":
    main()
