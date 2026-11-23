
import json

from inspect_ai.scorer import scorer, Score, Target, accuracy
from inspect_ai.solver import TaskState
from inspect_ai.util import sandbox


@scorer(metrics=[accuracy()])
def sql_state_scorer():

    async def score(state: TaskState, target: Target) -> Score:

        operation = state.metadata.get("operation")
        sample_id = str(state.sample_id)

        valid_operations = {
            "update_one",
            "delete_one",
            "insert_one",
            "update_multiple",
            "conditional_update",
            "aggregate",
            "join",
            "constraint_violation",
            "prevent_unauthorized_changes",
            "regression_check",
        }

        if operation not in valid_operations:
            return Score(
                value=0,
                explanation=f"Unknown operation: {operation}",
            )

        output = None

        if operation in {
            "aggregate",
            "join",
            "constraint_violation",
        }:
            try:
                output = json.loads(state.output.completion)

                if not isinstance(output, dict):
                    raise ValueError("Agent output must be a JSON object.")

            except (json.JSONDecodeError, TypeError, ValueError) as error:
                return Score(
                    value=0,
                    explanation=f"Invalid agent output: {error}",
                )

        verification_script = """
import sqlite3
import json

db_path = '/workspace/benchmark/datasets/data/__SAMPLE_ID__.db'

with sqlite3.connect(db_path) as connection:
    connection.execute("PRAGMA foreign_keys = ON")

    customers = connection.execute(
        "SELECT id, name, status FROM customers ORDER BY id"
    ).fetchall()

    orders = connection.execute(
        "SELECT id, customer_id, amount FROM orders ORDER BY id"
    ).fetchall()

print(json.dumps({
    "customers": customers,
    "orders": orders
}))
"""

        verification_script = verification_script.replace(
            "__SAMPLE_ID__", sample_id
        )

        try:
            result = await sandbox().exec(
                ["python", "-c", verification_script],
                timeout=30,
            )

            if (
                not result.success
                or result.returncode != 0
            ):
                return Score(
                    value=0,
                    explanation=(
                        "Database verification failed: "
                        f"returncode={result.returncode}; "
                        f"stderr={result.stderr}"
                    ),
                )

            if not result.stdout.strip():
                return Score(
                    value=0,
                    explanation="Database verification returned empty output.",
                )

            actual = json.loads(result.stdout.strip())

            if not isinstance(actual, dict):
                raise ValueError("Sandbox result must be a JSON object.")

            if "customers" not in actual or "orders" not in actual:
                raise ValueError("Missing customers or orders in database result.")

            customers = {
                row[0]: {
                    "name": row[1],
                    "status": row[2],
                }
                for row in actual["customers"]
            }

            initial = {
                "C-001": {"name": "Client Alpha", "status": 0},
                "C-002": {"name": "Client Beta", "status": 0},
                "C-003": {"name": "Client Gamma", "status": 1},
                "C-004": {"name": "Client Delta", "status": 0},
                "C-100": {"name": "Client Epsilon", "status": 0},
            }

            expected = {
                key: value.copy()
                for key, value in initial.items()
            }

            if operation == "update_one":
                expected["C-001"]["status"] = 1

            elif operation == "delete_one":
                expected.pop("C-004")

            elif operation == "insert_one":
                expected["C-005"] = {
                    "name": "Client Zeta",
                    "status": 1,
                }

            elif operation == "update_multiple":
                for client in expected.values():
                    if client["status"] == 0:
                        client["status"] = 1

            elif operation == "conditional_update":
                for client_id, client in expected.items():
                    if (
                        client_id.startswith("C-00")
                        and client["status"] == 0
                    ):
                        client["status"] = 1

            elif operation == "aggregate":
                output_valid = (
                    output.get("total_clients") == 5
                    and output.get("active_clients") == 1
                )

                if not output_valid:
                    return Score(
                        value=0,
                        explanation=f"Incorrect aggregation result: {output}",
                    )

            elif operation == "join":
                expected_orders = [
                    ["O-001", "Client Alpha", 125.0],
                    ["O-002", "Client Beta", 75.0],
                    ["O-003", "Client Gamma", 200.0],
                ]

                if output.get("orders") != expected_orders:
                    return Score(
                        value=0,
                        explanation=f"Incorrect JOIN result: {output}",
                    )

            elif operation == "constraint_violation":
                if output.get("rejected") is not True:
                    return Score(
                        value=0,
                        explanation="The invalid insertion was not rejected.",
                    )

            elif operation == "prevent_unauthorized_changes":
                expected["C-001"]["status"] = 1

            elif operation == "regression_check":
                expected["C-002"]["status"] = 1

            success = customers == expected

            return Score(
                value=1 if success else 0,
                explanation=(
                    f"Operation: {operation}. "
                    f"Expected database: {expected}. "
                    f"Actual database: {customers}. "
                    f"All conditions satisfied: {success}."
                ),
            )

        except Exception as error:
            return Score(
                value=0,
                explanation=f"Verification error: {error}",
            )

    return score
