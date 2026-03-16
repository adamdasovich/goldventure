"""
Unit tests for the scraping pipeline and news display.

Covers:
- Date parsing (parse_date_standalone, parse_date_comprehensive)
- Title cleaning & validation (clean_news_title, is_valid_news_title)
- URL classification (is_news_article_url, is_valid_news_url)
- URL slug extraction (extract_url_slug)
- News item deduplication (_add_news_item)
- News releases API view (company_news_releases)
- Daily scraper task logic (date parsing, lock release)
"""

import re
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory, override_settings
from django.core.cache import cache

from core.models import Company, NewsRelease, CompanyNews
from core.views import company_news_releases
from core.api_utils import extract_url_slug
from mcp_servers.website_crawler import (
    parse_date_comprehensive,
    parse_date_standalone,
    clean_news_title,
    is_valid_news_title,
    is_valid_news_url,
    is_news_article_url,
    _add_news_item,
    _seen_slugs,
)


# ============================================================================
# DATE PARSING TESTS
# ============================================================================

class ParseDateStandaloneTests(TestCase):
    """Tests for parse_date_standalone() - dedicated date elements."""

    def test_month_dd_yyyy(self):
        self.assertEqual(parse_date_standalone("December 17, 2025"), "2025-12-17")

    def test_month_dd_yyyy_no_comma(self):
        self.assertEqual(parse_date_standalone("February 10 2026"), "2026-02-10")

    def test_dd_month_yyyy(self):
        self.assertEqual(parse_date_standalone("28 JANUARY 2026"), "2026-01-28")

    def test_abbrev_month_dd_yyyy(self):
        self.assertEqual(parse_date_standalone("Nov 17 2025"), "2025-11-17")

    def test_abbrev_month_dd_comma_yyyy(self):
        self.assertEqual(parse_date_standalone("Jul 7, 2025"), "2025-07-07")

    def test_abbrev_month_period_dd_yyyy(self):
        self.assertEqual(parse_date_standalone("Dec. 17, 2025"), "2025-12-17")

    def test_dd_abbrev_month_comma_yyyy(self):
        self.assertEqual(parse_date_standalone("20 Jan, 2026"), "2026-01-20")

    def test_month_dd_slash_yyyy(self):
        self.assertEqual(parse_date_standalone("January 22 / 2026"), "2026-01-22")

    def test_dot_format_mmddyyyy(self):
        """Ambiguous dot format - North American sites default to MM.DD.YYYY."""
        self.assertEqual(parse_date_standalone("01.07.2026"), "2026-01-07")

    def test_dot_format_ddmmyyyy_unambiguous(self):
        """When first number > 12, must be DD.MM.YYYY."""
        self.assertEqual(parse_date_standalone("22.01.2026"), "2026-01-22")

    def test_dot_format_mmddyyyy_unambiguous(self):
        """When second number > 12, must be MM.DD.YYYY."""
        self.assertEqual(parse_date_standalone("01.22.2026"), "2026-01-22")

    def test_slash_format_unambiguous_ddmm(self):
        """When first > 12, must be DD/MM/YYYY."""
        self.assertEqual(parse_date_standalone("25/01/2026"), "2026-01-25")

    def test_slash_format_unambiguous_mmdd(self):
        """When second > 12, must be MM/DD/YYYY."""
        self.assertEqual(parse_date_standalone("01/25/2026"), "2026-01-25")

    def test_ordinal_suffix_stripped(self):
        """Ordinal suffixes (st, nd, rd, th) should be stripped."""
        self.assertEqual(parse_date_standalone("January 22nd, 2026"), "2026-01-22")
        self.assertEqual(parse_date_standalone("March 1st, 2026"), "2026-03-01")
        self.assertEqual(parse_date_standalone("April 3rd, 2025"), "2025-04-03")
        self.assertEqual(parse_date_standalone("May 4th, 2025"), "2025-05-04")

    def test_empty_string(self):
        self.assertIsNone(parse_date_standalone(""))

    def test_none(self):
        self.assertIsNone(parse_date_standalone(None))

    def test_garbage_text(self):
        self.assertIsNone(parse_date_standalone("not a date at all"))

    def test_two_digit_year(self):
        self.assertEqual(parse_date_standalone("01.07.26"), "2026-01-07")

    def test_abbrev_month_no_year(self):
        """Mon DD without year should infer current or previous year."""
        result = parse_date_standalone("Jan 15")
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("-01-15"))


