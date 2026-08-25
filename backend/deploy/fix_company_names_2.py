#!/usr/bin/env python
"""
Second pass on the scraper-mangled company names: add the corporate suffix
the first pass deliberately left off because it was not evidenced.

The first pass stripped page-title junk and refused to invent a suffix it
could not back. Adam confirmed the corporate name, which is the evidence that
was missing.

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

APPLY = "--apply" in sys.argv

# id: (name_we_expect_to_find, corrected_name, evidence)
FIXES = {
    52: (
        "Quartz Mountain Resources",
        "Quartz Mountain Resources Ltd.",
        "corporate suffix confirmed by Adam 2026-08-25",
    ),
}


def main():
    print("APPLY" if APPLY else "DRY RUN -- nothing will be written")
    print("=" * 70)
    for cid, (expected, new_name, evidence) in sorted(FIXES.items()):
        try:
            c = Company.objects.get(pk=cid)
        except Company.DoesNotExist:
            print(f"{cid:>4}  MISSING -- skipped")
            continue
        if c.name != expected:
            print(f"{cid:>4}  SKIP -- expected {expected!r}, found {c.name!r}")
            continue

        new_slug = slugify(new_name)[:220]
        clash = Company.objects.filter(slug=new_slug).exclude(pk=cid).values_list("id", "name")
        if clash:
            print(f"{cid:>4}  SKIP -- slug {new_slug!r} taken by {list(clash)}")
            continue

        print(f"{cid:>4}  {c.name!r}  ->  {new_name!r}")
        print(f"      why:  {evidence}")
        print(f"      slug: {c.slug}  ->  {new_slug}")
        print(f"      legal_name: {c.legal_name!r} (left as-is)")

        if APPLY:
            c.name = new_name
            c.save()  # regenerates slug; a queryset .update() would not
            c.refresh_from_db()
            print(f"      written -- slug now {c.slug!r}")
    print("=" * 70)
    if not APPLY:
        print("Re-run with --apply to write.")


if __name__ == "__main__":
    main()
