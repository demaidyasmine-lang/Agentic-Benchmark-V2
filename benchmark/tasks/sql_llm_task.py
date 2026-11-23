
from inspect_ai import Task, task

from benchmark.datasets.sql_dataset import sql_samples
from benchmark.solvers.sql_llm_solver import ollama_sql_solver
from benchmark.scorers.sql_scorer import sql_state_scorer


@task
def sql_llm_test_sql001():
    sql001_sample = [
        sample for sample in sql_samples
        if sample.id == "SQL-001"
    ]

    return Task(
        dataset=sql001_sample,
        solver=ollama_sql_solver(),
        scorer=sql_state_scorer(),
        sandbox=("docker", "../../compose.yaml"),
    )


@task
def sql_llm_benchmark():
    return Task(
        dataset=sql_samples,
        solver=ollama_sql_solver(),
        scorer=sql_state_scorer(),
        sandbox=("docker", "../../compose.yaml"),
    )