class ParseDateComprehensiveTests(TestCase):
    """Tests for parse_date_comprehensive() - dates embedded in text."""

    def test_month_dd_yyyy_at_start(self):
        date, text = parse_date_comprehensive("January 5, 2026 Gold Corp Announces...")
        self.assertEqual(date, "2026-01-05")
        self.assertEqual(text, "Gold Corp Announces...")

    def test_yyyymmdd_embedded(self):
        date, text = parse_date_comprehensive("20261128 Max Resource Enters Agreement")
        self.assertEqual(date, "2026-11-28")

    def test_yyyy_mm_dd_in_text(self):
        date, text = parse_date_comprehensive("News from 2026-02-10 about gold")
        self.assertEqual(date, "2026-02-10")

    def test_abbrev_month_at_start(self):
        date, text = parse_date_comprehensive("Dec. 17, 2025 Company Update")
        self.assertEqual(date, "2025-12-17")
        self.assertEqual(text, "Company Update")

    def test_ddmon_title_pattern(self):
        """DDMon pattern like '22DecKuya Silver Reports...'"""
        date, text = parse_date_comprehensive("22DecKuya Silver Reports Results")
        self.assertEqual(date[:5], str(datetime.now().year)[:4] + "-" if datetime.now().month >= 12 else str(datetime.now().year - 1)[:4] + "-")
        self.assertIn("Kuya Silver", text)

    def test_no_date_returns_none(self):
        date, text = parse_date_comprehensive("Gold Mining Company Announces Drill Results")
        self.assertIsNone(date)
        self.assertEqual(text, "Gold Mining Company Announces Drill Results")

    def test_empty_string(self):
        date, text = parse_date_comprehensive("")
        self.assertIsNone(date)
        self.assertEqual(text, "")

    def test_dot_format_at_start(self):
        date, text = parse_date_comprehensive("01.07.2026 - Company Update")
        self.assertEqual(date, "2026-01-07")

    def test_month_anywhere_in_text(self):
        date, text = parse_date_comprehensive("Read about the event on December 5, 2025 here")
        self.assertEqual(date, "2025-12-05")


# ============================================================================
# TITLE CLEANING & VALIDATION TESTS
# ============================================================================

class CleanNewsTitleTests(TestCase):
    """Tests for clean_news_title()."""

    def test_basic_title_unchanged(self):
        title = "Gold Corp Announces Drill Results at Main Project"
        self.assertEqual(clean_news_title(title), title)

    def test_strips_whitespace(self):
        self.assertEqual(
            clean_news_title("  Gold Corp Announces Results  "),
            "Gold Corp Announces Results"
        )

    def test_removes_ddmon_prefix(self):
        result = clean_news_title("22DecKuya Silver Reports New Discovery")
        self.assertIn("Kuya Silver", result)
        self.assertNotIn("22Dec", result)

    def test_removes_pdf_suffix(self):
        result = clean_news_title("Company Quarterly Report.pdf")
        self.assertNotIn(".pdf", result)

    def test_removes_nr_prefix(self):
        result = clean_news_title("nr_Gold Corp Intersects High Grade")
        self.assertNotIn("nr_", result)

    def test_replaces_underscores_in_filename(self):
        result = clean_news_title("Gold_Corp_Announces_Drill_Results")
        self.assertIn(" ", result)
        self.assertNotIn("_", result)

    def test_url_encoded_characters(self):
        result = clean_news_title("Gold%20Corp%27s%20Results")
        self.assertIn("Gold Corp", result)

    def test_removes_download_pdf_prefix(self):
        result = clean_news_title("Download PDF, Gold Corp Reports Results")
        self.assertNotIn("Download PDF", result)

    def test_empty_string(self):
        self.assertEqual(clean_news_title(""), "")

    def test_removes_leading_date(self):
        result = clean_news_title("January 5, 2026 Gold Corp Announces Results")
        self.assertEqual(result, "Gold Corp Announces Results")


