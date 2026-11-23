
from datetime import datetime
from pathlib import Path

from django.db import transaction
from inspect_ai.log import read_eval_log

from dashboard.models import EvaluationRun, TaskResult

from benchmark.datasets.sql_dataset import sql_samples
from benchmark.datasets.api_dataset import api_samples
from benchmark.datasets.repository_dataset import repository_samples


LOG_DIR = Path("logs")


TASK_CONFIG = {
    "sql_benchmark": {
        "category": "SQL",
        "benchmark_name": "SQL Benchmark",
        "agent_name": "Deterministic SQL Agent",
        "scorer": "sql_state_scorer",
        "expected_samples": len(sql_samples),
    },
    "sql_llm_benchmark": {
        "category": "SQL",
        "benchmark_name": "SQL LLM Benchmark",
        "agent_name": "Qwen SQL Agent",
        "scorer": "sql_state_scorer",
        "expected_samples": len(sql_samples),
    },
    "api_benchmark": {
        "category": "API",
        "benchmark_name": "API Benchmark",
        "agent_name": "Deterministic API Agent",
        "scorer": "api_state_scorer",
        "expected_samples": len(api_samples),
    },
    "api_llm_benchmark": {
        "category": "API",
        "benchmark_name": "API LLM Benchmark",
        "agent_name": "Qwen API Agent",
        "scorer": "api_state_scorer",
        "expected_samples": len(api_samples),
    },
    "repository_benchmark": {
        "category": "REPOSITORY",
        "benchmark_name": "Repository Repair Benchmark",
        "agent_name": "Deterministic Repository Agent",
        "scorer": "repository_state_scorer",
        "expected_samples": len(repository_samples),
    },
    "repository_llm_benchmark": {
        "category": "REPOSITORY",
        "benchmark_name": "Repository Repair LLM Benchmark",
        "agent_name": "Qwen Repository Agent",
        "scorer": "repository_state_scorer",
        "expected_samples": len(repository_samples),
    },
}


def identify_task_config(task_name, samples):
    """
    Identifie la configuration du benchmark.
    Certains résultats Repository LLM sont enregistrés
    sous le nom générique 'task' par Inspect AI.
    """

    config = TASK_CONFIG.get(task_name)

    if config is not None:
        return config

    if task_name == "task" and samples:
        sample_ids = [str(sample.id) for sample in samples]

        if (
            len(samples) == len(repository_samples)
            and all(sample_id.startswith("REPO-") for sample_id in sample_ids)
        ):
            return TASK_CONFIG["repository_llm_benchmark"]

    return None


def extract_model_tokens(log):
    """
    Récupère les tokens réellement consommés
    depuis les statistiques globales Inspect AI.
    """

    stats = getattr(log, "stats", None)

    if stats is None:
        return None

    model_usage = getattr(stats, "model_usage", None) or {}

    if not model_usage:
        return None

    total_tokens = 0

    for usage in model_usage.values():
        tokens = getattr(usage, "total_tokens", None)

        if tokens is None and isinstance(usage, dict):
            tokens = usage.get("total_tokens")

        if tokens is not None:
            total_tokens += int(tokens)

    return total_tokens if total_tokens > 0 else None


def extract_evaluation_duration(log, fallback_duration):
    """
    Calcule la durée réelle de l'évaluation à partir
    des dates de début et de fin Inspect AI.

    Utilise la somme des durées des tâches en secours.
    """

    stats = getattr(log, "stats", None)

    if stats is None:
        return fallback_duration

    started_at = getattr(stats, "started_at", None)
    completed_at = getattr(stats, "completed_at", None)

    if not started_at or not completed_at:
        return fallback_duration

    try:
        start = datetime.fromisoformat(str(started_at))
        end = datetime.fromisoformat(str(completed_at))

        duration = (end - start).total_seconds()

        return max(0.0, duration)

    except (ValueError, TypeError):
        return fallback_duration


def extract_trajectory(sample, scorer_name):
    events = sample.events or []

    span_lookup = {}
    solver_span_ids = set()
    solver_steps = 0

    for event in events:
        if type(event).__name__ == "SpanBeginEvent":
            span_id = getattr(event, "id", None)
            span_type = getattr(event, "type", "")

            span_lookup[span_id] = {
                "type": span_type,
                "name": getattr(event, "name", ""),
            }

            if span_type == "solver":
                solver_span_ids.add(span_id)
                solver_steps += 1

    trajectory = []
    total_sandbox_calls = 0
    solver_sandbox_calls = 0

    for event in events:
        event_type = type(event).__name__

        if event_type == "SpanBeginEvent":
            trajectory.append({
                "event": "span_begin",
                "span_type": getattr(event, "type", ""),
                "span_name": getattr(event, "name", ""),
            })

        elif event_type == "SpanEndEvent":
            ended_span = span_lookup.get(
                getattr(event, "id", None), {}
            )

            trajectory.append({
                "event": "span_end",
                "span_type": ended_span.get("type", ""),
                "span_name": ended_span.get("name", ""),
            })

        elif event_type == "SandboxEvent":
            total_sandbox_calls += 1

            span_id = getattr(event, "span_id", None)
            span = span_lookup.get(span_id, {})
            is_solver_call = span_id in solver_span_ids

            if is_solver_call:
                solver_sandbox_calls += 1

            output = getattr(event, "output", "") or ""

            trajectory.append({
                "event": "sandbox",
                "span_type": span.get("type", ""),
                "span_name": span.get("name", ""),
                "is_solver_call": is_solver_call,
                "action": getattr(event, "action", ""),
                "result": getattr(event, "result", None),
                "output_summary": str(output)[:300],
                "completed": str(
                    getattr(event, "completed", "")
                ),
            })

        elif event_type == "ScoreEvent":
            score = getattr(event, "score", None)

            trajectory.append({
                "event": "score",
                "scorer": getattr(event, "scorer", scorer_name),
                "value": getattr(score, "value", None),
                "explanation": getattr(score, "explanation", ""),
            })

        elif event_type == "StateEvent":
            trajectory.append({
                "event": "state_change",
            })

        elif event_type == "SampleInitEvent":
            trajectory.append({
                "event": "sample_init",
            })

    return {
        "event_count": len(events),
        "sandbox_calls": total_sandbox_calls,
        "solver_sandbox_calls": solver_sandbox_calls,
        "solver_steps": solver_steps,
        "turn_count": sample.turn_count or 0,
        "duration_seconds": sample.total_time or 0.0,
        "trajectory": trajectory,
    }


