"""
Quick diagnostic check - see what Claude extracted yesterday
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mcp_servers.document_processor_hybrid import HybridDocumentProcessor
from docling.document_converter import DocumentConverter
import json

def quick_diagnostic():
    """Quick check of what Docling can extract"""

    print("="*70)
    print("QUICK DIAGNOSTIC - Sample Table Extraction")
    print("="*70)

    processor = HybridDocumentProcessor()

    report_url = "https://www.1911gold.com/_resources/reports/2024-43-101-True-North-Gold-Project.pdf?v=021110"

    print(f"\n1. Downloading PDF...")
    pdf_path = processor._download_pdf(report_url)
    print(f"   Downloaded to: {pdf_path}")

    print(f"\n2. Extracting with Docling (first 10 pages only for speed)...")
    print("   This will take ~5-10 minutes...")

    try:
        # Process just first pages for quick check
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        doc = result.document

        # Get tables
        tables = []
        for item, _ in doc.iterate_items():
            from docling_core.types.doc import TableItem
            if isinstance(item, TableItem):
                tables.append({
                    'caption': item.caption if hasattr(item, 'caption') else None,
                    'data': item.export_to_markdown()
                })

        print(f"\n3. Results:")
        print(f"   Pages: {len(doc.pages) if hasattr(doc, 'pages') else 'unknown'}")
        print(f"   Tables found: {len(tables)}")

        # Show first few tables
        print(f"\n4. Sample Tables:")
        for i, table in enumerate(tables[:3]):
            print(f"\n   Table {i+1}:")
            print(f"   Caption: {table['caption']}")
            print(f"   Data preview:\n{table['data'][:300]}...")

        # Get some text
        markdown_text = doc.export_to_markdown()
        print(f"\n5. Document Text Sample (first 1000 chars):")
        print(markdown_text[:1000])

        # Now test Claude interpretation
        print(f"\n6. Testing Claude interpretation...")
        prompt = """Look at this data from an NI 43-101 mining report.
Extract the project name if you can find it.
Return JSON: {"project_name": "...", "found": true/false}"""

        context = f"TEXT:\n{markdown_text[:5000]}\n\nTABLES:\n{json.dumps(tables[:2], indent=2)}"

        response = processor._ask_claude(prompt, context, max_tokens=500)
        print(f"\n   Claude's response:\n{response}")

        # Cleanup
        pdf_path.unlink()
        print(f"\n7. Cleanup complete")

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        if pdf_path.exists():
            pdf_path.unlink()

if __name__ == "__main__":
    quick_diagnostic()