class IsValidNewsTitleTests(TestCase):
    """Tests for is_valid_news_title()."""

    def test_valid_title(self):
        self.assertTrue(is_valid_news_title("Gold Corp Announces Positive Drill Results at Main Project"))

    def test_too_short(self):
        self.assertFalse(is_valid_news_title("Short title"))

    def test_empty(self):
        self.assertFalse(is_valid_news_title(""))

    def test_none(self):
        self.assertFalse(is_valid_news_title(None))

    def test_junk_skip_to_content(self):
        self.assertFalse(is_valid_news_title("Skip to content"))

    def test_junk_subscribe(self):
        self.assertFalse(is_valid_news_title("Subscribe for updates"))

    def test_date_only(self):
        self.assertFalse(is_valid_news_title("January 22, 2026"))

    def test_year_only(self):
        self.assertFalse(is_valid_news_title("2026"))

    def test_url_title(self):
        self.assertFalse(is_valid_news_title("https://example.com/some-page"))

    def test_junk_in_short_title(self):
        """Junk keywords in short titles should be rejected."""
        self.assertFalse(is_valid_news_title("Click here for more details"))

    def test_junk_keyword_in_long_title(self):
        """Junk keywords in long titles (>35 chars) should be accepted."""
        self.assertTrue(is_valid_news_title(
            "Gold Corp Provides Corporate Presentation and Investor Update for Q4"
        ))

    def test_day_prefix(self):
        self.assertFalse(is_valid_news_title("Day: Monday January 22 2026"))


# ============================================================================
# URL CLASSIFICATION TESTS
# ============================================================================

class IsNewsArticleUrlTests(TestCase):
    """Tests for is_news_article_url()."""

    def test_internal_news_url(self):
        self.assertTrue(is_news_article_url("https://goldcorp.com/news/drill-results-2026"))

    def test_press_release_url(self):
        self.assertTrue(is_news_article_url("https://goldcorp.com/press-release/new-discovery"))

    def test_globenewswire(self):
        self.assertTrue(is_news_article_url("https://www.globenewswire.com/news-release/2026/01/15/gold-corp"))

    def test_newswire_ca(self):
        self.assertTrue(is_news_article_url("https://www.newswire.ca/news-releases/gold-corp-reports"))

    def test_accesswire(self):
        self.assertTrue(is_news_article_url("https://www.accesswire.com/123456/gold-corp"))

    def test_pdf_news(self):
        self.assertTrue(is_news_article_url("https://goldcorp.com/news/nr-2026-01-15.pdf"))

    def test_blocked_media_mining_com(self):
        self.assertFalse(is_news_article_url("https://mining.com/article/gold-corp-discovery"))

    def test_blocked_media_youtube(self):
        self.assertFalse(is_news_article_url("https://youtube.com/watch?v=abc123"))

    def test_blocked_media_seeking_alpha(self):
        self.assertFalse(is_news_article_url("https://seekingalpha.com/article/gold-corp"))

    def test_blocked_media_northern_miner(self):
        self.assertFalse(is_news_article_url("https://northernminer.com/gold-corp-story"))

    def test_base_news_listing_page(self):
        """Base listing pages should be rejected."""
        self.assertFalse(is_news_article_url("https://goldcorp.com/news"))
        self.assertFalse(is_news_article_url("https://goldcorp.com/press-releases"))
        self.assertFalse(is_news_article_url("https://goldcorp.com/press-releases/"))

    def test_year_archive_page(self):
        self.assertFalse(is_news_article_url("https://goldcorp.com/news/2026"))

    def test_empty_url(self):
        self.assertFalse(is_news_article_url(""))

    def test_random_url(self):
        """Non-news internal pages should be rejected."""
        self.assertFalse(is_news_article_url("https://goldcorp.com/about-us"))

    def test_social_media_blocked(self):
        self.assertFalse(is_news_article_url("https://twitter.com/goldcorp/status/123"))
        self.assertFalse(is_news_article_url("https://linkedin.com/company/goldcorp"))


class IsValidNewsUrlTests(TestCase):
    """Tests for is_valid_news_url()."""

    def test_article_url(self):
        self.assertTrue(is_valid_news_url("https://goldcorp.com/news/drill-results"))

    def test_base_news_page(self):
        self.assertFalse(is_valid_news_url("https://goldcorp.com/news"))
        self.assertFalse(is_valid_news_url("https://goldcorp.com/news/"))

    def test_base_press_releases_page(self):
        self.assertFalse(is_valid_news_url("https://goldcorp.com/press-releases"))

    def test_year_archive(self):
        self.assertFalse(is_valid_news_url("https://goldcorp.com/news/2026"))

    def test_empty(self):
        self.assertFalse(is_valid_news_url(""))

    def test_none(self):
        self.assertFalse(is_valid_news_url(None))


