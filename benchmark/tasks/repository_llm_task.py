from inspect_ai import Task, task

from benchmark.datasets.repository_dataset import repository_samples
from benchmark.solvers.repository_llm_solver import ollama_repository_solver
from benchmark.scorers.repository_scorer import repository_state_scorer


@task
def repository_llm_test_repo001():
    repo001_sample = [
        sample for sample in repository_samples
        if sample.id == "REPO-001"
    ]

    return Task(
        dataset=repo001_sample,
        solver=ollama_repository_solver(),
        scorer=repository_state_scorer(),
        sandbox=("docker", "../../compose.yaml"),
    )


@task
def repository_llm_benchmark():
    return Task(
        dataset=repository_samples,
        solver=ollama_repository_solver(),
        scorer=repository_state_scorer(),
        sandbox=("docker", "../../compose.yaml"),
    )