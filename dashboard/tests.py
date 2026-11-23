from io import StringIO

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

    def add_task(self, evaluation, sample_id, passed=True):
        return TaskResult.objects.create(
            evaluation=evaluation,
            sample_id=sample_id,
            category="SQL",
            score=1.0 if passed else 0.0,
            passed=passed,
        )

    def create_comparison(self):
        baseline = self.create_evaluation("logs/2026-01-01_old.eval")
        current = self.create_evaluation("logs/2026-01-02_new.eval")
        return baseline, current

    def test_no_regression(self):
        baseline, current = self.create_comparison()

        self.add_task(baseline, "SQL-001", True)
        self.add_task(current, "SQL-001", True)

        output = StringIO()
        call_command("check_regressions", stdout=output)

        self.assertIn("CONTROLE REUSSI", output.getvalue())

    def test_detects_failed_task(self):
        baseline, current = self.create_comparison()

        self.add_task(baseline, "SQL-001", True)
        self.add_task(current, "SQL-001", False)

        with self.assertRaises(CommandError):
            call_command("check_regressions", stdout=StringIO())

    def test_detects_missing_task(self):
        baseline, current = self.create_comparison()

        self.add_task(baseline, "SQL-001", True)

        with self.assertRaises(CommandError):
            call_command("check_regressions", stdout=StringIO())

    def test_detects_added_task(self):
        baseline, current = self.create_comparison()

        self.add_task(baseline, "SQL-001", True)
        self.add_task(current, "SQL-001", True)
        self.add_task(current, "SQL-002", True)

        with self.assertRaises(CommandError):
            call_command("check_regressions", stdout=StringIO())
