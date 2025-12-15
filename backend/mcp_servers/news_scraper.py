"""
News Article Scraper for Mining Industry News Sources
Uses Crawl4AI to scrape articles from configured news sources like The Northern Miner, Mining.com, etc.
"""

import asyncio
import re
import sys
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from bs4 import BeautifulSoup

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class MiningNewsScraper:
    """
    Scraper for mining industry news websites.
    Extracts article titles, URLs, publication dates, and summaries.
    """

    # Site-specific configurations
    SITE_CONFIGS = {
        'northernminer.com': {
            'article_selectors': ['article', '.post', '.news-item', '.article-card'],
            'title_selectors': ['h2 a', 'h3 a', '.entry-title a', '.post-title a'],
            'date_selectors': ['.date', '.post-date', 'time', '.entry-date', '.published'],
            'summary_selectors': ['.excerpt', '.summary', '.entry-excerpt', 'p'],
        },
        'mining.com': {
            'article_selectors': ['article', '.post', '.news-item', '.story'],
            'title_selectors': ['h2 a', 'h3 a', '.entry-title a', '.story-title a'],
            'date_selectors': ['.date', '.post-date', 'time', '.entry-date'],
            'summary_selectors': ['.excerpt', '.summary', '.teaser', 'p'],
        },
        'default': {
            'article_selectors': ['article', '.post', '.news-item', '.article', '.story', '.entry'],
            'title_selectors': ['h2 a', 'h3 a', 'h4 a', '.title a', '.entry-title a'],
            'date_selectors': ['.date', 'time', '.published', '.post-date', '.entry-date'],
            'summary_selectors': ['.excerpt', '.summary', '.description', 'p'],
        }
    }

    def __init__(self):
        self.articles = []

    def _get_site_config(self, url: str) -> Dict:
        """Get site-specific configuration or default"""
        domain = urlparse(url).netloc.lower()
        for key in self.SITE_CONFIGS:
            if key in domain:
                return self.SITE_CONFIGS[key]
        return self.SITE_CONFIGS['default']

    async def scrape_source(
        self,
        source_url: str,
        source_name: str,
        custom_selector: str = None,
        max_articles: int = 50
    ) -> List[Dict]:
        """
        Scrape articles from a single news source.

        Args:
            source_url: Base URL of the news source
            source_name: Display name of the source
            custom_selector: Custom CSS selector for articles (optional)
            max_articles: Maximum number of articles to scrape

        Returns:
            List of article dictionaries
        """
        self.articles = []
        config = self._get_site_config(source_url)

        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )

        crawler_config = CrawlerRunConfig(
            cache_mode="bypass",
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Try common news listing pages
            pages_to_try = [
                source_url,
                urljoin(source_url, '/news'),
                urljoin(source_url, '/latest'),
                urljoin(source_url, '/articles'),
                urljoin(source_url, '/category/news'),
            ]

            for page_url in pages_to_try:
                try:
                    result = await crawler.arun(url=page_url, config=crawler_config)
                    if not result.success:
                        continue

                    soup = BeautifulSoup(result.html, 'html.parser')

                    # Use custom selector if provided, otherwise try configured selectors
                    if custom_selector:
                        article_containers = soup.select(custom_selector)
                    else:
                        article_containers = []
                        for selector in config['article_selectors']:
                            article_containers.extend(soup.select(selector))

                    print(f"[{source_name}] Found {len(article_containers)} potential articles on {page_url}")

                    for container in article_containers[:max_articles]:
                        article = self._extract_article(container, page_url, source_name, config)
                        if article and article.get('title') and article.get('url'):
                            # Avoid duplicates
                            if not any(a['url'] == article['url'] for a in self.articles):
                                self.articles.append(article)
                                try:
                                    print(f"  [+] {article['title'][:60]}...")
                                except UnicodeEncodeError:
                                    print(f"  [+] Found article")

                    # If we found articles, don't try other pages
                    if self.articles:
                        break

                except Exception as e:
                    print(f"[{source_name}] Error scraping {page_url}: {str(e)}")
                    continue

        return self.articles

    def _extract_article(
        self,
        container,
        base_url: str,
        source_name: str,
        config: Dict
    ) -> Optional[Dict]:
        """Extract article data from a container element"""

        article = {
            'source_name': source_name,
        }

        # Extract title and URL
        title_elem = None
        for selector in config['title_selectors']:
            title_elem = container.select_one(selector)
            if title_elem:
                break

        # If no title found with selectors, try finding any link with substantial text
        if not title_elem:
            links = container.find_all('a', href=True)
            for link in links:
                link_text = link.get_text(strip=True)
                if len(link_text) > 20:
                    title_elem = link
                    break

        if title_elem:
            article['title'] = title_elem.get_text(strip=True)
            href = title_elem.get('href', '')
            if href:
                article['url'] = urljoin(base_url, href)
        else:
            return None

        # Extract publication date
        date_str = None
        for selector in config['date_selectors']:
            date_elem = container.select_one(selector)
            if date_elem:
                # Check for datetime attribute first
                if date_elem.has_attr('datetime'):
                    date_str = date_elem['datetime']
                else:
                    date_str = date_elem.get_text(strip=True)
                break

        if date_str:
            article['published_at'] = self._parse_date(date_str)
        else:
            article['published_at'] = None

        # Extract summary/excerpt
        for selector in config['summary_selectors']:
            summary_elem = container.select_one(selector)
            if summary_elem:
                summary_text = summary_elem.get_text(strip=True)
                # Make sure it's not just the title repeated
                if summary_text and summary_text != article.get('title', ''):
                    article['summary'] = summary_text[:500]  # Limit length
                    break

        if 'summary' not in article:
            article['summary'] = ''

        # Extract image URL if available
        img_elem = container.find('img')
        if img_elem and img_elem.get('src'):
            article['image_url'] = urljoin(base_url, img_elem['src'])
        else:
            article['image_url'] = ''

        return article

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats and return ISO format"""
        if not date_str:
            return None

        # Try ISO format first
        iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
        if iso_match:
            return f"{iso_match.group(1)}-{iso_match.group(2)}-{iso_match.group(3)}"

        # Try "Month Day, Year" format
        month_day_year = re.search(
            r'(January|February|March|April|May|June|July|August|September|October|November|December|'
            r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.\s]+(\d{1,2})[,\s]+(\d{4})',
            date_str,
            re.IGNORECASE
        )
        if month_day_year:
            month_name = month_day_year.group(1).lower()[:3]
            day = month_day_year.group(2).zfill(2)
            year = month_day_year.group(3)

            month_map = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            month = month_map.get(month_name, '01')
            return f"{year}-{month}-{day}"

        # Try "Day Month Year" format
        day_month_year = re.search(
            r'(\d{1,2})[.\s]+(January|February|March|April|May|June|July|August|September|October|November|December|'
            r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.\s]+(\d{4})',
            date_str,
            re.IGNORECASE
        )
        if day_month_year:
            day = day_month_year.group(1).zfill(2)
            month_name = day_month_year.group(2).lower()[:3]
            year = day_month_year.group(3)

            month_map = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            month = month_map.get(month_name, '01')
            return f"{year}-{month}-{day}"

        # Try numeric formats MM/DD/YYYY or DD/MM/YYYY
        numeric_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', date_str)
        if numeric_match:
            # Assume MM/DD/YYYY for US-based sites
            month = numeric_match.group(1).zfill(2)
            day = numeric_match.group(2).zfill(2)
            year = numeric_match.group(3)
            return f"{year}-{month}-{day}"

        return None


async def scrape_all_sources(sources: List[Dict]) -> Dict:
    """
    Scrape all configured news sources.

    Args:
        sources: List of source dictionaries with 'name', 'url', and optional 'selector'

    Returns:
        Dictionary with results including articles and statistics
    """
    scraper = MiningNewsScraper()
    all_articles = []
    errors = []
    sources_processed = 0

    for source in sources:
        if not source.get('is_active', True):
            continue

        try:
            print(f"\n{'='*60}")
            print(f"Scraping: {source['name']} ({source['url']})")
            print(f"{'='*60}")

            articles = await scraper.scrape_source(
                source_url=source['url'],
                source_name=source['name'],
                custom_selector=source.get('scrape_selector', None)
            )

            all_articles.extend(articles)
            sources_processed += 1

            print(f"[{source['name']}] Found {len(articles)} articles")

        except Exception as e:
            error_msg = f"Failed to scrape {source['name']}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            errors.append(error_msg)

    return {
        'articles': all_articles,
        'sources_processed': sources_processed,
        'articles_found': len(all_articles),
        'errors': errors
    }


async def run_scrape_job(job_id: int = None):
    """
    Run a complete scrape job using configured sources from the database.

    Args:
        job_id: Optional job ID to update with progress

    Returns:
        Dictionary with job results
    """
    import os
    import sys
    import django

    # Set up Django
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    from core.models import NewsSource, NewsArticle, NewsScrapeJob
    from django.utils import timezone

    # Get or create job
    if job_id:
        job = NewsScrapeJob.objects.get(id=job_id)
    else:
        job = NewsScrapeJob.objects.create(status='pending', is_scheduled=True)

    # Mark job as running
    job.status = 'running'
    job.started_at = timezone.now()
    job.save()

    try:
        # Get active sources
        sources = list(NewsSource.objects.filter(is_active=True).values('id', 'name', 'url', 'scrape_selector', 'is_active'))

        if not sources:
            job.status = 'completed'
            job.completed_at = timezone.now()
            job.errors = ['No active news sources configured']
            job.save()
            return {'error': 'No active news sources configured'}

        # Run the scraping
        results = await scrape_all_sources(sources)

        # Save articles to database
        articles_new = 0
        for article_data in results['articles']:
            # Find the source
            source = NewsSource.objects.filter(name=article_data['source_name']).first()
            if not source:
                continue

            # Check if article already exists
            if NewsArticle.objects.filter(url=article_data['url']).exists():
                continue

            # Parse the published_at date
            published_at = None
            if article_data.get('published_at'):
                try:
                    published_at = datetime.strptime(article_data['published_at'], '%Y-%m-%d')
                    published_at = timezone.make_aware(published_at)
                except:
                    pass

            # Create the article
            NewsArticle.objects.create(
                title=article_data['title'][:500],
                url=article_data['url'],
                source=source,
                published_at=published_at,
                summary=article_data.get('summary', '')[:1000],
                image_url=article_data.get('image_url', '')[:500],
            )
            articles_new += 1

        # Update source statistics
        for source in NewsSource.objects.filter(is_active=True):
            source.last_scraped_at = timezone.now()
            source.last_scrape_status = 'success'
            source.articles_found_last_scrape = len([
                a for a in results['articles']
                if a['source_name'] == source.name
            ])
            source.save()

        # Update job
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.sources_processed = results['sources_processed']
        job.articles_found = results['articles_found']
        job.articles_new = articles_new
        job.errors = results['errors']
        job.save()

        return {
            'job_id': job.id,
            'status': 'completed',
            'sources_processed': results['sources_processed'],
            'articles_found': results['articles_found'],
            'articles_new': articles_new,
            'errors': results['errors']
        }

    except Exception as e:
        job.status = 'failed'
        job.completed_at = timezone.now()
        job.errors = [str(e)]
        job.save()
        raise


if __name__ == '__main__':
    # Test scraping
    async def test():
        test_sources = [
            {'name': 'Northern Miner', 'url': 'https://www.northernminer.com/', 'is_active': True},
            {'name': 'Mining.com', 'url': 'https://mining.com/', 'is_active': True},
        ]
        results = await scrape_all_sources(test_sources)
        print(f"\nTotal articles found: {results['articles_found']}")
        for article in results['articles'][:5]:
            print(f"  - {article['title'][:60]}...")

    asyncio.run(test())