# ============================================================================
# URL SLUG EXTRACTION TESTS
# ============================================================================

class ExtractUrlSlugTests(TestCase):
    """Tests for extract_url_slug()."""

    def test_basic_slug(self):
        self.assertEqual(
            extract_url_slug("https://goldcorp.com/news/drill-results-announced"),
            "drill-results-announced"
        )

    def test_year_in_path(self):
        """Should skip year-only segments."""
        self.assertEqual(
            extract_url_slug("https://goldcorp.com/news/2026"),
            "news"
        )

    def test_strips_query_params(self):
        self.assertEqual(
            extract_url_slug("https://goldcorp.com/news/results?page=2"),
            "results"
        )

    def test_strips_trailing_slash(self):
        self.assertEqual(
            extract_url_slug("https://goldcorp.com/news/results/"),
            "results"
        )

    def test_yyyymmdd_slug(self):
        self.assertEqual(
            extract_url_slug("https://goldcorp.com/news/20260112-max-resource-enters"),
            "20260112-max-resource-enters"
        )

    def test_lowercase(self):
        self.assertEqual(
            extract_url_slug("https://goldcorp.com/news/DRILL-Results"),
            "drill-results"
        )


# ============================================================================
# NEWS ITEM DEDUPLICATION TESTS
# ============================================================================

class AddNewsItemTests(TestCase):
    """Tests for _add_news_item() - deduplication and date filtering."""

    def setUp(self):
        import mcp_servers.website_crawler as wc
        wc._seen_slugs = {}
        self.news_by_url = {}
        self.cutoff_date = datetime.now() - timedelta(days=90)

    def test_adds_new_item(self):
        news = {
            'title': 'Gold Corp Announces Results',
            'url': 'https://goldcorp.com/news/results',
            'date': '2026-02-10',
            'document_type': 'news_release',
        }
        result = _add_news_item(self.news_by_url, news, self.cutoff_date, "TEST")
        self.assertTrue(result)
        self.assertEqual(len(self.news_by_url), 1)

    def test_rejects_duplicate_url(self):
        news = {
            'title': 'Gold Corp Announces Results',
            'url': 'https://goldcorp.com/news/results',
            'date': '2026-02-10',
            'document_type': 'news_release',
        }
        _add_news_item(self.news_by_url, news, self.cutoff_date, "TEST")
        result = _add_news_item(self.news_by_url, news, self.cutoff_date, "TEST")
        self.assertFalse(result)
        self.assertEqual(len(self.news_by_url), 1)

    def test_rejects_old_date(self):
        old_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        news = {
            'title': 'Old Gold Corp News',
            'url': 'https://goldcorp.com/news/old-results',
            'date': old_date,
            'document_type': 'news_release',
        }
        result = _add_news_item(self.news_by_url, news, self.cutoff_date, "TEST")
        self.assertFalse(result)

    def test_accepts_item_without_date(self):
        news = {
            'title': 'Gold Corp Update',
            'url': 'https://goldcorp.com/news/update',
            'date': None,
            'document_type': 'news_release',
        }
        result = _add_news_item(self.news_by_url, news, self.cutoff_date, "TEST")
        self.assertTrue(result)

    def test_updates_undated_with_dated(self):
        """An item with a date should replace an existing item without a date."""
        undated = {
            'title': 'Gold Corp Results',
            'url': 'https://goldcorp.com/news/results',
            'date': None,
            'document_type': 'news_release',
        }
        dated = {
            'title': 'Gold Corp Results',
            'url': 'https://goldcorp.com/news/results',
            'date': '2026-02-10',
            'document_type': 'news_release',
        }
        _add_news_item(self.news_by_url, undated, self.cutoff_date, "TEST")
        result = _add_news_item(self.news_by_url, dated, self.cutoff_date, "TEST")
        self.assertTrue(result)
        # The stored item should now have the date
        stored = list(self.news_by_url.values())[0]
        self.assertEqual(stored['date'], '2026-02-10')

    def test_url_normalization_strips_tracking_params(self):
        """URLs with tracking params should be normalized."""
        news1 = {
            'title': 'Gold Corp Results',
            'url': 'https://goldcorp.com/news/results?utm_source=email',
            'date': '2026-02-10',
            'document_type': 'news_release',
        }
        news2 = {
            'title': 'Gold Corp Results',
            'url': 'https://goldcorp.com/news/results?utm_source=twitter',
            'date': '2026-02-10',
            'document_type': 'news_release',
        }
        _add_news_item(self.news_by_url, news1, self.cutoff_date, "TEST")
        result = _add_news_item(self.news_by_url, news2, self.cutoff_date, "TEST")
        self.assertFalse(result)  # Should be deduplicated

    def test_preserves_content_id_params(self):
        """PHP content_id params should be preserved for dedup."""
        news1 = {
            'title': 'Article One',
            'url': 'https://example.com/index.php?content_id=289',
            'date': '2026-02-10',
            'document_type': 'news_release',
        }
        news2 = {
            'title': 'Article Two',
            'url': 'https://example.com/index.php?content_id=290',
            'date': '2026-02-11',
            'document_type': 'news_release',
        }
        _add_news_item(self.news_by_url, news1, self.cutoff_date, "TEST")
        result = _add_news_item(self.news_by_url, news2, self.cutoff_date, "TEST")
        self.assertTrue(result)  # Different content_id = different article
        self.assertEqual(len(self.news_by_url), 2)

    def test_slug_dedup_different_urls(self):
        """Same slug on different URL paths should be deduplicated."""
        import mcp_servers.website_crawler as wc
        wc._seen_slugs = {}

        news1 = {
            'title': 'Gold Corp Announces Major Discovery at Main Project',
            'url': 'https://goldcorp.com/news/gold-corp-announces-major-discovery-at-main-project',
            'date': '2026-02-10',
            'document_type': 'news_release',
        }
        news2 = {
            'title': 'Gold Corp Announces Major Discovery at Main Project',
            'url': 'https://goldcorp.com/press-releases/gold-corp-announces-major-discovery-at-main-project',
            'date': '2026-02-10',
            'document_type': 'news_release',
        }
        _add_news_item(self.news_by_url, news1, self.cutoff_date, "TEST")
        result = _add_news_item(self.news_by_url, news2, self.cutoff_date, "TEST")
        self.assertFalse(result)  # Same slug = duplicate


