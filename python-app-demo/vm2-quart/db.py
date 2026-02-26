"""
db.py — Oracle ADB connection helper for StayEasy Hotel Booking.

Uses oracledb thin mode (no Oracle Instant Client needed).
Connection via TLS (wallet-less) to OCI Autonomous Database.
"""

import os
import logging
import oracledb

log = logging.getLogger(__name__)

# Connection details from environment (.env loaded by systemd)
DB_USER = os.environ.get("DB_USER", "stayeasy")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_DSN = os.environ.get("DB_DSN", "")


def _make_dict_row_factory(cursor):
    """Return a rowfactory that produces dict-like rows from cursor.description.

    Called once after each execute() — maps column names (lowercased) to values,
    so row["column_name"] works just like sqlite3.Row did.
    """
    columns = [col[0].lower() for col in cursor.description]

    def create_row(*args):
        return dict(zip(columns, args))

    return create_row


def get_db():
    """Return a new Oracle connection with autocommit off.

    The caller is responsible for commit/rollback/close.
    Each cursor.execute() sets a dict rowfactory automatically via
    the outputtypehandler.
    """
    if not DB_DSN or not DB_PASSWORD:
        raise RuntimeError("DB_DSN and DB_PASSWORD must be set in environment")

    conn = oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)
    conn.autocommit = False
    return conn


def seed():
    """No-op — schema and seed data are created by setup_schema.py.

    Kept for compatibility with app.py's @app.before_serving call.
    Verifies connectivity on startup.
    """
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM hotels")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        log.info("ADB connection OK — hotels table has %d rows", count)
    except Exception as e:
        log.error("ADB connection check failed: %s", e)
        raise
