"""
Repair resource estimate rows that are duplicated or carry wrong units.

Three defects, all found by checking extracted numbers against their own
arithmetic (tonnes x grade / 31.1035 must equal contained ounces):

1. Duplicate rows. The same technical report exists as two Document rows —
   Altar as doc:456 and doc:459, Calico as doc:102 and doc:141 — so extraction
   ran twice over it and produced identical estimates. Any tool that sums
   across a project counts those deposits twice.

2. Unit errors. Resource tables report contained metal in thousands of ounces
   ("koz", "'000 oz") and the extraction prompt never said which unit to
   return, so some rows hold 1,145 where the report meant 1,145,000. These are
   unambiguous: the implied-to-stated ratio lands almost exactly on 1000.

3. Rows that disagree with their own arithmetic for no clean reason, such as
   True North's 140,000 t at 4.11 g/t recorded as 1,100,000 oz when the
   tonnage and grade imply 18,500. Tonnage and grade corroborate each other
   against a single ounces figure, so the ounces field is the one to trust
   least; it is recomputed and the change logged individually.

Usage:
    python manage.py repair_resource_estimates --dry-run
    python manage.py repair_resource_estimates
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import ResourceEstimate

GRAMS_PER_TROY_OZ = Decimal('31.1035')

# How far stated ounces may drift from tonnes x grade before we treat the row
# as wrong. Rounding in published tables is well inside this.
TOLERANCE = Decimal('0.25')

# How close the implied/stated ratio must sit to 1000 to call it a koz error
# rather than a number that is simply wrong.
UNIT_RATIO_TOLERANCE = Decimal('0.05')


class Command(BaseCommand):
    help = "De-duplicate resource estimates and correct unit/arithmetic errors."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        self.dry_run = opts['dry_run']

        removed = self._dedupe()
        unit_fixed, recomputed = self._fix_metal('gold')
        s_unit, s_recomputed = self._fix_metal('silver')

        self.stdout.write(self.style.SUCCESS(
            f"\n{removed} duplicate row(s) removed, "
            f"{unit_fixed + s_unit} unit error(s) corrected, "
            f"{recomputed + s_recomputed} row(s) recomputed from tonnes x grade"
        ))
        if self.dry_run:
            self.stdout.write(self.style.NOTICE('Dry run — nothing written.'))

    # ------------------------------------------------------------------

    def _dedupe(self):
        """Drop rows identical on the fields that define an estimate."""
        seen, doomed = {}, []
        for est in ResourceEstimate.objects.order_by('id'):
            key = (est.project_id, est.category, est.report_date,
                   est.tonnes, est.gold_grade_gpt, est.silver_grade_gpt)
            if key in seen:
                doomed.append((est, seen[key]))
            else:
                seen[key] = est.id

        if doomed:
            self.stdout.write("\n=== duplicate rows ===")
        for est, kept_id in doomed:
            self.stdout.write(
                f"  drop #{est.id} (dup of #{kept_id}) {est.project.name[:28]:28s} "
                f"{est.category} {est.report_date} src={(est.report_url or '')[:10]}"
            )
        if doomed and not self.dry_run:
            with transaction.atomic():
                ResourceEstimate.objects.filter(id__in=[e.id for e, _ in doomed]).delete()
        return len(doomed)

    def _fix_metal(self, metal):
        """Correct stated ounces for one metal against tonnes x grade."""
        grade_field = f'{metal}_grade_gpt'
        oz_field = f'{metal}_ounces'

        unit_fixed = recomputed = 0
        header_written = False

        rows = (ResourceEstimate.objects
                .filter(tonnes__gt=0, **{f'{grade_field}__gt': 0,
                                         f'{oz_field}__gt': 0}))

        for est in rows:
            tonnes = est.tonnes
            grade = getattr(est, grade_field)
            stated = getattr(est, oz_field)

            implied = (tonnes * grade) / GRAMS_PER_TROY_OZ
            if implied <= 0:
                continue
            drift = abs(stated - implied) / implied
            if drift <= TOLERANCE:
                continue

            ratio = implied / stated
            is_unit_error = abs(ratio - 1000) / 1000 <= UNIT_RATIO_TOLERANCE
            corrected = (stated * 1000) if is_unit_error else implied

            if not header_written:
                self.stdout.write(f"\n=== {metal} ounces disagreeing with tonnes x grade ===")
                header_written = True
            self.stdout.write(
                f"  #{est.id:<5d} {est.project.name[:26]:26s} {est.category:<9s} "
                f"{float(stated):>12,.0f} -> {float(corrected):>12,.0f}  "
                f"{'koz unit error' if is_unit_error else 'recomputed (ratio %.1fx)' % float(ratio)}"
            )

            if is_unit_error:
                unit_fixed += 1
            else:
                recomputed += 1

            if not self.dry_run:
                setattr(est, oz_field, corrected.quantize(Decimal('1')))
                est.save(update_fields=[oz_field, 'updated_at'])

        return unit_fixed, recomputed
