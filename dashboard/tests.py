
import json
import tempfile
from pathlib import Path

from django.core.management import call_command, CommandError
from django.db import IntegrityError, transaction
from django.test import TestCase

from dashboard.models import EvaluationRun, TaskResult


class DashboardModelTests(TestCase):

    def create_evaluation(self, log_path):
        return EvaluationRun.objects.create(
            benchmark_name="SQL Benchmark",
            category="SQL",
            agent_name="Test Agent",
            status="SUCCESS",
            log_path=log_path,
            total_tasks=1,
            passed_tasks=1,
            failed_tasks=0,
            accuracy=1.0,
        )

    def test_evaluation_creation(self):
        evaluation = self.create_evaluation("logs/test-001.eval")
        self.assertEqual(evaluation.category, "SQL")
        self.assertEqual(evaluation.accuracy, 1.0)
        self.assertEqual(evaluation.total_tasks, 1)

    def test_task_result_creation(self):
        evaluation = self.create_evaluation("logs/test-002.eval")

        result = TaskResult.objects.create(
            evaluation=evaluation,
            sample_id="SQL-001",
            category="SQL",
            score=1.0,
            passed=True,
        )

        self.assertTrue(result.passed)
        self.assertEqual(result.sample_id, "SQL-001")

    def test_duplicate_sample_is_rejected(self):
        evaluation = self.create_evaluation("logs/test-003.eval")

        TaskResult.objects.create(
            evaluation=evaluation,
            sample_id="SQL-001",
            category="SQL",
            score=1.0,
            passed=True,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TaskResult.objects.create(
                    evaluation=evaluation,
                    sample_id="SQL-001",
                    category="SQL",
                    score=1.0,
                    passed=True,
                )


class RegressionCommandTests(TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.baseline_path = Path(self.temp_dir.name) / "baseline.json"

        baseline = {
            "version": 1,
            "baselines": [
                {
                    "agent_name": "Test Agent",
                    "category": "SQL",
                    "passed_samples": ["SQL-001"],
                }
            ],
        }

        with self.baseline_path.open("w", encoding="utf-8") as file:
            json.dump(baseline, file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_evaluation(self, log_path, agent_name="Test Agent"):
        return EvaluationRun.objects.create(
            benchmark_name="SQL Benchmark",
            category="SQL",
            agent_name=agent_name,
            status="SUCCESS",
            log_path=log_path,
            total_tasks=1,
            passed_tasks=1,
            failed_tasks=0,
            accuracy=1.0,
        )

    def add_task(self, evaluation, sample_id, passed=True):
        return TaskResult.objects.create(
            evaluation=evaluation,
            sample_id=sample_id,
            category="SQL",
            score=1.0 if passed else 0.0,
            passed=passed,
        )

    def run_regression_check(self):
        call_command(
            "check_regressions",
            baseline=str(self.baseline_path),
        )

    def test_no_regression(self):
        evaluation = self.create_evaluation("logs/current.eval")
        self.add_task(evaluation, "SQL-001", True)

        self.run_regression_check()

    def test_detects_failed_task(self):
        evaluation = self.create_evaluation("logs/current.eval")
        self.add_task(evaluation, "SQL-001", False)

        with self.assertRaises(CommandError):
            self.run_regression_check()

    def test_detects_missing_task(self):
        self.create_evaluation("logs/current.eval")

        with self.assertRaises(CommandError):
            self.run_regression_check()

    def test_detects_added_task(self):
        evaluation = self.create_evaluation("logs/current.eval")
        self.add_task(evaluation, "SQL-001", True)
        self.add_task(evaluation, "SQL-002", True)

        with self.assertRaises(CommandError):
            self.run_regression_check()

    def test_does_not_compare_different_agents(self):
        evaluation = self.create_evaluation(
            "logs/expected-agent.eval",
            agent_name="Test Agent",
        )
        self.add_task(evaluation, "SQL-001", True)

        other = self.create_evaluation(
            "logs/other-agent.eval",
            agent_name="Other Agent",
        )
        self.add_task(other, "SQL-001", False)

        self.run_regression_check()

    def test_detects_missing_agent_evaluation(self):
        with self.assertRaises(CommandError):
            self.run_regression_check()
