
import base64
import json
import re

from inspect_ai.model import ChatMessageUser, ModelOutput
from inspect_ai.solver import solver
from inspect_ai.util import sandbox


@solver
def ollama_repository_solver():

    async def solve(state, generate):

        sample_id = str(state.sample_id)
        task_instruction = str(state.input)

        # 1. Préparer le projet et récupérer son code initial
        setup_script = r'''
import json
import shutil
import subprocess
from pathlib import Path

sample_id = "__SAMPLE_ID__"

fixture = Path(
    f"/workspace/benchmark/repository/fixtures/{sample_id}"
)
destination = Path(
    f"/workspace/benchmark/repository/data/{sample_id}/project"
)

if destination.exists():
    shutil.rmtree(destination)

shutil.copytree(fixture, destination)

app_file = destination / "app.py"

if not app_file.exists():
    raise RuntimeError("Le fichier app.py est introuvable.")

source = app_file.read_text(encoding="utf-8")

collection = subprocess.run(
    ["python", "-m", "pytest", "--collect-only", "-q"],
    cwd=destination,
    capture_output=True,
    text=True
)

if collection.returncode != 0:
    raise RuntimeError(
        "Échec de collecte : "
        + collection.stdout + collection.stderr
    )

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
        "passed": result.returncode == 0
    }

baseline_tests = [
    run_test(test_id)
    for test_id in test_ids
]

baseline = subprocess.run(
    ["python", "-m", "pytest", "-q"],
    cwd=destination,
    capture_output=True,
    text=True
)

print(json.dumps({
    "source": source,
    "test_ids": test_ids,
    "baseline_tests": baseline_tests,
    "baseline_returncode": baseline.returncode,
    "baseline_output": baseline.stdout + baseline.stderr
}))
'''

        setup_script = setup_script.replace(
            "__SAMPLE_ID__", sample_id
        )

        try:
            setup = await sandbox().exec(
                ["python", "-c", setup_script],
                timeout=120
            )

            if not setup.success or setup.returncode != 0:
                raise RuntimeError(
                    "Préparation du projet impossible : "
                    + setup.stderr
                )

            initial_data = json.loads(setup.stdout.strip())

            source = initial_data["source"]
            test_ids = initial_data["test_ids"]
            baseline_tests = initial_data["baseline_tests"]
            baseline_returncode = initial_data["baseline_returncode"]

            if baseline_returncode == 0:
                raise ValueError(
                    "Le projet initial ne présente aucun échec."
                )

        except Exception as error:
            state.output = ModelOutput.from_content(
                model="ollama/qwen2.5:3b",
                content=json.dumps({
                    "sample_id": sample_id,
                    "patch_applied": False,
                    "error": str(error)
                })
            )
            return state

        # 2. Demander à Qwen de réparer le code
        prompt = f"""
Tu es un agent autonome spécialisé dans la réparation de code Python.

OBJECTIF :
Corriger le fichier app.py pour satisfaire la consigne et réussir
tous les tests pytest.

CONSIGNE :
{task_instruction}

CODE SOURCE INITIAL DE app.py :
```python
{source}
```

REGLES :
- Analyse attentivement le comportement actuel de la fonction.
- Identifie précisément la différence entre le comportement actuel
  et celui demandé dans la consigne.
- Vérifie les conditions booléennes : True et False ne sont pas
  interchangeables.
- Pour les filtres, vérifie quels éléments doivent être conservés
  et lesquels doivent être exclus.
- Corrige le problème sans supprimer les fonctionnalités existantes.
- Conserve les noms des fonctions et leurs signatures.
- Ne modifie pas les tests.
- Ne retourne pas une correction prédéfinie.
- Retourne le fichier app.py COMPLET après correction.
- Ne retourne aucune explication.
- N'utilise pas de balises Markdown.
- Retourne uniquement du code Python valide.
"""

        state.messages.append(
            ChatMessageUser(content=prompt)
        )

        try:
            state = await generate(state)

            if state.output is None:
                raise ValueError(
                    "Le modèle n'a retourné aucune réponse."
                )

            completion = state.output.completion.strip()

            # Extraire le code si le modèle utilise des balises Markdown
            code_match = re.search(
                r"```(?:python)?\s*(.*?)```",
                completion,
                re.DOTALL | re.IGNORECASE
            )

            corrected_code = (
                code_match.group(1)
                if code_match
                else completion
            )

            # Nettoyer les caractères invisibles et les espaces
            corrected_code = corrected_code.replace(
                "\ufeff", ""
            ).strip()

            if not corrected_code:
                raise ValueError("Le code corrigé est vide.")

            if "def " not in corrected_code:
                raise ValueError(
                    "La réponse ne contient pas de fonction Python."
                )

            # Vérifier la syntaxe avant de modifier le projet
            compile(corrected_code, "app.py", "exec")

        except Exception as error:
            state.output = ModelOutput.from_content(
                model="ollama/qwen2.5:3b",
                content=json.dumps({
                    "sample_id": sample_id,
                    "patch_applied": False,
                    "error": str(error)
                })
            )
            return state

        # 3. Transmettre le code corrigé au Sandbox
        payload = {
            "sample_id": sample_id,
            "code": corrected_code,
            "baseline_tests": baseline_tests,
            "baseline_returncode": baseline_returncode,
            "test_ids": test_ids
        }

        encoded_payload = base64.b64encode(
            json.dumps(payload).encode("utf-8")
        ).decode("ascii")

        verification_script = r'''
import json
import base64
import subprocess
from pathlib import Path

payload = json.loads(
    base64.b64decode("__PAYLOAD__").decode("utf-8")
)

sample_id = payload["sample_id"]

project = Path(
    f"/workspace/benchmark/repository/data/{sample_id}/project"
)

app_file = project / "app.py"

source = payload["code"]

# Application du correctif proposé par le modèle
app_file.write_text(source, encoding="utf-8")

test_ids = payload["test_ids"]
baseline_tests = payload["baseline_tests"]

def run_test(test_id):
    result = subprocess.run(
        ["python", "-m", "pytest", "-q", test_id],
        cwd=project,
        capture_output=True,
        text=True
    )

    return {
        "test_id": test_id,
        "passed": result.returncode == 0
    }

final_tests = [
    run_test(test_id)
    for test_id in test_ids
]

after = subprocess.run(
    ["python", "-m", "pytest", "-q"],
    cwd=project,
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
    "patch_applied": True,
    "baseline_returncode": payload["baseline_returncode"],
    "final_returncode": after.returncode,
    "baseline_output": "",
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

        verification_script = verification_script.replace(
            "__PAYLOAD__", encoded_payload
        )

        try:
            result = await sandbox().exec(
                ["python", "-c", verification_script],
                timeout=120
            )

            if not result.success or result.returncode != 0:
                raise RuntimeError(result.stderr)

            output = result.stdout.strip()

            if not output:
                raise ValueError(
                    "Aucun résultat de vérification retourné."
                )

            final_result = json.loads(output)

        except Exception as error:
            final_result = {
                "sample_id": sample_id,
                "patch_applied": False,
                "error": str(error)
            }

        state.output = ModelOutput.from_content(
            model="ollama/qwen2.5:3b",
            content=json.dumps(final_result)
        )

        return state

    return solve
