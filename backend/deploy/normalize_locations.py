#!/usr/bin/env python
"""
Normalise project country values, and company exchange casing.

Three problems, all the same class as the 'Gold' vs 'gold' commodity casing
fixed earlier -- nothing breaks today, but every GROUP BY and every distinct
audit lies, and they split what should be one bucket:

  * 'United States' (17) alongside 'USA' (109). _REGION_TO_COUNTRY in
    company_scraper already treats USA as canonical, so that wins.
  * 46 projects carry a province or state in `country`: Nevada, Ontario,
    British Columbia, Yukon, Saskatchewan, Colorado, Alaska, Arizona, Wyoming.
    Those map to their country, and the region moves into province_state when
    that field is empty rather than being discarded.
  * One company has exchange 'TSXV' where 269 have 'tsxv'.

Uses the scraper's own _REGION_TO_COUNTRY so this and the extractor cannot
disagree about which country a region belongs to.

Dry run by default. Pass --apply to write.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, "/var/www/goldventure/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from core.models import Company, Project  # noqa: E402
from mcp_servers.company_scraper import _REGION_TO_COUNTRY  # noqa: E402

APPLY = "--apply" in sys.argv

# Spellings of the same country.
COUNTRY_ALIASES = {
    "united states": "USA",
    "united states of america": "USA",
    "u.s.a.": "USA",
    "us": "USA",
}


def main():
    print("APPLY" if APPLY else "DRY RUN -- nothing will be written")

    print("=" * 74)
    print("PROJECT COUNTRY")
    print("=" * 74)
    moved = Counter()
    aliased = Counter()

    for project in Project.objects.exclude(country="").exclude(country="Unknown"):
        raw = (project.country or "").strip()
        key = raw.lower()

        target = None
        region_to_move = None

        if key in COUNTRY_ALIASES:
            target = COUNTRY_ALIASES[key]
            aliased[f"{raw} -> {target}"] += 1
        elif key in _REGION_TO_COUNTRY:
            target = _REGION_TO_COUNTRY[key]
            region_to_move = raw
            moved[f"{raw} -> {target}"] += 1

        if not target or target == raw:
            continue

        if APPLY:
            project.country = target[:100]
            # Keep the region rather than discarding it, but never overwrite a
            # province_state that already holds something.
            if region_to_move and not (project.province_state or "").strip():
                project.province_state = region_to_move[:100]
                project.save(update_fields=["country", "province_state"])
            else:
                project.save(update_fields=["country"])

    print("spelling variants folded:")
    for k, v in aliased.most_common():
        print(f"   {v:>4}  {k}")
    print("\nregions moved to their country (region kept in province_state):")
    for k, v in moved.most_common():
        print(f"   {v:>4}  {k}")
    print(f"\ntotal projects touched: {sum(aliased.values()) + sum(moved.values())}")

    print()
    print("=" * 74)
    print("COMPANY EXCHANGE")
    print("=" * 74)
    fixed = 0
    for company in Company.objects.exclude(exchange=""):
        raw = company.exchange or ""
        norm = raw.strip().lower()
        if raw == norm:
            continue
        print(f"   {company.id:>4}  {company.name[:34]:<34} {raw!r} -> {norm!r}")
        if APPLY:
            company.exchange = norm[:20]
            company.save(update_fields=["exchange"])
        fixed += 1
    print(f"\ncompanies touched: {fixed}")

    print("=" * 74)
    if not APPLY:
        print("Re-run with --apply to write.")


if __name__ == "__main__":
    main()
