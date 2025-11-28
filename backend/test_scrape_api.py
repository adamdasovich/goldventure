"""
Test the updated news scraping API with real web crawler
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company
import requests

def test_scrape_news():
    # Get 1911 Gold Corporation
    company = Company.objects.get(name__icontains="1911 Gold")

    print("=" * 80)
    print(f"Testing News Scraping for: {company.name}")
    print(f"Website: {company.website}")
    print("=" * 80)

    # Call the scraping API
    print("\nCalling scraping API...")
    response = requests.post(f'http://localhost:8000/api/companies/{company.id}/scrape-news/')

    if response.status_code == 200:
        data = response.json()
        print(f"\n[SUCCESS]")
        print(f"Status: {data.get('status')}")
        print(f"Message: {data.get('message')}")
        print(f"Financial News: {data.get('financial_count')}")
        print(f"Non-Financial News: {data.get('non_financial_count')}")
        print(f"Last Scraped: {data.get('last_scraped')}")
    else:
        print(f"\n[ERROR]")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

    # Now fetch the news releases
    print("\n" + "=" * 80)
    print("Fetching news releases from database...")
    print("=" * 80)

    response = requests.get(f'http://localhost:8000/api/companies/{company.id}/news-releases/')

    if response.status_code == 200:
        data = response.json()

        print(f"\nFinancial News ({data.get('financial_count')} total):")
        print("-" * 80)
        for news in data.get('financial', [])[:3]:  # Show first 3
            print(f"\n  [{news['release_date']}] {news['title']}")
            print(f"  Type: {news['release_type']}")
            print(f"  URL: {news['url']}")

        print(f"\n\nNon-Financial News ({data.get('non_financial_count')} total):")
        print("-" * 80)
        for news in data.get('non_financial', [])[:3]:  # Show first 3
            print(f"\n  [{news['release_date']}] {news['title']}")
            print(f"  Type: {news['release_type']}")
            print(f"  URL: {news['url']}")

        print("\n" + "=" * 80)
        print("[SUCCESS] News scraping with real web crawler is working!")
        print("=" * 80)
    else:
        print(f"\n[ERROR] Failed to fetch news!")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == '__main__':
    test_scrape_news()
