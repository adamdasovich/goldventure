"""
News Release Storage
Handles storing crawled news releases into the database
"""

import os
import django
from datetime import datetime
from typing import List, Dict
from asgiref.sync import sync_to_async

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import NewsRelease, Company
from django.db import transaction


def store_news_releases(company_name: str, news_releases: List[Dict], overwrite_duplicates: bool = False) -> Dict:
    """
    Store discovered news releases in the database

    Args:
        company_name: Name of the company
        news_releases: List of news release dictionaries from crawler
        overwrite_duplicates: If True, update existing news releases. If False, skip duplicates.

    Returns:
        Dictionary with statistics: created, updated, skipped
    """
    stats = {
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': []
    }

    # Get or create company
    try:
        company = Company.objects.get(name=company_name)
    except Company.DoesNotExist:
        stats['errors'].append(f"Company '{company_name}' not found in database")
        return stats

    for news_item in news_releases:
        try:
            url = news_item['url']
            title = news_item['title']
            date_str = news_item.get('date')

            # Parse date
            if date_str:
                try:
                    release_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    # If date parsing fails, skip this news release
                    stats['errors'].append(f"Invalid date format for {title}: {date_str}")
                    stats['skipped'] += 1
                    continue
            else:
                # No date available, skip
                stats['errors'].append(f"No date available for {title}")
                stats['skipped'] += 1
                continue

            # Check if news release already exists (by URL or title+date)
            existing = NewsRelease.objects.filter(
                company=company,
                url=url
            ).first()

            if not existing:
                # Check by title and date as well
                existing = NewsRelease.objects.filter(
                    company=company,
                    title=title,
                    release_date=release_date
                ).first()

            if existing:
                if overwrite_duplicates:
                    # Update existing
                    existing.title = title
                    existing.url = url
                    existing.release_date = release_date
                    existing.save()
                    stats['updated'] += 1
                else:
                    # Skip duplicate
                    stats['skipped'] += 1
            else:
                # Create new news release
                NewsRelease.objects.create(
                    company=company,
                    title=title,
                    url=url,
                    release_date=release_date,
                    release_type='other',  # Default type, can be classified later
                    summary='',  # To be filled later
                    full_text='',  # To be extracted later
                    is_material=False  # To be determined later
                )
                stats['created'] += 1

        except Exception as e:
            stats['errors'].append(f"Error processing {news_item.get('title', 'Unknown')}: {str(e)}")

    return stats


def store_news_releases_bulk(company_news_map: Dict[str, List[Dict]]) -> Dict:
    """
    Store news releases for multiple companies at once

    Args:
        company_news_map: Dictionary mapping company names to lists of news releases

    Returns:
        Dictionary with statistics per company
    """
    results = {}

    for company_name, news_releases in company_news_map.items():
        results[company_name] = store_news_releases(company_name, news_releases)

    return results


def get_existing_news_releases(company_name: str, months: int = 6) -> List[Dict]:
    """
    Get existing news releases from database for a company

    Args:
        company_name: Name of the company
        months: Number of months to look back

    Returns:
        List of news release dictionaries
    """
    try:
        company = Company.objects.get(name=company_name)
    except Company.DoesNotExist:
        return []

    from datetime import timedelta
    cutoff_date = datetime.now().date() - timedelta(days=months * 30)

    news_releases = NewsRelease.objects.filter(
        company=company,
        release_date__gte=cutoff_date
    ).order_by('-release_date')

    return [
        {
            'id': nr.id,
            'title': nr.title,
            'url': nr.url,
            'date': nr.release_date.isoformat(),
            'release_type': nr.release_type,
            'is_material': nr.is_material,
            'summary': nr.summary,
        }
        for nr in news_releases
    ]
