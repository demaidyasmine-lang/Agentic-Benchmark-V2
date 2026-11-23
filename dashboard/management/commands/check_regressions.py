from django.core.management.base import BaseCommand, CommandError

from dashboard.models import EvaluationRun


class Command(BaseCommand):
    help = "Compare les deux dernières évaluations et détecte les régressions."

    def handle(self, *args, **options):
        categories = ["SQL", "API", "REPOSITORY"]
        total_issues = 0
        compared_categories = 0

        self.stdout.write("\nCONTROLE DES REGRESSIONS")
        self.stdout.write("--------------------------------")

        for category in categories:
            evaluations = list(
                EvaluationRun.objects.filter(
                    category=category,
                    status="SUCCESS"
                ).order_by("-log_path")[:2]
            )

            if len(evaluations) < 2:
                self.stdout.write(
                    f"{category} : comparaison impossible "
                    "(pas encore deux évaluations)."
                )
                continue

            current, baseline = evaluations[0], evaluations[1]

            previous_results = {
                result.sample_id: result
                for result in baseline.task_results.all()
            }
            current_results = {
                result.sample_id: result
                for result in current.task_results.all()
            }

            previous_ids = set(previous_results)
            current_ids = set(current_results)

            missing_ids = sorted(previous_ids - current_ids)
            added_ids = sorted(current_ids - previous_ids)

            regressions = sorted(
                sample_id
                for sample_id in previous_ids & current_ids
                if previous_results[sample_id].passed
                and not current_results[sample_id].passed
            )

            compared_categories += 1

            self.stdout.write(f"\nBenchmark : {category}")
            self.stdout.write(f"Référence : {baseline.log_path}")
            self.stdout.write(f"Nouvelle évaluation : {current.log_path}")

            issues = len(regressions) + len(missing_ids) + len(added_ids)

            if issues:
                total_issues += issues
                self.stdout.write(self.style.ERROR(
                    f"ECHEC : {issues} anomalie(s) détectée(s)"
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
                    "OK : aucune régression ni modification des tâches."
                ))

        self.stdout.write("\n--------------------------------")

        if compared_categories == 0:
            self.stdout.write(
                "Aucune catégorie ne possède encore deux évaluations comparables."
            )
            return

        if total_issues:
            raise CommandError(
                f"Contrôle échoué : {total_issues} anomalie(s) détectée(s)."
            )

        self.stdout.write(self.style.SUCCESS(
            "CONTROLE REUSSI : aucune anomalie détectée."
        ))
