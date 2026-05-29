"""
Backfill NewsRelease.is_material based on release_type.

Historically the flag was either always False (one ingest path) or set to
"is_financial" (the wrong field — financial-statement titles, not material
events). After news_classification.is_material_release_type was added,
this command syncs every existing row to the new rule:

  is_material = release_type in MATERIAL_RELEASE_TYPES
                # drill_results, resource_update, study_results,
                # financing, acquisition
"""

from django.core.management.base import BaseCommand

from core.models import NewsRelease
from core.news_classification import MATERIAL_RELEASE_TYPES


class Command(BaseCommand):
    help = "Sync NewsRelease.is_material to match release_type-based classification."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Show counts but do not write.",
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        material_qs = NewsRelease.objects.filter(release_type__in=MATERIAL_RELEASE_TYPES)
        non_material_qs = NewsRelease.objects.exclude(release_type__in=MATERIAL_RELEASE_TYPES)

        to_set_true = material_qs.filter(is_material=False).count()
        to_set_false = non_material_qs.filter(is_material=True).count()

        self.stdout.write(
            f"Material release_types: {sorted(MATERIAL_RELEASE_TYPES)}"
        )
        self.stdout.write(f"To flip False -> True: {to_set_true}")
        self.stdout.write(f"To flip True  -> False: {to_set_false}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — no rows updated."))
            return

        updated_true = material_qs.filter(is_material=False).update(is_material=True)
        updated_false = non_material_qs.filter(is_material=True).update(is_material=False)

        self.stdout.write(self.style.SUCCESS(
            f"Updated {updated_true} rows -> is_material=True"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Updated {updated_false} rows -> is_material=False"
        ))
