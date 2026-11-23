import json

from inspect_ai.solver import solver
from inspect_ai.model import ModelOutput
from inspect_ai.util import sandbox


@solver
def deterministic_api_solver():

    async def solve(state, generate):

        operation = state.metadata.get("operation")
        sample_id = str(state.sample_id)

        script = r'''
import os
import json
import threading
import urllib.request
import urllib.error

sample_id = "__SAMPLE_ID__"
operation = "__OPERATION__"

db_path = f"/workspace/benchmark/api/data/{sample_id}.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)

if os.path.exists(db_path):
    os.remove(db_path)

os.environ["API_DB_PATH"] = db_path

from benchmark.api.server import app
from werkzeug.serving import make_server

server = make_server("127.0.0.1", 0, app)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

base_url = f"http://127.0.0.1:{server.server_port}"

def request(method, path, payload=None):
    data = None
    headers = {}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        base_url + path,
        data=data,
        headers=headers,
        method=method
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        body = error.read().decode()
        return error.code, json.loads(body)

try:
    if operation == "get_user":
        status, body = request("GET", "/users/1")

    elif operation == "create_user":
        status, body = request(
            "POST",
            "/users",
            {"name": "Charlie", "email": "charlie@example.com", "role": "user"}
        )

    elif operation == "update_user":
        status, body = request(
            "PUT",
            "/users/1",
            {"name": "Alice Johnson", "email": "alice.johnson@example.com"}
        )

    elif operation == "delete_user":
        status, body = request("DELETE", "/users/2")

    elif operation == "filter_users":
        status, body = request("GET", "/users?role=admin")

    elif operation == "validate_missing_email":
        status, body = request("POST", "/users", {"name": "Test"})

    elif operation == "not_found":
        status, body = request("GET", "/users/999")

    elif operation == "prevent_invalid_update":
        status, body = request(
            "PUT",
            "/users/1",
            {"name": "Alice Broken", "email": "invalid-email"}
        )

    else:
        raise ValueError(f"Opération inconnue : {operation}")

    result = {
        "sample_id": sample_id,
        "operation": operation,
        "http_status": status,
        "response": body
    }

    print(json.dumps(result))

finally:
    server.shutdown()
'''

        script = script.replace("__SAMPLE_ID__", sample_id)
        script = script.replace("__OPERATION__", operation)

        result = await sandbox().exec(
            ["python", "-c", script],
            timeout=30
        )

        output = result.stdout.strip()

        state.output = ModelOutput.from_content(
            model="deterministic-api-agent",
            content=output if output else result.stderr
        )

        return state

    return solve
