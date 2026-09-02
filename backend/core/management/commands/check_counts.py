"""
Assert that every number the site publishes matches the database.

Written after four separate count bugs shipped in one week, all of the same
shape — a plausible wrong number, no error, nobody notices:

  * /api/financings/?status=open silently ignored the filter and returned all
    297 rows, so "297 open financings" went into page copy, a pricing rationale
    and Google Ads assets. The real figure was 21.
  * /api/platform-stats/ counted NewsArticle (the ~1.9k scraped industry feed)
    and labelled it "news items" on the homepage, while the platform is built
    on ~17.9k NewsRelease rows.
  * "500+ companies" sat on the homepage, /companies, About, four guides and a
    live ad against a database of 396.
  * CompanyViewSet filtered is_active but not is_deleted, so a soft-deleted
    company would have stayed in the directory, the API and the sitemap.

Three of those four are checked here. The "500+ companies" one is NOT, and
cannot be: this drives the API through Django's test client and never reads the
frontend, so it cannot see a number typed into a component. That is a decision,
not a gap waiting to be filled -- several pages carry a legitimate "500+" about
the TSXV market as a whole, so scanning rendered copy for company-count claims
would fire on true statements, and a check that cries wolf gets ignored.

None of these threw. Tests that assert behaviour would not have caught them
either, because the code did exactly what it said — it just said the wrong
thing. What catches this class is comparing the published number against the
source of truth, which is all this does.

    python manage.py check_counts          # exits 1 on any mismatch
    python manage.py check_counts --json   # machine-readable

Run it after a deploy, or from cron. A non-zero exit means something the site
tells visitors is no longer true.
"""

import json

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.test import Client

from core.models import Company, Financing, NewsArticle, NewsRelease, Project


class Command(BaseCommand):
    help = "Verify published counts match the database."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="as_json")
        parser.add_argument(
            "--host",
            default="juniorminingintelligence.com",
            help="Host header; must be in ALLOWED_HOSTS or every request 400s.",
        )

    def handle(self, *args, **options):
        # SERVER_NAME matters: the Django test client sends "testserver" by
        # default, which prod's ALLOWED_HOSTS rejects with a 400 before any view
        # runs — every assertion then fails for the wrong reason.
        client = Client(SERVER_NAME=options["host"])

        # /api/platform-stats/ caches for 10 minutes. The scrapers add news
        # releases continuously, so a cached payload is routinely a few rows
        # behind the database and this command reported a mismatch that was
        # only cache age — 17,912 against 17,914 on the first run after the
        # scraper ticked. An assertion that cries wolf gets ignored, which is
        # worse than not having it, so drop the key and compare what the
        # endpoint actually computes.
        cache.delete("platform_stats_v2")
        checks = []

        def check(label, actual, expected, note=""):
            checks.append({
                "check": label,
                "actual": actual,
                "expected": expected,
                "ok": actual == expected,
                "note": note,
            })

        # --- source of truth -------------------------------------------------
        live_companies = Company.objects.filter(is_deleted=False).count()
        open_financings = Financing.objects.filter(is_closed=False).count()
        closed_financings = Financing.objects.filter(is_closed=True).count()

        # --- /api/platform-stats/ -------------------------------------------
        r = client.get("/api/platform-stats/")
        if r.status_code == 200:
            s = r.json()
            check("platform-stats.companies", s.get("companies"), live_companies,
                  "excludes soft-deleted")
            check("platform-stats.projects", s.get("projects"),
                  Project.objects.count())
            check("platform-stats.open_financings", s.get("open_financings"),
                  open_financings)
            check("platform-stats.news_releases", s.get("news_releases"),
                  NewsRelease.objects.count(),
                  "company press releases, NOT the NewsArticle industry feed")
            check("platform-stats.news_articles", s.get("news_articles"),
                  NewsArticle.objects.count())
        else:
            check("platform-stats reachable", r.status_code, 200)

        # --- /api/open-financings/ ------------------------------------------
        r = client.get("/api/open-financings/")
        if r.status_code == 200:
            check("open-financings.total_count", r.json().get("total_count"),
                  open_financings)
        else:
            check("open-financings reachable", r.status_code, 200)

        # --- the filter that silently did nothing ---------------------------
        r = client.get("/api/financings/", {"status": "open", "page_size": 1})
        if r.status_code == 200:
            check("financings?status=open", r.json().get("count"), open_financings,
                  "returned ALL financings before 2026-08-31")
        else:
            check("financings?status=open reachable", r.status_code, 200)

        r = client.get("/api/financings/", {"status": "closed", "page_size": 1})
        if r.status_code == 200:
            check("financings?status=closed", r.json().get("count"),
                  closed_financings)

        # An unknown parameter must be rejected, not ignored. This is the
        # guard itself, so it is worth asserting that the guard still guards.
        r = client.get("/api/financings/", {"stauts": "open"})
        check("financings rejects unknown param", r.status_code, 400,
              "a typo must 400, not return the whole table")

        # --- the directory must not serve deleted companies -----------------
        r = client.get("/api/companies/", {"page_size": 1})
        if r.status_code == 200:
            check("companies list excludes deleted", r.json().get("count"),
                  Company.objects.filter(is_active=True, is_deleted=False).count())

        failed = [c for c in checks if not c["ok"]]

        if options["as_json"]:
            self.stdout.write(json.dumps(
                {"ok": not failed, "checks": checks}, indent=2))
        else:
            for c in checks:
                mark = "PASS" if c["ok"] else "FAIL"
                line = "  [%s] %-42s actual=%-8s expected=%s" % (
                    mark, c["check"], c["actual"], c["expected"])
                if not c["ok"] and c["note"]:
                    line += "\n         %s" % c["note"]
                self.stdout.write(line)
            self.stdout.write("\n  %d/%d passed" % (
                len(checks) - len(failed), len(checks)))

        if failed:
            raise SystemExit(1)
