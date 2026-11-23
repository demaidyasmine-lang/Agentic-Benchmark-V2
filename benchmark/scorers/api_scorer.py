
import json

from inspect_ai.scorer import scorer, accuracy, Score
from inspect_ai.util import sandbox


@scorer(metrics=[accuracy()])
def api_state_scorer():

    async def score(state, target):

        operation = state.metadata.get("operation")
        sample_id = str(state.sample_id)

        try:
            output = json.loads(state.output.completion)

            if not isinstance(output, dict):
                raise ValueError("La sortie de l'agent doit être un objet JSON.")

            expected_statuses = {
                "get_user": 200,
                "create_user": 201,
                "update_user": 200,
                "delete_user": 200,
                "filter_users": 200,
                "validate_missing_email": 400,
                "not_found": 404,
                "prevent_invalid_update": 400,
            }

            if operation not in expected_statuses:
                raise ValueError(f"Opération inconnue : {operation}")

            expected_status = expected_statuses[operation]
            status_ok = output.get("http_status") == expected_status
            response = output.get("response")

            if operation == "filter_users":
                if not isinstance(response, list):
                    response_ok = False
                else:
                    response_ok = (
                        all(isinstance(user, dict) for user in response)
                        and [user.get("id") for user in response] == [1, 3]
                    )
            else:
                response_ok = isinstance(response, dict)

                if response_ok:
                    if operation == "get_user":
                        response_ok = (
                            response.get("id") == 1
                            and response.get("name") == "Alice"
                            and response.get("email") == "alice@example.com"
                        )

                    elif operation == "create_user":
                        response_ok = (
                            response.get("id") == 4
                            and response.get("name") == "Charlie"
                            and response.get("email") == "charlie@example.com"
                        )

                    elif operation == "update_user":
                        response_ok = (
                            response.get("id") == 1
                            and response.get("name") == "Alice Johnson"
                            and response.get("email") == "alice.johnson@example.com"
                        )

                    elif operation == "delete_user":
                        response_ok = response.get("message") == "User deleted"

                    elif operation == "validate_missing_email":
                        response_ok = response.get("error") == "Invalid name or email"

                    elif operation == "not_found":
                        response_ok = response.get("error") == "User not found"

                    elif operation == "prevent_invalid_update":
                        response_ok = response.get("error") == "Invalid name or email"

            verification_script = r'''
import sqlite3
import json

db_path = "/workspace/benchmark/api/data/__SAMPLE_ID__.db"

with sqlite3.connect(db_path) as connection:
    connection.row_factory = sqlite3.Row

    users = connection.execute(
        "SELECT id, name, email, role FROM users ORDER BY id"
    ).fetchall()

actual = [dict(user) for user in users]

expected = [
    {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
    {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
    {"id": 3, "name": "David", "email": "david@example.com", "role": "admin"},
]

operation = "__OPERATION__"

if operation == "create_user":
    expected.append({
        "id": 4,
        "name": "Charlie",
        "email": "charlie@example.com",
        "role": "user"
    })

elif operation == "update_user":
    expected[0]["name"] = "Alice Johnson"
    expected[0]["email"] = "alice.johnson@example.com"

elif operation == "delete_user":
    expected = [user for user in expected if user["id"] != 2]

passed = actual == expected

print(json.dumps({
    "database_valid": passed,
    "actual_users": actual,
    "expected_users": expected
}))
'''

            verification_script = verification_script.replace(
                "__SAMPLE_ID__", sample_id
            ).replace("__OPERATION__", operation)

            verification = await sandbox().exec(
                ["python", "-c", verification_script],
                timeout=20
            )

            if (
                not verification.success
                or verification.returncode != 0
            ):
                raise RuntimeError(
                    f"Échec de la vérification Sandbox : "
                    f"{verification.stderr}"
                )

            if not verification.stdout.strip():
                raise ValueError("La vérification Sandbox n'a retourné aucun résultat.")

            database_result = json.loads(verification.stdout.strip())

            if not isinstance(database_result, dict):
                raise ValueError("Résultat de vérification de base de données invalide.")

            database_ok = database_result.get("database_valid") is True

            passed = status_ok and response_ok and database_ok

            explanation = (
                f"HTTP attendu={expected_status}, "
                f"HTTP obtenu={output.get('http_status')}; "
                f"réponse correcte={response_ok}; "
                f"état base de données correct={database_ok}"
            )

            return Score(
                value=1 if passed else 0,
                explanation=explanation
            )

        except Exception as error:
            return Score(
                value=0,
                explanation=f"Erreur pendant la vérification : {error}"
            )

    return score
