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

3. Rows that disagree with their own arithmetic for no clean reason. These are
   REPORTED, NOT CHANGED. It is tempting to trust tonnage and grade over a
   single ounces figure and recompute, but True North shows why that is wrong:
   140,000 t at 4.11 g/t against 1,100,000 oz recorded. Roughly 1.1 Moz is a
   plausible M&I for that deposit while 140,000 t is not, and its gold and
   silver rows are both out by the same ~60x — so the tonnage is the bad field
   and recomputing would have discarded the one correct number. Which field is
   wrong cannot be decided from the row alone, so these need a human against
   the source report. Pass --recompute-ambiguous to force the arithmetic.

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
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--recompute-ambiguous', action='store_true',
                            help="Also overwrite ounces that disagree for no clean "
                                 "reason. Off by default: the wrong field may be "
                                 "tonnes, not ounces.")

    def handle(self, *args, **opts):
        self.dry_run = opts['dry_run']
        self.recompute_ambiguous = opts['recompute_ambiguous']

        # Units first: two copies of a row that differ only because one was read
        # as koz are not detectable as duplicates until both are in the same
        # unit, and de-duplicating first could keep the wrong copy.
        unit_fixed, flagged = self._fix_metal('gold')
        s_unit, s_flagged = self._fix_metal('silver')
        removed = self._dedupe()

        verb = 'recomputed' if self.recompute_ambiguous else 'FLAGGED for review'
        self.stdout.write(self.style.SUCCESS(
            f"\n{unit_fixed + s_unit} unit error(s) corrected, "
            f"{removed} duplicate row(s) removed, "
            f"{flagged + s_flagged} row(s) {verb}"
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

        unit_fixed = flagged = 0
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
                f"{'koz unit error — fixing' if is_unit_error else 'AMBIGUOUS (%.0fx) — review, not changed' % float(ratio if ratio > 1 else 1 / ratio)}"
            )

            if is_unit_error:
                unit_fixed += 1
            else:
                flagged += 1
                if not self.recompute_ambiguous:
                    continue

            if not self.dry_run:
                setattr(est, oz_field, corrected.quantize(Decimal('1')))
                est.save(update_fields=[oz_field, 'updated_at'])

        return unit_fixed, flagged
