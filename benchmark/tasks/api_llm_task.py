
from inspect_ai import Task, task

from benchmark.datasets.api_dataset import api_samples
from benchmark.solvers.api_llm_solver import ollama_api_solver
from benchmark.scorers.api_scorer import api_state_scorer


@task
def api_llm_test_api001():
    api001_sample = [
        sample for sample in api_samples
        if sample.id == "API-001"
    ]

    return Task(
        dataset=api001_sample,
        solver=ollama_api_solver(),
        scorer=api_state_scorer(),
        sandbox=("docker", "../../compose.yaml"),
    )


@task
def api_llm_benchmark():
    return Task(
        dataset=api_samples,
        solver=ollama_api_solver(),
        scorer=api_state_scorer(),
        sandbox=("docker", "../../compose.yaml"),
    )