@transaction.atomic
def import_all():

    total_imported = 0
    imported_evaluations = 0
    skipped_evaluations = 0

    log_files = sorted(LOG_DIR.glob("*.eval"))

    print(f"Fichiers Inspect AI détectés : {len(log_files)}")
    print("--------------------------------")

    for path in log_files:

        try:
            log = read_eval_log(str(path))
        except Exception as exc:
            print(f"IGNORÉ | {path.name} | Lecture impossible : {exc}")
            skipped_evaluations += 1
            continue

        if log.status != "success":
            print(f"IGNORÉ | {path.name} | Statut : {log.status}")
            skipped_evaluations += 1
            continue

        samples = log.samples or []
        task_name = log.eval.task

        config = identify_task_config(task_name, samples)

        if config is None:
            print(f"IGNORÉ | {path.name} | Tâche inconnue : {task_name}")
            skipped_evaluations += 1
            continue

        expected = config["expected_samples"]

        if len(samples) != expected:
            print(
                f"IGNORÉ | {path.name} | "
                f"Évaluation incomplète : {len(samples)}/{expected}"
            )
            skipped_evaluations += 1
            continue

        scorer_name = config["scorer"]

        if any(scorer_name not in sample.scores for sample in samples):
            print(f"IGNORÉ | {path.name} | Scoreur manquant")
            skipped_evaluations += 1
            continue

        results = []
        passed = 0

        for sample in samples:

            score_data = sample.scores[scorer_name]
            score_value = float(score_data.value)

            is_passed = (
                score_value == 1.0
                and sample.error is None
            )

            if is_passed:
                passed += 1

            metrics = extract_trajectory(sample, scorer_name)

            results.append({
                "sample_id": str(sample.id),
                "score": score_value,
                "passed": is_passed,
                "error": str(sample.error) if sample.error else "",
                **metrics,
            })

        total = len(results)
        accuracy = passed / total if total else 0.0

        model_name = str(log.eval.model or "")

        if model_name.lower() in ("none", "none/none"):
            model_name = ""

        average_steps = (
            sum(result["solver_steps"] for result in results) / total
            if total else 0.0
        )

        cumulative_task_duration = sum(
            result["duration_seconds"] for result in results
        )

        evaluation_duration = extract_evaluation_duration(
            log,
            cumulative_task_duration,
        )

        total_tokens = extract_model_tokens(log)

        evaluation, created = EvaluationRun.objects.update_or_create(
            log_path=str(path),
            defaults={
                "benchmark_name": config["benchmark_name"],
                "category": config["category"],
                "agent_name": config["agent_name"],
                "model_name": model_name,
                "status": "SUCCESS",
                "total_tasks": total,
                "passed_tasks": passed,
                "failed_tasks": total - passed,
                "accuracy": accuracy,
                "average_steps": average_steps,
                "duration_seconds": evaluation_duration,
                "total_tokens": total_tokens,
            },
        )

        evaluation.task_results.all().delete()

        TaskResult.objects.bulk_create([
            TaskResult(
                evaluation=evaluation,
                sample_id=result["sample_id"],
                category=config["category"],
                score=result["score"],
                passed=result["passed"],
                error=result["error"],
                steps=result["solver_steps"],
                duration_seconds=result["duration_seconds"],
                event_count=result["event_count"],
                sandbox_calls=result["sandbox_calls"],
                solver_sandbox_calls=result["solver_sandbox_calls"],
                turn_count=result["turn_count"],
                trajectory=result["trajectory"],
            )
            for result in results
        ])

        total_imported += total
        imported_evaluations += 1

        action = "créée" if created else "mise à jour"

        average_solver_calls = (
            sum(result["solver_sandbox_calls"] for result in results) / total
            if total else 0.0
        )

        token_display = (
            f"{total_tokens:,}".replace(",", " ")
            if total_tokens is not None
            else "Non disponible"
        )

        print(
            f"IMPORTÉ | {config['category']} | "
            f"{config['agent_name']} | "
            f"{passed}/{total} | Accuracy : {accuracy:.2%} | "
            f"Étapes solver moyennes : {average_steps:.2f} | "
            f"Appels Sandbox totaux moyens : "
            f"{sum(result['sandbox_calls'] for result in results) / total:.2f} | "
            f"Appels Sandbox solver moyens : {average_solver_calls:.2f} | "
            f"Durée réelle : {evaluation_duration:.2f}s | "
            f"Tokens : {token_display} | "
            f"Évaluation {action}"
        )

    print("--------------------------------")
    print(f"Évaluations importées : {imported_evaluations}")
    print(f"Évaluations ignorées : {skipped_evaluations}")
    print(f"Total des tâches importées : {total_imported}")
    print("Import terminé.")
