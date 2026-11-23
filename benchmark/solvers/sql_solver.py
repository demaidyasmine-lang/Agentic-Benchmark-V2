import json

from inspect_ai.solver import solver, TaskState, Generate
from inspect_ai.model import ModelOutput
from inspect_ai.util import sandbox


@solver
def deterministic_sql_solver():

    async def solve(state: TaskState, generate: Generate) -> TaskState:

        operation = state.metadata.get("operation")
        sample_id = str(state.sample_id)

        sql_script = f"""
import sqlite3
import json

db_path = f'/workspace/benchmark/datasets/data/{sample_id}.db'

with sqlite3.connect(db_path) as connection:
    connection.execute("PRAGMA foreign_keys = ON")

    connection.execute("DROP TABLE IF EXISTS orders")
    connection.execute("DROP TABLE IF EXISTS customers")

    connection.execute(
        "CREATE TABLE customers (id TEXT PRIMARY KEY, name TEXT NOT NULL, status INTEGER NOT NULL CHECK (status IN (0, 1)))"
    )

    connection.execute(
        "CREATE TABLE orders (id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, amount REAL NOT NULL, FOREIGN KEY (customer_id) REFERENCES customers(id))"
    )

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

    result = {{"operation": "{operation}", "success": True}}

    if "{operation}" == "update_one":
        cursor = connection.execute(
            "UPDATE customers SET status = 1 WHERE id = ?",
            ("C-001",)
        )
        result["rows_affected"] = cursor.rowcount

    elif "{operation}" == "delete_one":
        cursor = connection.execute(
            "DELETE FROM customers WHERE id = ?",
            ("C-004",)
        )
        result["rows_affected"] = cursor.rowcount

    elif "{operation}" == "insert_one":
        connection.execute(
            "INSERT INTO customers VALUES (?, ?, ?)",
            ("C-005", "Client Zeta", 1)
        )
        result["inserted"] = "C-005"

    elif "{operation}" == "update_multiple":
        cursor = connection.execute(
            "UPDATE customers SET status = 1 WHERE status = 0"
        )
        result["rows_affected"] = cursor.rowcount

    elif "{operation}" == "conditional_update":
        cursor = connection.execute(
            "UPDATE customers SET status = 1 WHERE status = 0 AND id LIKE 'C-00%'"
        )
        result["rows_affected"] = cursor.rowcount

    elif "{operation}" == "aggregate":
        row = connection.execute(
            "SELECT COUNT(*), SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) FROM customers"
        ).fetchone()

        result["total_clients"] = row[0]
        result["active_clients"] = row[1]

    elif "{operation}" == "join":
        rows = connection.execute(
            "SELECT orders.id, customers.name, orders.amount FROM orders JOIN customers ON orders.customer_id = customers.id ORDER BY orders.id"
        ).fetchall()

        result["orders"] = rows

    elif "{operation}" == "constraint_violation":
        try:
            connection.execute(
                "INSERT INTO customers VALUES (?, ?, ?)",
                ("C-999", "Client Invalid", 5)
            )
            result["rejected"] = False
        except sqlite3.IntegrityError:
            result["rejected"] = True

    elif "{operation}" == "prevent_unauthorized_changes":
        cursor = connection.execute(
            "UPDATE customers SET status = 1 WHERE id = ?",
            ("C-001",)
        )
        result["rows_affected"] = cursor.rowcount

    elif "{operation}" == "regression_check":
        cursor = connection.execute(
            "UPDATE customers SET status = 1 WHERE id = ?",
            ("C-002",)
        )
        result["rows_affected"] = cursor.rowcount

    else:
        raise ValueError("Unknown SQL operation")

    connection.commit()

print(json.dumps(result))
"""

        execution = await sandbox().exec(
            ["python", "-c", sql_script],
            timeout=30,
        )

        if execution.success:
            message = execution.stdout.strip()
        else:
            message = json.dumps({
                "success": False,
                "error": execution.stderr.strip(),
            })

        state.output = ModelOutput.from_content(
            model="deterministic-sql-agent",
            content=message,
        )

        return state

    return solve
