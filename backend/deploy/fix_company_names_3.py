#!/usr/bin/env python
"""
Third pass on scraper-mangled company names.

These three were missed by the first audit, which looked for a *closed*
trailing parenthetical. Each of these was truncated mid-listing, so the
bracket never closed:

    "Galway Metals Inc. (TSX.V"
    "Military Metals Corp (CSE: MILI"
    "Trident Resources Corp (TSX-V: ROCK"

They surfaced when clean_company_name() was validated against all 396 names
in the database -- the validation run was the thing that found them.

The corrected values are exactly what clean_company_name() now produces, so
the repair and the prevention agree. legal_name mirrors the junk in all three
and is cleared, as in the first pass.

Dry run by default. Pass --apply to write.
"""
import os
import sys

sys.path.insert(0, "/var/www/goldventure/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.utils.text import slugify  # noqa: E402

from core.models import Company  # noqa: E402
from mcp_servers.company_scraper import clean_company_name  # noqa: E402

APPLY = "--apply" in sys.argv

EXPECTED = {
    333: "Galway Metals Inc. (TSX.V",
    359: "Military Metals Corp (CSE: MILI",
    236: "Trident Resources Corp (TSX-V: ROCK",
}


def main():
    print("APPLY" if APPLY else "DRY RUN -- nothing will be written")
    print("=" * 72)
    for cid, expected in sorted(EXPECTED.items()):
        try:
            c = Company.objects.get(pk=cid)
        except Company.DoesNotExist:
            print(f"{cid:>4}  MISSING -- skipped")
            continue
        if c.name != expected:
            print(f"{cid:>4}  SKIP -- expected {expected!r}, found {c.name!r}")
            continue

        new_name = clean_company_name(c.name)
        if not new_name or new_name == c.name:
            print(f"{cid:>4}  SKIP -- cleaner returned {new_name!r}, no change")
            continue

        new_slug = slugify(new_name)[:220]
        clash = Company.objects.filter(slug=new_slug).exclude(pk=cid).values_list("id", "name")
        if clash:
            print(f"{cid:>4}  SKIP -- slug {new_slug!r} taken by {list(clash)}")
            continue

        clear_legal = c.legal_name == expected
        print(f"{cid:>4}  {c.name!r}")
        print(f"      ->   {new_name!r}   (from clean_company_name)")
        print(f"      slug: {c.slug}  ->  {new_slug}")
        if clear_legal:
            print("      legal_name: cleared (was the same junk)")

        if APPLY:
            c.name = new_name
            if clear_legal:
                c.legal_name = ""
            c.save()  # regenerates slug; a queryset .update() would not
            c.refresh_from_db()
            print(f"      written -- name {c.name!r}, slug {c.slug!r}")
        print("")
    print("=" * 72)
    if not APPLY:
        print("Re-run with --apply to write.")


if __name__ == "__main__":
    main()
