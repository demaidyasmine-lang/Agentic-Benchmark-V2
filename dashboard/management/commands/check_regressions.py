


import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from dashboard.models import EvaluationRun


class Command(BaseCommand):
    help = "Compare les évaluations aux références officielles du benchmark."

    def add_arguments(self, parser):
        parser.add_argument(
            "--baseline",
            type=str,
            default=None,
            help="Chemin vers le fichier JSON de référence."
        )

    def handle(self, *args, **options):
        baseline_path = (
            Path(options["baseline"])
            if options["baseline"]
            else Path(settings.BASE_DIR)
            / "benchmark"
            / "baselines"
            / "regression_baseline.json"
        )

        try:
            with baseline_path.open("r", encoding="utf-8-sig") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise CommandError(
                f"Impossible de lire le fichier de référence : {error}"
            )

        if (
            not isinstance(data, dict)
            or data.get("version") != 1
            or not isinstance(data.get("baselines"), list)
        ):
            raise CommandError("Format du fichier de référence invalide.")

        baselines = data["baselines"]

        if not baselines:
            raise CommandError("Aucune référence trouvée.")

        seen = set()
        total_issues = 0

        self.stdout.write("\nCONTROLE DES REGRESSIONS")
        self.stdout.write("--------------------------------")

        for baseline in baselines:
            if not isinstance(baseline, dict):
                raise CommandError(
                    "Une référence contient des données invalides."
                )

            agent_name = baseline.get("agent_name")
            category = baseline.get("category")
            passed_samples = baseline.get("passed_samples")

            if (
                not isinstance(agent_name, str)
                or not agent_name.strip()
                or category not in ["SQL", "API", "REPOSITORY"]
                or not isinstance(passed_samples, list)
                or not passed_samples
                or not all(
                    isinstance(sample, str) and sample.strip()
                    for sample in passed_samples
                )
            ):
                raise CommandError(
                    "Une référence contient des données invalides."
                )

            key = (agent_name, category)

            if key in seen:
                raise CommandError(
                    f"Référence dupliquée : {agent_name} / {category}"
                )

            seen.add(key)

            if len(passed_samples) != len(set(passed_samples)):
                raise CommandError(
                    f"Identifiants dupliqués pour {agent_name} / {category}."
                )

            evaluation = (
                EvaluationRun.objects.filter(
                    category=category,
                    agent_name=agent_name,
                    status="SUCCESS"
                )
                .order_by("-created_at", "-id")
                .first()
            )

            self.stdout.write(f"\nBenchmark : {category}")
            self.stdout.write(f"Agent : {agent_name}")

            if evaluation is None:
                total_issues += 1
                self.stdout.write(self.style.ERROR(
                    "ECHEC : aucune évaluation réussie trouvée."
                ))
                continue

            current_results = {
                result.sample_id: result
                for result in evaluation.task_results.all()
            }

            baseline_ids = set(passed_samples)
            current_ids = set(current_results)

            missing_ids = sorted(baseline_ids - current_ids)
            added_ids = sorted(current_ids - baseline_ids)

            regressions = sorted(
                sample_id
                for sample_id in baseline_ids & current_ids
                if not current_results[sample_id].passed
            )

            issues = len(missing_ids) + len(added_ids) + len(regressions)
            total_issues += issues

            self.stdout.write(
                f"Évaluation : {evaluation.log_path}"
            )

            if issues:
                self.stdout.write(self.style.ERROR(
                    f"ECHEC : {issues} anomalie(s) détectée(s)."
                ))

                for sample_id in regressions:
                    self.stdout.write(
                        self.style.ERROR(f"  - Régression : {sample_id}")
                    )

                for sample_id in missing_ids:
                    self.stdout.write(
                        self.style.ERROR(f"  - Tâche manquante : {sample_id}")
                    )

                for sample_id in added_ids:
                    self.stdout.write(
                        self.style.ERROR(f"  - Nouvelle tâche : {sample_id}")
                    )
            else:
                self.stdout.write(self.style.SUCCESS(
                    "OK : aucune régression détectée."
                ))

        self.stdout.write("\n--------------------------------")

        if total_issues:
            raise CommandError(
                f"Contrôle échoué : {total_issues} anomalie(s) détectée(s)."
            )

        self.stdout.write(self.style.SUCCESS(
            "CONTROLE REUSSI : toutes les références sont respectées."
        ))
