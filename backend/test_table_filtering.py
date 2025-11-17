"""
Quick test to verify table filtering is working correctly
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mcp_servers.document_processor_hybrid import HybridDocumentProcessor

def test_table_filtering():
    """Test that the table filtering identifies resource tables"""

    print("="*80)
    print("TESTING TABLE FILTERING")
    print("="*80)

    processor = HybridDocumentProcessor()

    report_url = "https://astonbayholdings.com/site/assets/files/1399/aston_bay_storm-seal_2025.pdf"

    print("\n1. Downloading PDF...")
    pdf_path = processor._download_pdf(report_url)

    print("2. Extracting with Docling (this will take ~60 minutes)...")
    print("   Press Ctrl+C if you want to skip")

    try:
        docling_data = processor._process_with_docling(pdf_path)

        print(f"\n3. Docling extracted {len(docling_data['tables'])} tables")

        print("\n4. Filtering tables for resource estimates...")
        filtered_tables = processor._filter_resource_tables(docling_data['tables'])

        print(f"   Found {len(filtered_tables)} relevant tables")

        print("\n5. Top 10 filtered tables:")
        for i, table in enumerate(filtered_tables[:10], 1):
            caption = table.get('caption', 'No caption')
            data_preview = table['data'][:200].replace('\n', ' ')
            print(f"\n   Table {i}:")
            print(f"   Caption: {caption}")
            print(f"   Data preview: {data_preview}...")

        print("\n6. Now asking Claude to interpret with filtered tables...")
        prompt = """Analyze this NI 43-101 technical report extracted by Docling.

The document has been pre-processed:
- Tables have been extracted and converted to markdown
- Text structure has been preserved
- Sections have been identified

Extract ALL key data in JSON format:

{
  "document_info": {
    "title": "...",
    "report_date": "YYYY-MM-DD",
    "authors": ["..."],
    "qualified_persons": ["..."]
  },
  "project_info": {
    "project_name": "...",
    "location": "...",
    "property_size_hectares": <number>,
    "ownership_percentage": <number>
  },
  "mineral_resources": [
    {
      "category": "Measured|Indicated|Inferred",
      "mineral_type": "gold|silver|copper|...",
      "tonnage_mt": <number>,
      "grade": <number>,
      "grade_unit": "g/t|%",
      "contained_metal": <number>,
      "contained_unit": "oz|tonnes"
    }
  ],
  "economic_study": {
    "study_type": "PEA|PFS|FS",
    "npv_usd_millions": <number>,
    "discount_rate": <number>,
    "irr_percent": <number>,
    "capex_initial_usd_millions": <number>,
    "opex_per_tonne": <number>,
    "payback_period_years": <number>,
    "mine_life_years": <number>
  },
  "key_findings": {
    "executive_summary": "...",
    "highlights": ["...", "..."],
    "recommendations": ["...", "..."]
  }
}

Return ONLY valid JSON. Use null for missing values."""

        import json as json_module

        context = f"""DOCUMENT TEXT AND STRUCTURE:
{docling_data['text'][:15000]}

EXTRACTED TABLES ({len(docling_data['tables'])} total tables, showing {len(filtered_tables)} most relevant):
{json_module.dumps(filtered_tables, indent=2)[:50000]}
"""

        response_text = processor._ask_claude(prompt, context, max_tokens=4000)

        print("\n" + "="*80)
        print("CLAUDE'S RESPONSE:")
        print("="*80)
        print(response_text)
        print("="*80)

        # Parse and check for mineral_resources
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1:
                data = json.loads(response_text[json_start:json_end])

                if 'mineral_resources' in data and data['mineral_resources']:
                    print("\n[SUCCESS] Found mineral_resources array!")
                    for i, res in enumerate(data['mineral_resources'], 1):
                        print(f"\n  Resource {i}:")
                        print(f"    Category: {res.get('category')}")
                        print(f"    Mineral: {res.get('mineral_type')}")
                        print(f"    Tonnage: {res.get('tonnage_mt')} Mt")
                        print(f"    Grade: {res.get('grade')} {res.get('grade_unit')}")
                        print(f"    Contained: {res.get('contained_metal')} {res.get('contained_unit')}")

                        # Check if values are populated
                        if res.get('tonnage_mt') and res.get('grade'):
                            print(f"    [OK] This resource has valid data and will be stored!")
                        else:
                            print(f"    [!] Missing tonnage or grade - will NOT be stored")
                else:
                    print("\n[FAILED] No mineral_resources in response")

        except Exception as e:
            print(f"\n[ERROR] Could not parse JSON: {e}")

        # Cleanup
        pdf_path.unlink()
        print("\n7. Test complete")

    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        if pdf_path.exists():
            pdf_path.unlink()
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        if pdf_path.exists():
            pdf_path.unlink()

if __name__ == "__main__":
    test_table_filtering()
