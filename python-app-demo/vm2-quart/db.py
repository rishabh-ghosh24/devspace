import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "retail.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def seed():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id       INTEGER PRIMARY KEY,
            name     TEXT,
            category TEXT,
            price    REAL,
            stock    INTEGER
        );

        CREATE TABLE IF NOT EXISTS customers (
            id    INTEGER PRIMARY KEY,
            name  TEXT,
            email TEXT,
            city  TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            id          INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id  INTEGER,
            quantity    INTEGER,
            total       REAL,
            status      TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(product_id)  REFERENCES products(id)
        );

        INSERT OR IGNORE INTO products VALUES
            (1, 'Wireless Headphones', 'Electronics',  79.99, 120),
            (2, 'Running Shoes',       'Footwear',     59.99, 200),
            (3, 'Coffee Maker',        'Appliances',   49.99,  85),
            (4, 'Yoga Mat',            'Sports',       29.99, 300),
            (5, 'Laptop Bag',          'Accessories',  39.99, 150);

        INSERT OR IGNORE INTO customers VALUES
            (1, 'Alice Martin', 'alice@example.com', 'London'),
            (2, 'Bob Singh',    'bob@example.com',   'Manchester'),
            (3, 'Clara Doe',    'clara@example.com', 'Edinburgh');

        INSERT OR IGNORE INTO orders VALUES
            (1, 1, 1, 2, 159.98, 'shipped'),
            (2, 2, 3, 1,  49.99, 'pending'),
            (3, 3, 2, 1,  59.99, 'delivered'),
            (4, 1, 4, 3,  89.97, 'processing');
    """)
    conn.commit()
    conn.close()
