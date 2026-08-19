"""Correct press releases stored with a future release_date.

Cause: both scrapers inferred the year for a date published without one by
comparing month only, so any day later in the current month resolved to the
current year instead of the previous one. Fixed in website_crawler and
company_scraper; this repairs the rows already written.

The correction is exactly minus one year. The month and day were parsed
correctly from the source; only the inferred year was wrong, and the fixed
parser produces precisely this result for the same input.

Run with --apply to write. Without it, prints what it would do and changes
nothing.
"""

import os
import sys

import django

# Staged in /root and run by path, so the project is not on sys.path already.
BACKEND = "/var/www/goldventure/backend"
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.utils import timezone  # noqa: E402

from core.models import NewsRelease  # noqa: E402

APPLY = "--apply" in sys.argv

today = timezone.now().date()
rows = NewsRelease.objects.filter(release_date__gt=today).order_by("release_date")

print(f"today: {today}")
print(f"releases dated in the future: {rows.count()}")
print()

changed = 0
skipped = 0
for n in rows:
    old = n.release_date
    new = old.replace(year=old.year - 1)

    # Refuse anything that does not land in the past — a row this does not fix
    # needs a human, not a second guess.
    if new >= today:
        print(f"  SKIP  id={n.id}  {old} -> {new} still not in the past")
        skipped += 1
        continue

    print(f"  {'FIX ' if APPLY else 'WOULD'}  id={n.id}  {old} -> {new}  "
          f"{n.company.name[:24]:24}  {n.title[:44]}")
    if APPLY:
        n.release_date = new
        n.save(update_fields=["release_date"])
    changed += 1

print()
print(f"{'corrected' if APPLY else 'would correct'}: {changed}    skipped: {skipped}")
if not APPLY:
    print("\nDry run. Re-run with --apply to write.")
else:
    remaining = NewsRelease.objects.filter(release_date__gt=today).count()
    print(f"remaining future-dated rows: {remaining}")
