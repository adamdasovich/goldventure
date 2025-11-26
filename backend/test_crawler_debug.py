"""
Debug News Crawler - See what's actually being extracted
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import asyncio
from mcp_servers.website_crawler import crawl_news_releases


async def test_crawl():
    """Test crawler and show what's extracted"""

    url = "https://www.1911gold.com"

    print("="*80)
    print("DEBUGGING NEWS CRAWLER")
    print("="*80)
    print(f"\nCrawling: {url}")
    print(f"Looking for news from last 6 months\n")

    news_releases = await crawl_news_releases(
        url=url,
        months=6,
        max_depth=2
    )

    print(f"\nFound {len(news_releases)} news releases")
    print("="*80)

    if news_releases:
        print("\nFirst 5 news releases (FULL DETAILS):")
        print("-"*80)

        for i, news in enumerate(news_releases[:5], 1):
            print(f"\n{i}. TITLE: {news.get('title', 'NO TITLE')}")
            print(f"   DATE: {news.get('date', 'NO DATE')}")
            print(f"   URL: {news.get('url', 'NO URL')}")
            print(f"   TYPE: {news.get('document_type', 'NO TYPE')}")
            print(f"   SCORE: {news.get('relevance_score', 0)}")
    else:
        print("No news releases found")


if __name__ == "__main__":
    asyncio.run(test_crawl())
