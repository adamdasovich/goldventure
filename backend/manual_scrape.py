"""
Manual News Scraper - Interactive
Quickly scrape a company website for news releases and store them
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import asyncio
from asgiref.sync import sync_to_async
from core.models import Company
from mcp_servers.website_crawler import crawl_news_releases
from mcp_servers.news_release_storage import store_news_releases


async def manual_scrape():
    """Interactive manual scraping"""

    print("="*80)
    print("MANUAL NEWS SCRAPER")
    print("="*80)

    # Get all companies
    companies = await sync_to_async(list)(Company.objects.filter(website__isnull=False))

    if not companies:
        print("\nNo companies found in database!")
        return

    # Show companies
    print(f"\nFound {len(companies)} companies:\n")
    for i, company in enumerate(companies, 1):
        print(f"{i}. {company.name} - {company.website}")

    # Get user choice
    print("\nOptions:")
    print("  Enter number (1-{}) to scrape specific company".format(len(companies)))
    print("  Enter 'all' to scrape all companies")
    print("  Enter 'url' to scrape any URL manually")
    print("  Enter 'q' to quit")

    choice = input("\nYour choice: ").strip().lower()

    if choice == 'q':
        print("Cancelled.")
        return

    # Get scraping parameters
    try:
        months_input = input("How many months back? (default 6): ").strip()
        months = int(months_input) if months_input else 6
    except ValueError:
        months = 6

    try:
        depth_input = input("Crawl depth? (default 2): ").strip()
        depth = int(depth_input) if depth_input else 2
    except ValueError:
        depth = 2

    print(f"\nSettings: {months} months back, depth {depth}\n")

    # Process based on choice
    if choice == 'all':
        # Scrape all companies
        print(f"Scraping all {len(companies)} companies...\n")
        await scrape_companies(companies, months, depth)

    elif choice == 'url':
        # Manual URL entry
        url = input("\nEnter website URL: ").strip()
        company_name = input("Enter company name (must match database): ").strip()

        if url and company_name:
            print(f"\nScraping {url}...\n")
            await scrape_url(url, company_name, months, depth)
        else:
            print("Error: URL and company name required")

    else:
        # Specific company by number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(companies):
                company = companies[idx]
                print(f"\nScraping {company.name}...\n")
                await scrape_companies([company], months, depth)
            else:
                print("Invalid number")
        except ValueError:
            print("Invalid choice")


async def scrape_companies(companies, months, depth):
    """Scrape multiple companies"""

    total_created = 0
    total_skipped = 0

    for company in companies:
        print("="*80)
        print(f"Company: {company.name}")
        print(f"Website: {company.website}")
        print("="*80)

        try:
            # Crawl
            news_releases = await crawl_news_releases(
                url=company.website,
                months=months,
                max_depth=depth
            )

            print(f"\nFound {len(news_releases)} news releases")

            if news_releases:
                # Show preview
                print("\nPreview (latest 3):")
                for i, news in enumerate(news_releases[:3], 1):
                    date = news.get('date', 'No date')
                    title = news.get('title', 'No title')[:60]
                    print(f"  {i}. [{date}] {title}")

                # Store
                print("\nStoring in database...")
                store_async = sync_to_async(store_news_releases)
                stats = await store_async(company.name, news_releases, overwrite_duplicates=False)

                created = stats['created']
                skipped = stats['skipped']

                total_created += created
                total_skipped += skipped

                print(f"✓ Created: {created}")
                print(f"⊘ Skipped: {skipped}")

                if stats['errors']:
                    print(f"✗ Errors: {len(stats['errors'])}")
                    for error in stats['errors'][:2]:
                        print(f"  - {error}")
            else:
                print("No news releases found")

        except Exception as e:
            print(f"Error: {str(e)}")

        print()

    # Summary
    print("="*80)
    print("SCRAPING COMPLETE")
    print("="*80)
    print(f"Companies scraped: {len(companies)}")
    print(f"Total created: {total_created}")
    print(f"Total skipped: {total_skipped}")


async def scrape_url(url, company_name, months, depth):
    """Scrape a single URL"""

    try:
        # Crawl
        news_releases = await crawl_news_releases(
            url=url,
            months=months,
            max_depth=depth
        )

        print(f"\nFound {len(news_releases)} news releases")

        if news_releases:
            # Show preview
            print("\nPreview (all):")
            for i, news in enumerate(news_releases, 1):
                date = news.get('date', 'No date')
                title = news.get('title', 'No title')[:60]
                print(f"  {i}. [{date}] {title}")

            # Store
            print("\nStoring in database...")
            store_async = sync_to_async(store_news_releases)
            stats = await store_async(company_name, news_releases, overwrite_duplicates=False)

            print(f"\n✓ Created: {stats['created']}")
            print(f"⊘ Skipped: {stats['skipped']}")

            if stats['errors']:
                print(f"✗ Errors: {len(stats['errors'])}")
                for error in stats['errors']:
                    print(f"  - {error}")
        else:
            print("No news releases found")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(manual_scrape())