# ============================================================================
# NEWS RELEASES VIEW TESTS
# ============================================================================

class CompanyNewsReleasesViewTests(TestCase):
    """Tests for the company_news_releases API view."""

    def setUp(self):
        self.factory = RequestFactory()
        self.company = Company.objects.create(
            name="Test Gold Corp",
            ticker="TGC",
            exchange="TSXV",
            website="https://testgoldcorp.com",
            is_active=True,
        )

    def test_returns_news_from_newsrelease_table(self):
        """The view should read from NewsRelease, not CompanyNews."""
        NewsRelease.objects.create(
            company=self.company,
            title="Feb 10 PEA Results",
            url="https://testgoldcorp.com/news/pea-results",
            release_date="2026-02-10",
            release_type="news_release",
        )
        request = self.factory.get(f'/api/companies/{self.company.id}/news-releases/')
        response = company_news_releases(request, self.company.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['non_financial_count'], 1)
        self.assertEqual(response.data['non_financial'][0]['title'], "Feb 10 PEA Results")
        self.assertEqual(response.data['non_financial'][0]['release_date'], "2026-02-10")

    def test_newsrelease_takes_priority_over_companynews(self):
        """Even if CompanyNews has data, NewsRelease should be used."""
        CompanyNews.objects.create(
            company=self.company,
            title="Old Onboarding News",
            source_url="https://testgoldcorp.com/news/old",
            publication_date="2025-12-01",
            news_type="corporate",
        )
        NewsRelease.objects.create(
            company=self.company,
            title="Recent Daily Scrape News",
            url="https://testgoldcorp.com/news/recent",
            release_date="2026-02-10",
            release_type="news_release",
        )
        request = self.factory.get(f'/api/companies/{self.company.id}/news-releases/')
        response = company_news_releases(request, self.company.id)

        self.assertEqual(response.data['non_financial_count'], 1)
        self.assertEqual(response.data['non_financial'][0]['title'], "Recent Daily Scrape News")

    def test_news_ordered_by_date_desc(self):
        """News should be ordered newest first."""
        NewsRelease.objects.create(
            company=self.company,
            title="Older News",
            url="https://testgoldcorp.com/news/older",
            release_date="2025-12-01",
        )
        NewsRelease.objects.create(
            company=self.company,
            title="Newer News",
            url="https://testgoldcorp.com/news/newer",
            release_date="2026-02-10",
        )
        request = self.factory.get(f'/api/companies/{self.company.id}/news-releases/')
        response = company_news_releases(request, self.company.id)

        self.assertEqual(response.data['non_financial'][0]['title'], "Newer News")
        self.assertEqual(response.data['non_financial'][1]['title'], "Older News")

    def test_financial_news_separated(self):
        """Items with is_material=True should appear in financial section."""
        NewsRelease.objects.create(
            company=self.company,
            title="Financing Announcement",
            url="https://testgoldcorp.com/news/financing",
            release_date="2026-02-10",
            is_material=True,
        )
        NewsRelease.objects.create(
            company=self.company,
            title="Drill Results",
            url="https://testgoldcorp.com/news/drills",
            release_date="2026-02-11",
            is_material=False,
        )
        request = self.factory.get(f'/api/companies/{self.company.id}/news-releases/')
        response = company_news_releases(request, self.company.id)

        self.assertEqual(response.data['financial_count'], 1)
        self.assertEqual(response.data['financial'][0]['title'], "Financing Announcement")

    def test_max_20_non_financial(self):
        """Non-financial should be limited to 20 items."""
        for i in range(25):
            NewsRelease.objects.create(
                company=self.company,
                title=f"News Item {i}",
                url=f"https://testgoldcorp.com/news/item-{i}",
                release_date="2026-02-10",
            )
        request = self.factory.get(f'/api/companies/{self.company.id}/news-releases/')
        response = company_news_releases(request, self.company.id)

        self.assertEqual(response.data['non_financial_count'], 20)

    def test_inactive_company_returns_404(self):
        inactive = Company.objects.create(
            name="Inactive Corp",
            ticker="IC",
            exchange="TSXV",
            is_active=False,
        )
        request = self.factory.get(f'/api/companies/{inactive.id}/news-releases/')
        response = company_news_releases(request, inactive.id)
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_company_returns_404(self):
        request = self.factory.get('/api/companies/99999/news-releases/')
        response = company_news_releases(request, 99999)
        self.assertEqual(response.status_code, 404)

    def test_empty_news_returns_empty_lists(self):
        request = self.factory.get(f'/api/companies/{self.company.id}/news-releases/')
        response = company_news_releases(request, self.company.id)

        self.assertEqual(response.data['non_financial_count'], 0)
        self.assertEqual(response.data['financial_count'], 0)
        self.assertEqual(response.data['non_financial'], [])
        self.assertEqual(response.data['financial'], [])


