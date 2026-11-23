
from unittest.mock import AsyncMock, patch
import asyncio
import json
from types import SimpleNamespace

from benchmark.scorers.sql_scorer import sql_state_scorer
from benchmark.scorers.api_scorer import api_state_scorer
from benchmark.scorers.repository_scorer import repository_state_scorer


def make_state(sample_id, operation, output):
    return SimpleNamespace(
        sample_id=sample_id,
        metadata={"operation": operation},
        output=SimpleNamespace(completion=json.dumps(output)),
    )


def make_raw_state(sample_id, operation, completion):
    return SimpleNamespace(
        sample_id=sample_id,
        metadata={"operation": operation},
        output=SimpleNamespace(completion=completion),
    )


def make_sandbox_result(data, success=True, returncode=0):
    return SimpleNamespace(
        success=success,
        returncode=returncode,
        stdout=json.dumps(data) if data is not None else "",
        stderr="Erreur Sandbox" if not success else "",
    )


# ============================================================
# SQL SCORER
# ============================================================

def test_sql_unknown_operation_returns_zero():
    scorer = sql_state_scorer()

    state = make_state(
        "SQL-001",
        "unknown_operation",
        {},
    )

    fake_result = make_sandbox_result({
        "customers": [],
        "orders": [],
    })

    with patch("benchmark.scorers.sql_scorer.sandbox") as mock_sandbox:
        mock_sandbox.return_value.exec = AsyncMock(
            return_value=fake_result
        )

        result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "Unknown operation" in result.explanation


def test_sql_invalid_json_returns_zero():
    scorer = sql_state_scorer()

    state = make_raw_state(
        "SQL-006",
        "aggregate",
        "JSON invalide",
    )

    result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "Invalid agent output" in result.explanation


def test_sql_incorrect_aggregation_returns_zero():
    scorer = sql_state_scorer()

    state = make_state(
        "SQL-006",
        "aggregate",
        {
            "total_clients": 10,
            "active_clients": 5,
        },
    )

    with patch("benchmark.scorers.sql_scorer.sandbox") as mock_sandbox:
        mock_sandbox.return_value.exec = AsyncMock(
            return_value=make_sandbox_result({
                "customers": [],
                "orders": [],
            })
        )

        result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "Incorrect aggregation result" in result.explanation


def test_sql_sandbox_failure_returns_zero():
    scorer = sql_state_scorer()

    state = make_state(
        "SQL-001",
        "update_one",
        {},
    )

    fake_result = make_sandbox_result(
        None,
        success=False,
        returncode=1,
    )

    with patch("benchmark.scorers.sql_scorer.sandbox") as mock_sandbox:
        mock_sandbox.return_value.exec = AsyncMock(
            return_value=fake_result
        )

        result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "Database verification failed" in result.explanation


def test_sql_incorrect_database_state_returns_zero():
    scorer = sql_state_scorer()

    state = make_state(
        "SQL-001",
        "update_one",
        {},
    )

    fake_result = make_sandbox_result({
        "customers": [
            ["C-001", "Client Alpha", 0],
            ["C-002", "Client Beta", 0],
            ["C-003", "Client Gamma", 1],
            ["C-004", "Client Delta", 0],
            ["C-100", "Client Epsilon", 0],
        ],
        "orders": [],
    })

    with patch("benchmark.scorers.sql_scorer.sandbox") as mock_sandbox:
        mock_sandbox.return_value.exec = AsyncMock(
            return_value=fake_result
        )

        result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "All conditions satisfied: False" in result.explanation


# ============================================================
# API SCORER
# ============================================================

def test_api_unknown_operation_returns_zero():
    scorer = api_state_scorer()

    state = make_state(
        "API-001",
        "unknown_operation",
        {"http_status": 200, "response": {}},
    )

    result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "Opération inconnue" in result.explanation


def test_api_invalid_json_returns_zero():
    scorer = api_state_scorer()

    state = make_raw_state(
        "API-001",
        "get_user",
        "JSON invalide",
    )

    result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert result.explanation.startswith(
        "Erreur pendant la vérification"
    )


