"""
Test the crawler directly to see what news releases it finds
"""

import asyncio
import sys
from mcp_servers.website_crawler import crawl_news_releases

async def test_crawler():
    print("=" * 80)
    print("Testing Direct Crawler for 1911 Gold")
    print("=" * 80)

    url = "https://www.1911gold.com"
    print(f"\nCrawling: {url}")
    print("Looking for news from last 6 months...")
    print("Max depth: 2")
    print("\nThis may take 30-60 seconds...\n")

    try:
        news_releases = await crawl_news_releases(
            url=url,
            months=6,
            max_depth=2
        )

        print(f"\nFound {len(news_releases)} news releases:")
        print("=" * 80)

        # Sort by date descending
        news_releases.sort(key=lambda x: x.get('date', ''), reverse=True)

        for i, release in enumerate(news_releases[:10], 1):  # Show first 10
            date = release.get('date', 'No date')
            title = release.get('title', 'No title')
            url = release.get('url', 'No URL')

            print(f"\n{i}. [{date}] {title}")
            print(f"   URL: {url}")

        if len(news_releases) > 10:
            print(f"\n... and {len(news_releases) - 10} more")

        print("\n" + "=" * 80)
        print("Crawler test complete!")
        print("=" * 80)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_crawler())
