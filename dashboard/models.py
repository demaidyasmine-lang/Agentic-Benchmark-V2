from django.db import models


class EvaluationRun(models.Model):

    CATEGORY_CHOICES = [
        ("SQL", "SQL"),
        ("API", "API"),
        ("REPOSITORY", "Repository Repair"),
        ("ALL", "All benchmarks"),
    ]

    STATUS_CHOICES = [
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("RUNNING", "Running"),
    ]

    benchmark_name = models.CharField(max_length=150)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="ALL"
    )

    agent_name = models.CharField(max_length=150)
    model_name = models.CharField(max_length=150, blank=True, default="")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SUCCESS"
    )

    total_tasks = models.PositiveIntegerField(default=0)
    passed_tasks = models.PositiveIntegerField(default=0)
    failed_tasks = models.PositiveIntegerField(default=0)

    accuracy = models.FloatField(default=0.0)

    pass_at_1 = models.FloatField(null=True, blank=True)
    pass_at_5 = models.FloatField(null=True, blank=True)

    total_tokens = models.PositiveBigIntegerField(null=True, blank=True)
    average_steps = models.FloatField(null=True, blank=True)
    estimated_cost = models.FloatField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    log_path = models.CharField(max_length=500, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.benchmark_name} - {self.agent_name}"


class TaskResult(models.Model):

    evaluation = models.ForeignKey(
        EvaluationRun,
        on_delete=models.CASCADE,
        related_name="task_results"
    )

    sample_id = models.CharField(max_length=100)
    category = models.CharField(max_length=20)

    score = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)

    error = models.TextField(blank=True, default="")

    tokens = models.PositiveIntegerField(null=True, blank=True)
    steps = models.PositiveIntegerField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    event_count = models.PositiveIntegerField(default=0)
    sandbox_calls = models.PositiveIntegerField(default=0)
    solver_sandbox_calls = models.PositiveIntegerField(default=0)
    turn_count = models.PositiveIntegerField(default=0)

    trajectory = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["sample_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["evaluation", "sample_id"],
                name="unique_sample_per_evaluation"
            )
        ]

    def __str__(self):
        return f"{self.sample_id} - {self.score}"