def test_api_wrong_http_status_returns_zero():
    scorer = api_state_scorer()

    state = make_state(
        "API-001",
        "get_user",
        {
            "http_status": 404,
            "response": {
                "id": 1,
                "name": "Alice",
                "email": "alice@example.com",
            },
        },
    )

    fake_result = make_sandbox_result({
        "database_valid": True,
        "actual_users": [],
        "expected_users": [],
    })

    with patch("benchmark.scorers.api_scorer.sandbox") as mock_sandbox:
        mock_sandbox.return_value.exec = AsyncMock(
            return_value=fake_result
        )

        result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "HTTP attendu=200" in result.explanation


def test_api_incorrect_response_returns_zero():
    scorer = api_state_scorer()

    state = make_state(
        "API-001",
        "get_user",
        {
            "http_status": 200,
            "response": {
                "id": 99,
                "name": "Unknown",
                "email": "wrong@example.com",
            },
        },
    )

    fake_result = make_sandbox_result({
        "database_valid": True,
        "actual_users": [],
        "expected_users": [],
    })

    with patch("benchmark.scorers.api_scorer.sandbox") as mock_sandbox:
        mock_sandbox.return_value.exec = AsyncMock(
            return_value=fake_result
        )

        result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "réponse correcte=False" in result.explanation


def test_api_sandbox_failure_returns_zero():
    scorer = api_state_scorer()

    state = make_state(
        "API-001",
        "get_user",
        {
            "http_status": 200,
            "response": {
                "id": 1,
                "name": "Alice",
                "email": "alice@example.com",
            },
        },
    )

    fake_result = make_sandbox_result(
        None,
        success=False,
        returncode=1,
    )

    with patch("benchmark.scorers.api_scorer.sandbox") as mock_sandbox:
        mock_sandbox.return_value.exec = AsyncMock(
            return_value=fake_result
        )

        result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "Erreur pendant la vérification" in result.explanation


# ============================================================
# REPOSITORY SCORER
# ============================================================

def test_repository_rejects_wrong_sample_id():
    scorer = repository_state_scorer()

    state = make_state(
        "REPO-001",
        "repair",
        {"sample_id": "REPO-002"},
    )

    result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "Identifiant du projet incorrect" in result.explanation


def test_repository_rejects_missing_patch():
    scorer = repository_state_scorer()

    state = make_state(
        "REPO-001",
        "repair",
        {
            "sample_id": "REPO-001",
            "patch_applied": False,
        },
    )

    result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "Aucun correctif confirmé" in result.explanation


def test_repository_rejects_inconsistent_classification():
    scorer = repository_state_scorer()

    state = make_state(
        "REPO-001",
        "repair",
        {
            "sample_id": "REPO-001",
            "patch_applied": True,
            "baseline_returncode": 1,
            "final_returncode": 0,
            "test_results": [
                {
                    "test_id": "test_app.py::test_discount",
                    "baseline_passed": False,
                    "final_passed": True,
                    "classification": "PASS_TO_PASS",
                }
            ],
        },
    )

    result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "Classification incorrecte" in result.explanation


def test_repository_rejects_regression():
    scorer = repository_state_scorer()

    state = make_state(
        "REPO-001",
        "repair",
        {
            "sample_id": "REPO-001",
            "patch_applied": True,
            "baseline_returncode": 1,
            "final_returncode": 0,
            "test_results": [
                {
                    "test_id": "test_app.py::test_new",
                    "baseline_passed": False,
                    "final_passed": True,
                    "classification": "FAIL_TO_PASS",
                },
                {
                    "test_id": "test_app.py::test_existing",
                    "baseline_passed": True,
                    "final_passed": True,
                    "classification": "PASS_TO_PASS",
                },
                {
                    "test_id": "test_app.py::test_regression",
                    "baseline_passed": True,
                    "final_passed": False,
                    "classification": "PASS_TO_FAIL",
                },
            ],
            "fail_to_pass": 1,
            "pass_to_pass": 1,
            "pass_to_fail": 1,
            "fail_to_fail": 0,
        },
    )

    result = asyncio.run(scorer(state, None))

    assert result.value == 0
    assert "Régression détectée" in result.explanation
