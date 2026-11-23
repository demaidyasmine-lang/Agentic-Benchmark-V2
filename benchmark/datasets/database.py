import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "data" / "customers.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

with sqlite3.connect(db_path) as connection:
    connection.execute("DROP TABLE IF EXISTS orders")
    connection.execute("DROP TABLE IF EXISTS customers")

    connection.execute("""
        CREATE TABLE customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status INTEGER NOT NULL CHECK (status IN (0, 1))
        )
    """)

    connection.execute("""
        CREATE TABLE orders (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)

    connection.executemany(
        "INSERT INTO customers VALUES (?, ?, ?)",
        [
            ("C-001", "Client Alpha", 0),
            ("C-002", "Client Beta", 0),
            ("C-003", "Client Gamma", 1),
            ("C-004", "Client Delta", 0),
            ("C-100", "Client Epsilon", 0),
        ],
    )

    connection.executemany(
        "INSERT INTO orders VALUES (?, ?, ?)",
        [
            ("O-001", "C-001", 125.0),
            ("O-002", "C-002", 75.0),
            ("O-003", "C-003", 200.0),
        ],
    )

print("Base initialisée avec 5 clients et 3 commandes.")
