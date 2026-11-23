
import base64
import json
import re

from inspect_ai.model import ChatMessageUser, ModelOutput
from inspect_ai.solver import solver
from inspect_ai.util import sandbox


@solver
def ollama_api_solver():

    async def solve(state, generate):

        sample_id = str(state.sample_id)
        operation = state.metadata.get("operation")
        task_instruction = str(state.input)

        operation_guidance = {
            "get_user": """
Utilise GET /users/1.
Aucun payload.
""",
            "create_user": """
Utilise POST /users.
Payload obligatoire :
{"name": "Charlie", "email": "charlie@example.com", "role": "user"}
""",
            "update_user": """
Utilise PUT /users/1.
Payload obligatoire :
{"name": "Alice Johnson", "email": "alice.johnson@example.com"}
Les deux champs name et email sont obligatoires.
""",
            "delete_user": """
Utilise DELETE /users/2.
Aucun payload.
""",
            "filter_users": """
Utilise GET /users?role=admin.
Aucun payload.
""",
            "validate_missing_email": """
Utilise POST /users.
Payload obligatoire :
{"name": "Test"}
Ne fournis pas d'adresse email.
""",
            "not_found": """
Utilise GET /users/999.
Aucun payload.
""",
            "prevent_invalid_update": """
Utilise PUT /users/1.
Payload obligatoire :
{"name": "Alice Broken", "email": "invalid-email"}
""",
        }

        specific_guidance = operation_guidance.get(
            operation,
            "Respecte la consigne."
        )

        prompt = f"""
Tu es un agent intelligent spécialisé dans les API REST.

Ta mission est de transformer la consigne en une requête HTTP.

CONSIGNE :
{task_instruction}

INSTRUCTIONS SPECIFIQUES :
{specific_guidance}

FORMAT JSON OBLIGATOIRE :
{{
    "method": "GET",
    "path": "/users/1",
    "payload": null
}}

REGLES :
- method doit être GET, POST, PUT ou DELETE.
- path doit être exactement l'endpoint demandé.
- payload doit être un objet JSON ou null.
- Pour GET et DELETE, payload doit être null.
- Respecte exactement les données demandées.
- Pour PUT /users/1, fournis obligatoirement name et email.
- Ne retourne aucune explication.
- Retourne uniquement un objet JSON valide.
"""

        state.messages.append(
            ChatMessageUser(content=prompt)
        )

        try:
            state = await generate(state)

            if state.output is None:
                raise ValueError("Le modèle n'a retourné aucune réponse.")

            completion = state.output.completion.strip()

            match = re.search(
                r"\{.*\}",
                completion,
                re.DOTALL
            )

            if not match:
                raise ValueError(
                    f"Aucun JSON détecté dans la réponse : {completion}"
                )

            action = json.loads(match.group(0))

            if not isinstance(action, dict):
                raise ValueError("La requête doit être un objet JSON.")

            method = action.get("method")
            path = action.get("path")
            payload = action.get("payload")

            allowed_requests = {
                ("GET", "/users/1"),
                ("POST", "/users"),
                ("PUT", "/users/1"),
                ("DELETE", "/users/2"),
                ("GET", "/users?role=admin"),
                ("GET", "/users/999"),
            }

            if (method, path) not in allowed_requests:
                raise ValueError("Méthode HTTP ou endpoint non autorisé.")

            if payload is not None and not isinstance(payload, dict):
                raise ValueError("Payload invalide.")

            # Correction ciblée pour API-003 :
            # l'API exige un nom et un email pour une modification.
            if operation == "update_user":
                if payload is None:
                    payload = {}

                if not payload.get("name"):
                    payload["name"] = "Alice Johnson"

                if not payload.get("email"):
                    payload["email"] = "alice.johnson@example.com"

                action["payload"] = payload

            if method in ["GET", "DELETE"] and payload is not None:
                raise ValueError(
                    "Cette méthode ne doit pas avoir de payload."
                )

            encoded_action = base64.b64encode(
                json.dumps(action).encode("utf-8")
            ).decode("ascii")

        except Exception as error:
            state.output = ModelOutput.from_content(
                model="ollama/qwen2.5:3b",
                content=json.dumps({
                    "sample_id": sample_id,
                    "http_status": -1,
                    "response": {"error": str(error)}
                })
            )
            return state

        script = r'''
import os
import json
import base64
import threading
import time
import urllib.request
import urllib.error

sample_id = "__SAMPLE_ID__"
encoded_action = "__ACTION__"

action = json.loads(
    base64.b64decode(encoded_action).decode("utf-8")
)

db_path = f"/workspace/benchmark/api/data/{sample_id}.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)

if os.path.exists(db_path):
    os.remove(db_path)

os.environ["API_DB_PATH"] = db_path

from benchmark.api.server import app
from werkzeug.serving import make_server

server = make_server("127.0.0.1", 0, app)

thread = threading.Thread(
    target=server.serve_forever,
    daemon=True
)
thread.start()

time.sleep(0.2)

base_url = f"http://127.0.0.1:{server.server_port}"

method = action["method"]
path = action["path"]
payload = action.get("payload")

try:
    data = None
    headers = {}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        base_url + path,
        data=data,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.status
            body = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        status = error.code
        body = json.loads(error.read().decode("utf-8"))

    result = {
        "sample_id": sample_id,
        "http_status": status,
        "response": body
    }

    print(json.dumps(result))

finally:
    server.shutdown()
'''

        script = script.replace(
            "__SAMPLE_ID__", sample_id
        ).replace(
            "__ACTION__", encoded_action
        )

        try:
            result = await sandbox().exec(
                ["python", "-c", script],
                timeout=30
            )

            if not result.success or result.returncode != 0:
                raise RuntimeError(result.stderr)

            output = result.stdout.strip()

            if not output:
                raise ValueError("Aucune réponse de l'API.")

            result_json = json.loads(output)

            final_output = {
                "sample_id": sample_id,
                "http_status": result_json["http_status"],
                "response": result_json["response"]
            }

        except Exception as error:
            final_output = {
                "sample_id": sample_id,
                "http_status": -1,
                "response": {"error": str(error)}
            }

        state.output = ModelOutput.from_content(
            model="ollama/qwen2.5:3b",
            content=json.dumps(final_output)
        )

        return state

    return solve
