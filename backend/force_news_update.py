"""
Force update news releases for 1911 Gold (bypassing cache)
"""

import os
import django
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company, NewsRelease
from mcp_servers.website_crawler import crawl_news_releases
from datetime import datetime

def force_update():
    # Get 1911 Gold
    company = Company.objects.get(name__icontains="1911 Gold")

    print("=" * 80)
    print(f"Force Updating News for: {company.name}")
    print(f"Website: {company.website}")
    print("=" * 80)

    # Crawl
    print("\nCrawling website (this may take 30-60 seconds)...")
    news_releases = asyncio.run(crawl_news_releases(
        url=company.website,
        months=6,
        max_depth=2
    ))

    print(f"\nFound {len(news_releases)} news releases from crawler")

    # Save to database
    financial_count = 0
    non_financial_count = 0
    created_count = 0
    updated_count = 0

    for release_data in news_releases:
        title = release_data.get('title', '')
        url = release_data.get('url', '')
        date_str = release_data.get('date')

        # Classify
        title_lower = title.lower()
        is_financial = any(keyword in title_lower for keyword in ['financial', 'financials', 'financing'])

        # Determine release type
        if is_financial:
            release_type = 'financing' if 'financing' in title_lower or 'placement' in title_lower else 'corporate'
            financial_count += 1
        else:
            non_financial_count += 1
            if 'drill' in title_lower or 'assay' in title_lower:
                release_type = 'drill_results'
            elif 'resource' in title_lower:
                release_type = 'resource_update'
            elif 'acquisition' in title_lower or 'disposition' in title_lower:
                release_type = 'acquisition'
            elif 'management' in title_lower or 'appoint' in title_lower:
                release_type = 'management'
            else:
                release_type = 'other'

        # Parse date
        if date_str:
            try:
                release_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                release_date = None
        else:
            release_date = None

        if not url or not release_date:
            continue

        # Create or update
        obj, created = NewsRelease.objects.update_or_create(
            company=company,
            url=url,
            defaults={
                'title': title,
                'release_type': release_type,
                'release_date': release_date,
                'summary': '',
                'is_material': is_financial,
                'full_text': ''
            }
        )

        if created:
            created_count += 1
        else:
            updated_count += 1

    print("\n" + "=" * 80)
    print("DATABASE UPDATE COMPLETE")
    print("=" * 80)
    print(f"Created: {created_count}")
    print(f"Updated: {updated_count}")
    print(f"Financial: {financial_count}")
    print(f"Non-Financial: {non_financial_count}")

    # Show latest 5
    print("\n" + "=" * 80)
    print("LATEST 5 NEWS RELEASES IN DATABASE:")
    print("=" * 80)

    latest = NewsRelease.objects.filter(company=company).order_by('-release_date')[:5]
    for news in latest:
        category = "Financial" if news.is_material else "Non-Financial"
        print(f"\n[{news.release_date}] {category}")
        print(f"  {news.title}")
        print(f"  {news.url}")

if __name__ == '__main__':
    force_update()
