
import json

from inspect_ai.scorer import scorer, Score, accuracy
from inspect_ai.util import sandbox


@scorer(metrics=[accuracy()])
def repository_state_scorer():

    async def score(state, target):

        try:
            output = state.output.completion
            result = json.loads(output)

            if not isinstance(result, dict):
                raise ValueError("La sortie de l'agent doit être un objet JSON.")

            sample_id = str(state.sample_id)

            if result.get("sample_id") != sample_id:
                return Score(
                    value=0,
                    explanation="Identifiant du projet incorrect."
                )

            if result.get("patch_applied") is not True:
                return Score(
                    value=0,
                    explanation="Aucun correctif confirmé."
                )

            if result.get("baseline_returncode") == 0:
                return Score(
                    value=0,
                    explanation="Le projet initial ne présente aucun échec."
                )

            if result.get("final_returncode") != 0:
                return Score(
                    value=0,
                    explanation="Des tests échouent après correction."
                )

            # Vérification des classifications individuelles
            test_results = result.get("test_results")

            if not isinstance(test_results, list) or not test_results:
                return Score(
                    value=0,
                    explanation="Résultats individuels des tests absents."
                )

            test_ids = set()

            counts = {
                "FAIL_TO_PASS": 0,
                "PASS_TO_PASS": 0,
                "PASS_TO_FAIL": 0,
                "FAIL_TO_FAIL": 0,
            }

            for test in test_results:

                if not isinstance(test, dict):
                    return Score(
                        value=0,
                        explanation="Format de résultat individuel invalide."
                    )

                test_id = test.get("test_id")
                baseline = test.get("baseline_passed")
                final = test.get("final_passed")

                if not isinstance(test_id, str) or not test_id.strip():
                    return Score(
                        value=0,
                        explanation="Identifiant de test invalide."
                    )

                if test_id in test_ids:
                    return Score(
                        value=0,
                        explanation="Identifiant de test dupliqué."
                    )

                test_ids.add(test_id)

                if type(baseline) is not bool or type(final) is not bool:
                    return Score(
                        value=0,
                        explanation="Résultat individuel invalide."
                    )

                if not baseline and final:
                    expected = "FAIL_TO_PASS"
                elif baseline and final:
                    expected = "PASS_TO_PASS"
                elif baseline and not final:
                    expected = "PASS_TO_FAIL"
                else:
                    expected = "FAIL_TO_FAIL"

                if test.get("classification") != expected:
                    return Score(
                        value=0,
                        explanation=f"Classification incorrecte pour {test_id}."
                    )

                counts[expected] += 1

            # Vérification des compteurs
            for classification, count in counts.items():

                if result.get(classification.lower()) != count:
                    return Score(
                        value=0,
                        explanation=f"Compteur incorrect : {classification}."
                    )

            if counts["FAIL_TO_PASS"] == 0:
                return Score(
                    value=0,
                    explanation="Aucun test FAIL_TO_PASS détecté."
                )

            if counts["PASS_TO_PASS"] == 0:
                return Score(
                    value=0,
                    explanation="Aucun test PASS_TO_PASS détecté."
                )

            if counts["PASS_TO_FAIL"] > 0:
                return Score(
                    value=0,
                    explanation="Régression détectée : PASS_TO_FAIL."
                )

            if counts["FAIL_TO_FAIL"] > 0:
                return Score(
                    value=0,
                    explanation="Certains tests restent en échec."
                )

            # Vérification indépendante dans le Sandbox
            verification_script = r'''
import json
import subprocess
from pathlib import Path

project = Path(
    "/workspace/benchmark/repository/data/__SAMPLE_ID__/project"
)

collection = subprocess.run(
    ["python", "-m", "pytest", "--collect-only", "-q"],
    cwd=project,
    capture_output=True,
    text=True
)

if collection.returncode != 0:
    raise RuntimeError(
        "Échec de collecte des tests : " + collection.stderr
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
    raise RuntimeError("Aucun test collecté.")

individual_results = []

for test_id in test_ids:

    test = subprocess.run(
        ["python", "-m", "pytest", "-q", test_id],
        cwd=project,
        capture_output=True,
        text=True
    )

    individual_results.append({
        "test_id": test_id,
        "passed": test.returncode == 0
    })

full_suite = subprocess.run(
    ["python", "-m", "pytest", "-q"],
    cwd=project,
    capture_output=True,
    text=True
)

print(json.dumps({
    "returncode": full_suite.returncode,
    "tests": individual_results
}))
'''

            verification_script = verification_script.replace(
                "__SAMPLE_ID__", sample_id
            )

            verification = await sandbox().exec(
                ["python", "-c", verification_script],
                timeout=120
            )

            if (
                not verification.success
                or verification.returncode != 0
            ):
                return Score(
                    value=0,
                    explanation=(
                        "Échec de la vérification indépendante : "
                        f"{verification.stderr}"
                    )
                )

            if not verification.stdout.strip():
                return Score(
                    value=0,
                    explanation=(
                        "La vérification indépendante "
                        "n'a retourné aucun résultat."
                    )
                )

            verified = json.loads(verification.stdout.strip())

            if not isinstance(verified, dict):
                raise ValueError("Résultat Sandbox invalide.")

            if verified.get("returncode") != 0:
                return Score(
                    value=0,
                    explanation="La suite complète échoue indépendamment."
                )

            verified_list = verified.get("tests")

            if not isinstance(verified_list, list):
                raise ValueError("Liste des tests vérifiés invalide.")

            verified_tests = {}

            for item in verified_list:

                if not isinstance(item, dict):
                    raise ValueError(
                        "Résultat de test indépendant invalide."
                    )

                test_id = item.get("test_id")
                passed = item.get("passed")

                if not isinstance(test_id, str) or type(passed) is not bool:
                    raise ValueError(
                        "Données de test indépendant invalides."
                    )

                if test_id in verified_tests:
                    raise ValueError(
                        "Test dupliqué dans la vérification indépendante."
                    )

                verified_tests[test_id] = passed

            # Comparaison des tests indépendants avec ceux du solver
            if set(verified_tests) != test_ids:
                return Score(
                    value=0,
                    explanation="Les tests vérifiés ne correspondent pas."
                )

            if not all(verified_tests.values()):
                return Score(
                    value=0,
                    explanation=(
                        "Un test individuel échoue "
                        "à la vérification indépendante."
                    )
                )

            return Score(
                value=1,
                explanation=(
                    f"Réparation validée : "
                    f"{counts['FAIL_TO_PASS']} FAIL_TO_PASS, "
                    f"{counts['PASS_TO_PASS']} PASS_TO_PASS, "
                    "aucune régression et vérification indépendante réussie."
                )
            )

        except Exception as error:

            return Score(
                value=0,
                explanation=f"Erreur pendant la vérification : {error}"
            )

    return score
