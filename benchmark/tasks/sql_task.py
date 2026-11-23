from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.solver import solver
from inspect_ai.util import sandbox

from benchmark.solvers.sql_solver import deterministic_sql_solver
from benchmark.scorers.sql_scorer import sql_state_scorer
from benchmark.datasets.sql_dataset import sql_samples


@task
def sql_benchmark():

    return Task(
        dataset=sql_samples,
        solver=deterministic_sql_solver(),
        scorer=sql_state_scorer(),
        sandbox=("docker", "../../compose.yaml"),
    )
