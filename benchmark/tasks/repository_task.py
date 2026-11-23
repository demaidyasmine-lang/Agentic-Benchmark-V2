from inspect_ai import Task, task

from benchmark.datasets.repository_dataset import repository_samples
from benchmark.solvers.repository_solver import deterministic_repository_solver
from benchmark.scorers.repository_scorer import repository_state_scorer


@task
def repository_benchmark():

    return Task(
        dataset=repository_samples,
        solver=deterministic_repository_solver(),
        scorer=repository_state_scorer(),
        sandbox=("docker", "../../compose.yaml"),
    )
