#!/usr/bin/env python
"""
Repair company names that the onboarding scraper lifted from a page <title>.

Fifteen companies carry a name like "Rokmaster Resources Website" or
"Waratah Minerals - ASX:WTM". The name drives the <h1>, <title>, meta
description, JSON-LD and -- via Company.save() -- the slug, so each of these
is wrong on a live, sitemap-submitted page.

legal_name is identical to name in every case (the scraper wrote both), so it
is not a fallback. It is cleared rather than overwritten: the corrected value
is a common name, not a legal name, and storing it as one would just re-seed
the same confusion later.

Dry run by default. Pass --apply to write.

    cd /var/www/goldventure/backend && source venv/bin/activate
    python /root/fix_company_names.py            # dry run
    python /root/fix_company_names.py --apply
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

# id: (name_we_expect_to_find, corrected_name, evidence, is_judgement_call)
#
# The expected-current-name guard matters: another session edits this repo and
# database, so a record that has already changed underneath us is skipped
# rather than clobbered.
FIXES = {
    33: (
        "Blackrock Silver- Silver, Gold & Lithium Exploration",
        "Blackrock Silver",
        "25/25 press releases lead with it",
        False,
    ),
    52: (
        "Quartz Mountain Resources Exploration in British Columbia",
        "Quartz Mountain Resources",
        "releases lead 'Quartz Mountain'; corporate suffix not evidenced",
        True,
    ),
    118: (
        "GR Silver Mining (GRSL)",
        "GR Silver Mining",
        "parenthetical is the ticker, already held in ticker_symbol",
        False,
    ),
    125: (
        "Klondike Gold Corp. ‹ Building Gold Resources in Historic Klondike Goldfields",
        "Klondike Gold Corp.",
        "company's own description",
        False,
    ),
    129: (
        "Max Resource Corp. (MAX.V)",
        "Max Resource Corp.",
        "parenthetical is the ticker",
        False,
    ),
    147: (
        "Perpetua Resources Home",
        "Perpetua Resources",
        "21 press releases",
        False,
    ),
    181: (
        "LAHONTAN GOLD CORP",
        "Lahontan Gold Corp.",
        "description: 'Lahontan Gold Corp (LG)'",
        False,
    ),
    200: (
        "Provenance Gold Corp. (PAU.CN)",
        "Provenance Gold Corp.",
        "company's own description",
        False,
    ),
    267: (
        "BULGOLD",
        "BULGOLD Inc.",
        "description: 'BULGOLD Inc. (“BULGOLD”)'; caps are the brand, not shouting",
        True,
    ),
    270: (
        "BWR EXPLORATION",
        "BWR Exploration",
        "description: 'BWR Exploration is a mining exploration company'",
        False,
    ),
    281: (
        "DOMESTIC METALS",
        "Domestic Metals",
        "23 press releases",
        False,
    ),
    299: (
        "Nouveau Monde Graphite » Solutions zéro-carbone™",
        "Nouveau Monde Graphite",
        "text after the separator is a tagline",
        False,
    ),
    312: (
        "THUNDER GOLD CORP",
        "Thunder Gold Corp.",
        "25/25 press releases",
        False,
    ),
    392: (
        "Rokmaster Resources Website",
        "Rokmaster Resources Corp.",
        "company's own description",
        False,
    ),
    421: (
        "Waratah Minerals • ASX:WTM",
        "Waratah Minerals",
        "text after the separator is the listing",
        False,
    ),
}


def main():
    print("APPLY" if APPLY else "DRY RUN -- nothing will be written")
    print("=" * 78)

    changed = skipped = 0
    slug_moves = []

    for cid, (expected, new_name, evidence, judgement) in sorted(FIXES.items()):
        try:
            c = Company.objects.get(pk=cid)
        except Company.DoesNotExist:
            print(f"{cid:>4}  MISSING -- no such company, skipped")
            skipped += 1
            continue

        if c.name != expected:
            print(f"{cid:>4}  SKIP -- name is not what this script was written against")
            print(f"      expected: {expected!r}")
            print(f"      found:    {c.name!r}")
            skipped += 1
            continue

        old_slug = c.slug
        new_slug = slugify(new_name)[:220]

        # A slug collision would break the unique lookup key; bail loudly
        # rather than silently producing a duplicate URL.
        clash = (
            Company.objects.filter(slug=new_slug).exclude(pk=cid).values_list("id", "name")
        )
        if clash:
            print(f"{cid:>4}  SKIP -- new slug {new_slug!r} already used by {list(clash)}")
            skipped += 1
            continue

        # legal_name is junk exactly when it matches the junk name. If someone
        # has since put a real legal name there, leave it alone.
        clear_legal = c.legal_name == expected
        old_legal = c.legal_name

        tag = "  [judgement call]" if judgement else ""
        print(f"{cid:>4}  {c.name!r}")
        print(f"      ->   {new_name!r}{tag}")
        print(f"      why: {evidence}")
        print(f"      slug: {old_slug}  ->  {new_slug}")
        if clear_legal:
            print(f"      legal_name: {old_legal!r}  ->  '' (cleared, was the same junk)")
        elif old_legal:
            print(f"      legal_name: {old_legal!r}  (left alone, not the junk value)")

        if APPLY:
            c.name = new_name
            if clear_legal:
                c.legal_name = ""
            # save() regenerates the slug from name -- must not be a
            # queryset .update(), which would bypass it and strand the URL.
            c.save()
            c.refresh_from_db()
            if c.slug != new_slug:
                print(f"      !! slug did not regenerate as expected: {c.slug!r}")
            else:
                print("      written")

        slug_moves.append((cid, old_slug, new_slug))
        changed += 1
        print("")

    print("=" * 78)
    print(f"{'changed' if APPLY else 'would change'}: {changed}    skipped: {skipped}")
    print("")
    print("URL moves (old path keeps returning 200; its canonical self-heals to the new one):")
    for cid, old, new in slug_moves:
        print(f"  /companies/{cid}-{old}")
        print(f"  /companies/{cid}-{new}")
    if not APPLY:
        print("")
        print("Re-run with --apply to write.")


if __name__ == "__main__":
    main()
