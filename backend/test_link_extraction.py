"""
Test Link Text Extraction from 1911 Gold News Page
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup


async def test_link_extraction():
    """Test extracting actual news titles from 1911 Gold website"""

    url = "https://www.1911gold.com/news/"

    print("="*80)
    print("Testing Link Text Extraction")
    print("="*80)
    print(f"\nCrawling: {url}\n")

    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=url)

        if result.success:
            soup = BeautifulSoup(result.html, 'html.parser')

            # Find all PDF links
            pdf_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '.pdf' in href.lower():
                    link_text = link.get_text(strip=True)
                    full_url = href if href.startswith('http') else f"https://www.1911gold.com{href}"

                    pdf_links.append({
                        'url': full_url,
                        'text': link_text,
                        'raw_href': href
                    })

            print(f"Found {len(pdf_links)} PDF links\n")
            print("First 10 links:")
            print("-"*80)

            for i, link in enumerate(pdf_links[:10], 1):
                print(f"\n{i}. URL: {link['url']}")
                print(f"   Text: '{link['text']}'")
                print(f"   Length: {len(link['text'])} chars")
        else:
            print("Failed to crawl page")


if __name__ == "__main__":
    asyncio.run(test_link_extraction())
