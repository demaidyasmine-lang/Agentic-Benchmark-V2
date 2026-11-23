
import json

from inspect_ai.solver import solver
from inspect_ai.model import ModelOutput
from inspect_ai.util import sandbox


@solver
def deterministic_repository_solver():

    async def solve(state, generate):

        sample_id = str(state.sample_id)
        operation = state.metadata.get("operation")

        script = r'''
import json
import shutil
import subprocess
from pathlib import Path

sample_id = "__SAMPLE_ID__"
operation = "__OPERATION__"

fixture = Path(f"/workspace/benchmark/repository/fixtures/{sample_id}")
destination = Path(f"/workspace/benchmark/repository/data/{sample_id}/project")

if destination.exists():
    shutil.rmtree(destination)

shutil.copytree(fixture, destination)

app_file = destination / "app.py"
source = app_file.read_text(encoding="utf-8")

patches = {
    "discount": (
        "return price * discount_rate",
        "return price * (1 - discount_rate)"
    ),
    "email_validation": (
        'return "@" in email',
        'return "@" in email and "." in email.split("@")[-1] and email.split("@")[0] != ""'
    ),
    "normalize_name": (
        '.split(" ")',
        ".split()"
    ),
    "sort_products": (
        "reverse=True",
        "reverse=False"
    ),
    "filter_active_users": (
        'user.get("active") is False',
        'user.get("active") is True'
    ),
    "safe_divide": (
        "except ZeroDivisionError:",
        "except (ZeroDivisionError, TypeError, ValueError):"
    ),
    "cart_total": (
        'tax = items[0]["price"] * tax_rate',
        "tax = subtotal * tax_rate"
    ),
}

if operation not in patches:
    raise RuntimeError(f"Opération inconnue : {operation}")

old, new = patches[operation]

if old not in source:
    raise RuntimeError(f"Patch source introuvable pour {operation}")

# Collecte des tests individuels
collection = subprocess.run(
    ["python", "-m", "pytest", "--collect-only", "-q"],
    cwd=destination,
    capture_output=True,
    text=True
)

if collection.returncode != 0:
    raise RuntimeError(
        "Impossible de collecter les tests : "
        + collection.stdout + collection.stderr
    )

# Correction : normalisation des identifiants Pytest
test_ids = []

for line in collection.stdout.splitlines():
    node_id = line.strip()

    if "::" not in node_id or node_id.startswith("<"):
        continue

    if "/project/" in node_id:
        node_id = node_id.split("/project/", 1)[1]

    test_ids.append(node_id)

if not test_ids:
    raise RuntimeError("Aucun test individuel détecté.")

def run_test(test_id):
    result = subprocess.run(
        ["python", "-m", "pytest", "-q", test_id],
        cwd=destination,
        capture_output=True,
        text=True
    )

    return {
        "test_id": test_id,
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "output": result.stdout + result.stderr
    }

# Résultats avant correction
baseline_tests = [
    run_test(test_id)
    for test_id in test_ids
]

before = subprocess.run(
    ["python", "-m", "pytest", "-q"],
    cwd=destination,
    capture_output=True,
    text=True
)

# Application du patch
source = source.replace(old, new, 1)
app_file.write_text(source, encoding="utf-8")

# Résultats après correction
final_tests = [
    run_test(test_id)
    for test_id in test_ids
]

after = subprocess.run(
    ["python", "-m", "pytest", "-q"],
    cwd=destination,
    capture_output=True,
    text=True
)

test_results = []

for initial, final in zip(baseline_tests, final_tests):

    if initial["passed"] and final["passed"]:
        classification = "PASS_TO_PASS"

    elif not initial["passed"] and final["passed"]:
        classification = "FAIL_TO_PASS"

    elif initial["passed"] and not final["passed"]:
        classification = "PASS_TO_FAIL"

    else:
        classification = "FAIL_TO_FAIL"

    test_results.append({
        "test_id": initial["test_id"],
        "baseline_passed": initial["passed"],
        "final_passed": final["passed"],
        "classification": classification
    })

result = {
    "sample_id": sample_id,
    "operation": operation,
    "patch_applied": True,
    "baseline_returncode": before.returncode,
    "baseline_output": before.stdout + before.stderr,
    "final_returncode": after.returncode,
    "final_output": after.stdout + after.stderr,
    "test_results": test_results,

    "fail_to_pass": sum(
        item["classification"] == "FAIL_TO_PASS"
        for item in test_results
    ),

    "pass_to_pass": sum(
        item["classification"] == "PASS_TO_PASS"
        for item in test_results
    ),

    "pass_to_fail": sum(
        item["classification"] == "PASS_TO_FAIL"
        for item in test_results
    ),

    "fail_to_fail": sum(
        item["classification"] == "FAIL_TO_FAIL"
        for item in test_results
    )
}

print(json.dumps(result))
'''

        script = script.replace("__SAMPLE_ID__", sample_id)
        script = script.replace("__OPERATION__", operation)

        result = await sandbox().exec(
            ["python", "-c", script],
            timeout=120
        )

        output = result.stdout.strip() or result.stderr.strip()

        state.output = ModelOutput.from_content(
            model="deterministic-repository-agent",
            content=output
        )

        return state

    return solve
