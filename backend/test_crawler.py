"""
Test the website crawler
Discovers NI 43-101 reports and other documents from company websites
"""

import asyncio
from mcp_servers.website_crawler import crawl_company_website


async def test_crawler():
    """Test crawling a mining company website"""

    print("="*80)
    print("TESTING WEBSITE CRAWLER")
    print("="*80)

    # Test with 1911 Gold website
    url = "https://www.1911gold.com"

    print(f"\nCrawling: {url}")
    print(f"Max depth: 2 (homepage + one level deep)")
    print(f"Looking for: NI 43-101 reports, presentations, technical documents")
    print("\nThis may take 30-60 seconds...\n")

    documents = await crawl_company_website(url, max_depth=2)

    print("\n" + "="*80)
    print(f"DISCOVERED {len(documents)} DOCUMENTS")
    print("="*80)

    # DEBUG: Check for any documents with '43-101' in URL
    technical_reports = [d for d in documents if '43-101' in d['url'].lower()]
    if technical_reports:
        print(f"\n[DEBUG] Found {len(technical_reports)} documents with '43-101' in URL:")
        for doc in technical_reports:
            print(f"  - Type: {doc['document_type']}, URL: {doc['url']}")
            print(f"    Title: {doc['title']}")
            print()

    # Group by type
    by_type = {}
    for doc in documents:
        doc_type = doc['document_type']
        if doc_type not in by_type:
            by_type[doc_type] = []
        by_type[doc_type].append(doc)

    # Display results
    for doc_type, docs in by_type.items():
        print(f"\n{doc_type.upper().replace('_', ' ')}: {len(docs)} documents")
        print("-" * 80)

        for doc in docs[:5]:  # Show first 5
            print(f"  [{doc['relevance_score']:.1f}] {doc['title'][:70]}")
            print(f"       {doc['url']}")
            if doc['year']:
                print(f"       Year: {doc['year']}")
            # DEBUG: Show classification info
            if doc_type == 'ni43101' or '43-101' in doc['url'].lower():
                print(f"       [DEBUG] Type: {doc_type}, URL contains '43-101': {'43-101' in doc['url'].lower()}")

        if len(docs) > 5:
            print(f"  ... and {len(docs) - 5} more")

    # Show NI 43-101 reports specifically
    ni43101_reports = [d for d in documents if d['document_type'] == 'ni43101']

    if ni43101_reports:
        print("\n" + "="*80)
        print("NI 43-101 TECHNICAL REPORTS (Ready to Process)")
        print("="*80)

        for i, doc in enumerate(ni43101_reports, 1):
            print(f"\n{i}. {doc['title']}")
            print(f"   URL: {doc['url']}")
            print(f"   Year: {doc['year'] or 'Unknown'}")
            print(f"   Relevance: {doc['relevance_score']}")

        print(f"\n[OK] Found {len(ni43101_reports)} NI 43-101 report(s)!")
        print("\nThese URLs can be added to the processing queue via:")
        print("1. Django admin 'Batch Add'")
        print("2. Or automatically with the 'Discover & Process' feature")

    else:
        print("\n[!] No NI 43-101 reports found")
        print("    Try increasing max_depth or check a different URL")

    print("\n" + "="*80)
    print("CRAWLER TEST COMPLETE")
    print("="*80)

    return documents


if __name__ == "__main__":
    asyncio.run(test_crawler())
