"""
Crawl and Store News Releases - Automated
Discovers news releases and stores them in the database automatically
"""

import asyncio
from asgiref.sync import sync_to_async
from mcp_servers.website_crawler import crawl_news_releases
from mcp_servers.news_release_storage import store_news_releases


async def crawl_and_store():
    """Crawl 1911 Gold and store news releases in database"""

    print("="*80)
    print("CRAWLING AND STORING NEWS RELEASES")
    print("="*80)

    company_name = "1911 Gold Corporation"  # Must match exact name in database
    url = "https://www.1911gold.com"

    print(f"\nCompany: {company_name}")
    print(f"URL: {url}")
    print(f"Looking for: News releases from last 6 months\n")

    # Crawl for news releases
    print("Crawling website...")
    news_releases = await crawl_news_releases(url, months=6, max_depth=2)

    print(f"\nFound {len(news_releases)} news releases")

    if news_releases:
        # Show first 5
        print("\nPreview (first 5):")
        for i, news in enumerate(news_releases[:5], 1):
            print(f"  {i}. [{news.get('date', 'No date')}] {news.get('title', 'No title')[:60]}")

        # Store in database (use sync_to_async to call Django ORM from async context)
        print(f"\nStoring in database...")
        store_async = sync_to_async(store_news_releases)
        stats = await store_async(company_name, news_releases, overwrite_duplicates=False)

        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"✓ Created: {stats['created']}")
        print(f"↻ Updated: {stats['updated']}")
        print(f"⊘ Skipped (duplicates): {stats['skipped']}")

        if stats['errors']:
            print(f"\n⚠ Errors ({len(stats['errors'])}):")
            for error in stats['errors'][:3]:
                print(f"  - {error}")

        print(f"\n[OK] Done! Check admin interface to view news releases.")
    else:
        print("\n[!] No news releases found")


if __name__ == "__main__":
    asyncio.run(crawl_and_store())
