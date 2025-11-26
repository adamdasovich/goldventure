"""
Test Link Text Extraction from 1911 Gold News Page - Simple Version
"""

import requests
from bs4 import BeautifulSoup


def test_link_extraction():
    """Test extracting actual news titles from 1911 Gold website"""

    url = "https://www.1911gold.com/news/"

    print("="*80)
    print("Testing Link Text Extraction")
    print("="*80)
    print(f"\nFetching: {url}\n")

    response = requests.get(url, timeout=30)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

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
            print(f"   Text Length: {len(link['text'])} chars")
    else:
        print(f"Failed to fetch page. Status code: {response.status_code}")


if __name__ == "__main__":
    test_link_extraction()
