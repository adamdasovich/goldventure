#!/usr/bin/env python
"""
Re-run project extraction for specific companies, one at a time.

These eleven extract zero projects (or carry no description) and are therefore
noindexed and absent from the sitemap -- the floor under the Search Console
"excluded by noindex" bucket. Six of them link their projects straight from
the homepage, so the extractor should find them now that the homepage is
always scraped and the website field points at the homepage.

Deliberately sequential and one browser at a time: the daily news batch runs
all morning and starting a parallel browser fleet against it exhausted swap
once already. Run under a memory-capped scope:

    systemd-run --scope -p MemoryMax=1200M \
      python /root/rescrape_projects.py 277 --apply

Dry run by default -- it still scrapes, it just does not write.

Only the scrape itself is async. Django's ORM refuses to run inside an async
context, so every read and write stays out here in sync code.
"""
import asyncio
import os
import sys

sys.path.insert(0, "/var/www/goldventure/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from core.models import Company, Project  # noqa: E402
from core.views.onboarding import _save_projects  # noqa: E402
from mcp_servers.company_scraper import scrape_company_website  # noqa: E402

APPLY = "--apply" in sys.argv
IDS = [int(a) for a in sys.argv[1:] if a.isdigit()]


def run_one(company):
    before = Project.objects.filter(company=company, is_active=True).count()
    print(f"\n=== {company.id}  {company.name}")
    print(f"    website: {company.website}")
    print(f"    projects before: {before}")

    try:
        data = asyncio.run(scrape_company_website(company.website))
    except Exception as exc:  # noqa: BLE001
        print(f"    SCRAPE FAILED: {type(exc).__name__}: {exc}")
        return

    # scrape_company() returns {"data": {...}, "errors": [...]}, not the
    # extracted data directly.
    payload = ((data or {}).get("data") or data or {})
    projects = payload.get("projects") or []
    print(f"    scraper found {len(projects)} project candidate(s)")
    for p in projects[:12]:
        print(
            f"      - {str(p.get('name', '?'))[:44]:<44} "
            f"{p.get('primary_commodity') or '-':<10} "
            f"{p.get('country') or '-'}"
        )

    desc = (payload.get("company") or {}).get("description") or ""

    # Only accept a description that is actually about this company.
    #
    # The first apply pass wrote a Metal Energy press release onto Ore Group --
    # a different company entirely -- because the scraper had picked a news item
    # out of the site's feed. It had to be cleared by hand. A description that
    # never names its own company is not a description.
    if desc:
        import re as _re

        stop = {"inc", "inc.", "ltd", "ltd.", "corp", "corp.", "corporation",
                "limited", "the", "group", "resources", "mining", "metals",
                "gold", "silver", "minerals", "exploration"}
        tokens = [
            w for w in _re.findall(r"[A-Za-z]+", company.name)
            if w.lower() not in stop and len(w) > 2
        ]
        mentions_company = (not tokens) or any(
            t.lower() in desc.lower() for t in tokens
        )

        looks_like_release = bool(
            _re.search(
                r"\(Newsfile|\(GLOBE NEWSWIRE|/CNW/|--\(BUSINESS WIRE\)|"
                r"^[A-Z][a-zA-Z .]+,\s+[A-Z][a-zA-Z .]+\s*[–—-]\s*\(",
                desc,
            )
        )

        if not mentions_company or looks_like_release:
            reason = (
                "does not name the company"
                if not mentions_company
                else "reads as a press release"
            )
            print(f"    description REJECTED ({reason}): {desc[:80]}...")
            desc = ""
    if desc and not company.description:
        print(f"    description found ({len(desc)} chars): {desc[:90]}...")

    if not APPLY:
        print("    (dry run -- nothing written)")
        return

    if projects:
        _save_projects(company, projects)
    if desc and not company.description:
        company.description = desc[:2000]
        company.save()

    after = Project.objects.filter(company=company, is_active=True).count()
    print(f"    projects after: {after}  (+{after - before})")


def main():
    if not IDS:
        print("usage: rescrape_projects.py <company_id> [more ids] [--apply]")
        return
    print("APPLY" if APPLY else "DRY RUN -- scrapes but does not write")
    for cid in IDS:
        try:
            company = Company.objects.get(pk=cid)
        except Company.DoesNotExist:
            print(f"\n=== {cid}  MISSING")
            continue
        run_one(company)
    print("\ndone")


if __name__ == "__main__":
    main()
