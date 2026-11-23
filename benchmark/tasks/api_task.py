from inspect_ai import Task, task

from benchmark.datasets.api_dataset import api_samples
from benchmark.solvers.api_solver import deterministic_api_solver
from benchmark.scorers.api_scorer import api_state_scorer


@task
def api_benchmark():

    return Task(
        dataset=api_samples,
        solver=deterministic_api_solver(),
        scorer=api_state_scorer(),
        sandbox=("docker", "../../compose.yaml"),
    )
