"""
Test News Release Crawler
Discovers and stores news releases from company websites (last 6 months only)
"""

import asyncio
from mcp_servers.website_crawler import crawl_news_releases
from mcp_servers.news_release_storage import store_news_releases


async def test_news_release_crawler():
    """Test crawling news releases for a mining company"""

    print("="*80)
    print("TESTING NEWS RELEASE CRAWLER")
    print("="*80)

    # Test with 1911 Gold website
    url = "https://www.1911gold.com"
    company_name = "1911 Gold Corp"  # Must match database company name
    months = 6

    print(f"\nCrawling: {url}")
    print(f"Company: {company_name}")
    print(f"Looking for: News releases from the last {months} months")
    print(f"Max depth: 2 (homepage + one level deep)")
    print("\nThis may take 30-60 seconds...\n")

    # Crawl for news releases
    news_releases = await crawl_news_releases(url, months=months, max_depth=2)

    print("\n" + "="*80)
    print(f"DISCOVERED {len(news_releases)} NEWS RELEASES")
    print("="*80)

    if news_releases:
        # Display discovered news releases
        print(f"\nNEWS RELEASES (Last {months} months):")
        print("-" * 80)

        for i, news in enumerate(news_releases[:10], 1):  # Show first 10
            date = news.get('date', 'Unknown date')
            title = news.get('title', 'No title')
            url = news.get('url', '')

            print(f"\n{i}. [{date}] {title[:70]}")
            print(f"   URL: {url}")
            print(f"   Relevance: {news.get('relevance_score', 0)}")

        if len(news_releases) > 10:
            print(f"\n... and {len(news_releases) - 10} more")

        # Ask if user wants to store in database
        print("\n" + "="*80)
        print("DATABASE STORAGE")
        print("="*80)

        try:
            response = input(f"\nStore these {len(news_releases)} news releases in the database? (y/n): ").strip().lower()
        except EOFError:
            # Running in automated mode (no interactive input)
            response = 'n'
            print(f"\n[INFO] Running in automated mode - skipping database storage")
            print(f"       To store, run this script interactively and answer 'y'")

        if response == 'y':
            print(f"\n[INFO] Storing news releases for {company_name}...")

            # Store in database
            stats = store_news_releases(
                company_name=company_name,
                news_releases=news_releases,
                overwrite_duplicates=False  # Skip duplicates by default
            )

            print("\n" + "="*80)
            print("STORAGE RESULTS")
            print("="*80)
            print(f"Created: {stats['created']}")
            print(f"Updated: {stats['updated']}")
            print(f"Skipped: {stats['skipped']}")

            if stats['errors']:
                print(f"\nErrors ({len(stats['errors'])}):")
                for error in stats['errors'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
                if len(stats['errors']) > 5:
                    print(f"  ... and {len(stats['errors']) - 5} more errors")

            if stats['created'] > 0:
                print(f"\n[OK] Successfully stored {stats['created']} new news release(s)!")
                print("     They are now available in the admin interface and chatbot.")
        else:
            print("\n[OK] News releases not stored.")

    else:
        print("\n[!] No news releases found from the last 6 months")
        print("    This could mean:")
        print("    - The company hasn't published news releases recently")
        print("    - The news releases are not in PDF format")
        print("    - The crawler couldn't find the news section")
        print("\n    Try:")
        print("    - Increasing max_depth to 3")
        print("    - Increasing the months parameter to 12")
        print("    - Checking the company website structure")

    print("\n" + "="*80)
    print("CRAWLER TEST COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Check admin interface: http://localhost:8000/admin/core/newsrelease/")
    print("2. Run crawler for other companies")
    print("3. Schedule automatic daily/weekly crawls")
    print("\nFor more info, see: CRAWL4AI_INTEGRATION.md")

    return news_releases


if __name__ == "__main__":
    asyncio.run(test_news_release_crawler())
