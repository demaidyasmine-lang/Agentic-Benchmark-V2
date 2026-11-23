
from django.shortcuts import render
from django.db.models import Sum

from .models import EvaluationRun, TaskResult


CATEGORY_LABELS = {
    "SQL": "SQL",
    "API": "API",
    "REPOSITORY": "Repository Repair",
}


def home(request):
    history = EvaluationRun.objects.all().order_by("-created_at")

    # Récupérer la dernière évaluation de chaque catégorie
    # pour chaque type d'agent (Déterministe et Qwen).
    latest_by_agent = {}

    for evaluation in history:
        key = (evaluation.category, evaluation.agent_name)

        if key not in latest_by_agent:
            latest_by_agent[key] = evaluation

    current_evaluations = list(latest_by_agent.values())
    current_evaluations.sort(
        key=lambda e: (e.category, e.agent_name)
    )

    # Statistiques globales des évaluations actuellement retenues.
    totals = EvaluationRun.objects.filter(
        pk__in=[e.pk for e in current_evaluations]
    ).aggregate(
        total_tasks=Sum("total_tasks"),
        passed_tasks=Sum("passed_tasks"),
        failed_tasks=Sum("failed_tasks"),
        total_duration=Sum("duration_seconds"),
        total_tokens=Sum("total_tokens"),
    )

    total_tasks = totals["total_tasks"] or 0
    passed_tasks = totals["passed_tasks"] or 0
    failed_tasks = totals["failed_tasks"] or 0

    global_accuracy = (
        passed_tasks / total_tasks * 100 if total_tasks else 0
    )

    # Résultats détaillés des tâches.
    task_results = list(
        TaskResult.objects.filter(
            evaluation__in=current_evaluations
        ).select_related("evaluation").order_by("sample_id")
    )

    # Statistiques des trajectoires.
    trajectory_totals = {
        "span_begin": 0,
        "span_end": 0,
        "sandbox": 0,
        "score": 0,
        "state_change": 0,
        "sample_init": 0,
    }

    total_sandbox_calls = 0
    total_solver_sandbox_calls = 0
    total_events = 0
    total_solver_steps = 0
    total_task_duration = 0

    for result in task_results:
        total_events += result.event_count
        total_sandbox_calls += result.sandbox_calls
        total_solver_sandbox_calls += result.solver_sandbox_calls
        total_solver_steps += result.steps or 0
        total_task_duration += result.duration_seconds or 0

        for event in result.trajectory:
            event_type = event.get("event", "")

            if event_type in trajectory_totals:
                trajectory_totals[event_type] += 1

    result_count = len(task_results)

    average_steps = (
        total_solver_steps / result_count if result_count else 0
    )

    average_solver_calls = (
        total_solver_sandbox_calls / result_count if result_count else 0
    )

    average_task_duration = (
        total_task_duration / result_count if result_count else 0
    )

    average_events = (
        total_events / result_count if result_count else 0
    )

    solver_call_ratio = (
        total_solver_sandbox_calls / total_sandbox_calls * 100
        if total_sandbox_calls else 0
    )

    trajectory_labels = [
        "Début d'étape",
        "Fin d'étape",
        "Appels Sandbox",
        "Évaluations des scores",
        "Changements d'état",
        "Initialisations",
    ]

    trajectory_values = [
        trajectory_totals["span_begin"],
        trajectory_totals["span_end"],
        trajectory_totals["sandbox"],
        trajectory_totals["score"],
        trajectory_totals["state_change"],
        trajectory_totals["sample_init"],
    ]

    # Préparation des données pour comparer les deux agents.
    comparison_data = []

    for category, category_label in CATEGORY_LABELS.items():

        deterministic = next(
            (
                e for e in current_evaluations
                if e.category == category
                and "Deterministic" in e.agent_name
            ),
            None,
        )

        qwen = next(
            (
                e for e in current_evaluations
                if e.category == category
                and "Qwen" in e.agent_name
            ),
            None,
        )

        comparison_data.append({
            "category": category,
            "label": category_label,

            "deterministic_accuracy": (
                round(deterministic.accuracy * 100, 2)
                if deterministic else None
            ),

            "qwen_accuracy": (
                round(qwen.accuracy * 100, 2)
                if qwen else None
            ),

            "deterministic_duration": (
                round(deterministic.duration_seconds, 2)
                if deterministic and deterministic.duration_seconds is not None
                else None
            ),

            "qwen_duration": (
                round(qwen.duration_seconds, 2)
                if qwen and qwen.duration_seconds is not None
                else None
            ),

            "deterministic_tokens": (
                deterministic.total_tokens if deterministic else None
            ),

            "qwen_tokens": (
                qwen.total_tokens if qwen else None
            ),

            "deterministic_passed": (
                deterministic.passed_tasks if deterministic else None
            ),

            "qwen_passed": (
                qwen.passed_tasks if qwen else None
            ),

            "deterministic_tasks": (
                deterministic.total_tasks if deterministic else None
            ),

            "qwen_tasks": (
                qwen.total_tasks if qwen else None
            ),
        })

    # Données conservées pour les graphiques déjà présents.
    chart_data = {
        "labels": [],
        "accuracies": [],
        "passed": [],
        "failed": [],
        "trajectory_labels": trajectory_labels,
        "trajectory_values": trajectory_values,

        # Comparaison Déterministe / Qwen.
        "comparison_labels": [
            item["label"] for item in comparison_data
        ],

        "deterministic_accuracies": [
            item["deterministic_accuracy"]
            for item in comparison_data
        ],

        "qwen_accuracies": [
            item["qwen_accuracy"]
            for item in comparison_data
        ],

        "deterministic_durations": [
            item["deterministic_duration"]
            for item in comparison_data
        ],

        "qwen_durations": [
            item["qwen_duration"]
            for item in comparison_data
        ],

        "deterministic_tokens": [
            item["deterministic_tokens"]
            for item in comparison_data
        ],

        "qwen_tokens": [
            item["qwen_tokens"]
            for item in comparison_data
        ],
    }

    for evaluation in current_evaluations:
        chart_data["labels"].append(
            f"{evaluation.get_category_display()} - {evaluation.agent_name}"
        )

        chart_data["accuracies"].append(
            round(evaluation.accuracy * 100, 2)
        )

        chart_data["passed"].append(evaluation.passed_tasks)
        chart_data["failed"].append(evaluation.failed_tasks)

    context = {
        "project_name": "Laboratoire d'évaluation des agents IA",

        "project_description": (
            "Plateforme d'évaluation reproductible et d'analyse "
            "des trajectoires multi-étapes des agents IA."
        ),

        "evaluations": history,
        "current_evaluations": current_evaluations,
        "comparison_data": comparison_data,
        "task_results": task_results,

        "total_evaluations": history.count(),
        "current_evaluation_count": len(current_evaluations),

        "total_tasks": total_tasks,
        "passed_tasks": passed_tasks,
        "failed_tasks": failed_tasks,
        "global_accuracy": round(global_accuracy, 2),

        "total_events": total_events,
        "total_sandbox_calls": total_sandbox_calls,
        "total_solver_sandbox_calls": total_solver_sandbox_calls,

        "average_steps": round(average_steps, 2),
        "average_solver_calls": round(average_solver_calls, 2),
        "average_task_duration": round(average_task_duration, 2),
        "average_events": round(average_events, 2),
        "solver_call_ratio": round(solver_call_ratio, 2),

        "total_duration": round(totals["total_duration"] or 0, 2),
        "total_tokens": totals["total_tokens"] or 0,

        "trajectory_totals": trajectory_totals,
        "chart_data": chart_data,
    }

    return render(request, "dashboard/home.html", context)
