"""Debug crawler to see what PDFs are being found"""

import asyncio
from mcp_servers.website_crawler import MiningDocumentCrawler


async def debug_crawler():
    crawler = MiningDocumentCrawler()

    print("Starting crawler...")
    documents = await crawler.discover_documents(
        start_url="https://www.1911gold.com",
        max_depth=2
    )

    print(f"\nFound {len(documents)} documents")
    print("\nFirst 10 URLs:")
    for i, doc in enumerate(documents[:10], 1):
        print(f"\n{i}. {doc['title']}")
        print(f"   URL: {doc['url']}")
        print(f"   Type: {doc['document_type']}")
        print(f"   Score: {doc['relevance_score']}")

        # Show why it was classified
        combined = (doc['title'] + ' ' + doc['url']).lower()
        print(f"   Combined text: {combined[:100]}...")

        if '43-101' in combined:
            print(f"   ✓ Contains '43-101'")
        if 'technical-report' in combined:
            print(f"   ✓ Contains 'technical-report'")
        if 'nr-' in combined:
            print(f"   ✓ Contains 'nr-' (news release)")


if __name__ == "__main__":
    asyncio.run(debug_crawler())