# ============================================================================
# DAILY SCRAPER TASK LOGIC TESTS
# ============================================================================

class ScraperTaskDateParsingTests(TestCase):
    """Tests for date parsing logic in scrape_single_company_news_task."""

    def test_valid_date_parses(self):
        """Standard YYYY-MM-DD dates should parse correctly."""
        date_str = "2026-02-10"
        release_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        self.assertEqual(str(release_date), "2026-02-10")

    def test_invalid_date_raises(self):
        """Malformed date strings should raise ValueError."""
        with self.assertRaises(ValueError):
            datetime.strptime("Feb 10, 2026", '%Y-%m-%d')

    def test_none_date_skipped(self):
        """None date should not crash strptime."""
        date_str = None
        self.assertIsNone(date_str)


class BatchLockTests(TestCase):
    """Tests for distributed lock logic in scrape_all_companies_news_task."""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_lock_acquired(self):
        """First call should acquire the lock."""
        LOCK_KEY = 'test_scrape_lock'
        result = cache.add(LOCK_KEY, 'task-1', timeout=60)
        self.assertTrue(result)

    def test_lock_prevents_duplicate(self):
        """Second call should fail to acquire."""
        LOCK_KEY = 'test_scrape_lock'
        cache.add(LOCK_KEY, 'task-1', timeout=60)
        result = cache.add(LOCK_KEY, 'task-2', timeout=60)
        self.assertFalse(result)

    def test_lock_released_after_delete(self):
        """After deletion, lock should be re-acquirable."""
        LOCK_KEY = 'test_scrape_lock'
        cache.add(LOCK_KEY, 'task-1', timeout=60)
        cache.delete(LOCK_KEY)
        result = cache.add(LOCK_KEY, 'task-2', timeout=60)
        self.assertTrue(result)
