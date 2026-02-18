import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "hotel.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def seed():
    conn = get_db()
    conn.executescript("""
        -- Hotels
        CREATE TABLE IF NOT EXISTS hotels (
            id     INTEGER PRIMARY KEY,
            name   TEXT NOT NULL,
            city   TEXT NOT NULL,
            rating REAL NOT NULL
        );

        -- Rooms
        CREATE TABLE IF NOT EXISTS rooms (
            id              INTEGER PRIMARY KEY,
            hotel_id        INTEGER NOT NULL,
            room_type       TEXT NOT NULL,
            price_per_night REAL NOT NULL,
            capacity        INTEGER NOT NULL,
            FOREIGN KEY (hotel_id) REFERENCES hotels(id)
        );

        -- Guests
        CREATE TABLE IF NOT EXISTS guests (
            id           INTEGER PRIMARY KEY,
            name         TEXT NOT NULL,
            email        TEXT NOT NULL UNIQUE,
            phone        TEXT,
            loyalty_tier TEXT NOT NULL DEFAULT 'standard'
        );

        -- Reservations
        CREATE TABLE IF NOT EXISTS reservations (
            id          INTEGER PRIMARY KEY,
            guest_id    INTEGER NOT NULL,
            room_id     INTEGER NOT NULL,
            check_in    TEXT NOT NULL,
            check_out   TEXT NOT NULL,
            total_price REAL NOT NULL,
            status      TEXT NOT NULL DEFAULT 'confirmed',
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (guest_id) REFERENCES guests(id),
            FOREIGN KEY (room_id)  REFERENCES rooms(id)
        );

        -- Payments
        CREATE TABLE IF NOT EXISTS payments (
            id             INTEGER PRIMARY KEY,
            reservation_id INTEGER NOT NULL UNIQUE,
            amount         REAL NOT NULL,
            method         TEXT NOT NULL,
            status         TEXT NOT NULL DEFAULT 'completed',
            processed_at   TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (reservation_id) REFERENCES reservations(id)
        );

        -- =========================================================
        -- Seed data
        -- =========================================================

        -- Hotels (4 hotels, 3 cities)
        INSERT OR IGNORE INTO hotels VALUES
            (1, 'Grand Palace Hotel', 'London',    4.8),
            (2, 'Seaside Resort',     'Brighton',  4.5),
            (3, 'City Central Inn',   'London',    4.2),
            (4, 'Highland Lodge',     'Edinburgh', 4.6);

        -- Rooms (3 per hotel = 12 total)
        INSERT OR IGNORE INTO rooms VALUES
            ( 1, 1, 'Standard',   120.00, 2),
            ( 2, 1, 'Deluxe',     200.00, 2),
            ( 3, 1, 'Suite',      350.00, 4),
            ( 4, 2, 'Standard',    90.00, 2),
            ( 5, 2, 'Ocean View', 150.00, 2),
            ( 6, 2, 'Family',     180.00, 4),
            ( 7, 3, 'Single',      70.00, 1),
            ( 8, 3, 'Double',     100.00, 2),
            ( 9, 3, 'Executive',  160.00, 2),
            (10, 4, 'Cabin',      110.00, 2),
            (11, 4, 'Lodge Room', 140.00, 3),
            (12, 4, 'Premium',    220.00, 4);

        -- Guests (5, various loyalty tiers)
        INSERT OR IGNORE INTO guests VALUES
            (1, 'Alice Martin', 'alice@example.com', '+44-7700-100001', 'gold'),
            (2, 'Bob Singh',    'bob@example.com',   '+44-7700-100002', 'standard'),
            (3, 'Clara Doe',    'clara@example.com',  '+44-7700-100003', 'platinum'),
            (4, 'David Chen',   'david@example.com',  '+44-7700-100004', 'silver'),
            (5, 'Emma Wilson',  'emma@example.com',   '+44-7700-100005', 'standard');

        -- Reservations (6, mix of statuses and dates)
        INSERT OR IGNORE INTO reservations VALUES
            (1, 1, 1, '2025-03-10', '2025-03-14',  432.00, 'checked_out', '2025-03-01 10:00:00'),
            (2, 2, 5, '2025-03-20', '2025-03-23',  450.00, 'confirmed',   '2025-03-15 14:30:00'),
            (3, 3, 3, '2025-04-01', '2025-04-05', 1190.00, 'confirmed',   '2025-03-20 09:15:00'),
            (4, 4, 8, '2025-03-25', '2025-03-28',  285.00, 'cancelled',   '2025-03-18 16:45:00'),
            (5, 5, 10,'2025-04-10', '2025-04-13',  330.00, 'confirmed',   '2025-03-25 11:00:00'),
            (6, 1, 6, '2025-04-15', '2025-04-20',  810.00, 'confirmed',   '2025-04-01 08:30:00');

        -- Payments (one per reservation)
        INSERT OR IGNORE INTO payments VALUES
            (1, 1,  432.00, 'credit_card',   'completed',  '2025-03-01 10:01:00'),
            (2, 2,  450.00, 'debit_card',    'completed',  '2025-03-15 14:31:00'),
            (3, 3, 1190.00, 'credit_card',   'completed',  '2025-03-20 09:16:00'),
            (4, 4,  285.00, 'credit_card',   'refunded',   '2025-03-18 16:46:00'),
            (5, 5,  330.00, 'bank_transfer', 'completed',  '2025-03-25 11:01:00'),
            (6, 6,  810.00, 'credit_card',   'completed',  '2025-04-01 08:31:00');
    """)
    conn.commit()
    conn.close()
