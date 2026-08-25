#!/usr/bin/env python
"""
Fill blank project commodities from unanimous sibling consensus.

336 projects carry no primary_commodity. Their names gave nothing, only 6 have
a description to score, and scraping every project detail page is hours of
browser time.

Sibling consensus is the one inference here that carries no facet risk. The
standing rule in this codebase is that a commodity must not be guessed, because
a wrong value puts a company on the wrong landing page. That consequence does
not apply when every other project at the company already shares one commodity:
the company is on that facet already, so filling the blank adds no new
membership anywhere.

Two guards, both added after reading the first dry run:

  * At least TWO agreeing siblings. A single tagged project is a data point,
    not a consensus -- "Bathurst Project" at Visionary Copper and Gold was
    about to be filed as zinc on the strength of one sibling.

  * The project name must not denote a different material. "Black Point
    Aggregate Project" at Morien Resources was about to become gold because
    Morien's other projects are; construction aggregate is not gold, and no
    amount of sibling agreement makes it so.

Deliberately NOT applying the description-only signal. Those companies have no
other tagged project, so a value drawn from marketing copy would add genuinely
new facet membership on weak evidence.

Dry run by default. Pass --apply to write.
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, "/var/www/goldventure/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from core.models import Project  # noqa: E402

APPLY = "--apply" in sys.argv
MIN_SIBLINGS = 2

# Materials that are not the metal its siblings carry. A project named for one
# of these is its own thing regardless of what the rest of the portfolio holds.
NON_METAL = re.compile(
    r"\b(aggregate|quarry|sand|gravel|limestone|dolomite|gypsum|coal|"
    r"potash|salt|brine field|clay|kaolin|silica|frac sand|peat|"
    r"oil|gas|geothermal|water)\b",
    re.IGNORECASE,
)


def main():
    print("APPLY" if APPLY else "DRY RUN -- nothing will be written")
    print("=" * 78)

    blank = Project.objects.filter(primary_commodity="").select_related("company")
    total = blank.count()
    filled = Counter()
    skipped_mixed = skipped_none = skipped_thin = skipped_material = 0
    examples = []
    blocked = []

    for project in blank:
        if NON_METAL.search(project.name or ""):
            skipped_material += 1
            blocked.append(f"{project.name[:40]} ({project.company.name[:24]})")
            continue

        siblings = [
            p.primary_commodity
            for p in project.company.projects.filter(is_active=True).exclude(
                primary_commodity=""
            )
            if p.id != project.id
        ]
        if not siblings:
            skipped_none += 1
            continue

        distinct = set(siblings)
        if len(distinct) != 1:
            skipped_mixed += 1
            continue
        if len(siblings) < MIN_SIBLINGS:
            skipped_thin += 1
            continue

        value = distinct.pop()
        filled[value] += 1
        if len(examples) < 12:
            examples.append((project.name, project.company.name, value, len(siblings)))

        if APPLY:
            project.primary_commodity = value[:50]
            project.save(update_fields=["primary_commodity"])

    n = sum(filled.values())
    print(f"blank commodity projects            : {total}")
    print(f"{'filled' if APPLY else 'would fill'} from >= {MIN_SIBLINGS} agreeing siblings : {n}")
    print(f"skipped, only one tagged sibling    : {skipped_thin}")
    print(f"skipped, siblings disagree          : {skipped_mixed}")
    print(f"skipped, no tagged siblings         : {skipped_none}")
    print(f"skipped, name denotes another material : {skipped_material}")
    print()
    for value, count in filled.most_common():
        print(f"   {count:>4}  {value}")
    print()
    print("  sample:")
    for name, company, value, count in examples:
        print(f"    {name[:32]:<32} {company[:24]:<24} -> {value:<9} (n={count})")
    if blocked:
        print()
        print("  blocked by the material guard:")
        for b in blocked[:10]:
            print(f"    {b}")

    print("=" * 78)
    if not APPLY:
        print("Re-run with --apply to write.")


if __name__ == "__main__":
    main()
