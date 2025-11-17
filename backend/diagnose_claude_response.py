"""
Diagnose what Claude actually returned for Aston Bay
"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mcp_servers.document_processor_hybrid import HybridDocumentProcessor

def test_claude_interpretation():
    """Re-run just the Claude interpretation part with the same PDF"""

    print("="*80)
    print("DIAGNOSTIC: What did Claude extract from Aston Bay report?")
    print("="*80)

    processor = HybridDocumentProcessor()

    report_url = "https://astonbayholdings.com/site/assets/files/1399/aston_bay_storm-seal_2025.pdf"

    print("\nStep 1: Downloading PDF...")
    pdf_path = processor._download_pdf(report_url)

    print("Step 2: Processing with Docling (this will take ~60 minutes)...")
    print("         Press Ctrl+C if you want to skip this")

    try:
        docling_data = processor._process_with_docling(pdf_path)

        print(f"\nDocling Results:")
        print(f"  Pages: {docling_data['page_count']}")
        print(f"  Tables: {len(docling_data['tables'])}")

        # Show first few tables to see what was extracted
        print(f"\nFirst 3 tables extracted:")
        for i, table in enumerate(docling_data['tables'][:3], 1):
            print(f"\n  Table {i}:")
            print(f"  Caption: {table.get('caption', 'No caption')}")
            print(f"  Data (first 500 chars):")
            print(f"  {table['data'][:500]}")

        print("\nStep 3: Asking Claude to interpret...")

        # This is the EXACT prompt used by the processor
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

        context = f"""DOCUMENT TEXT AND STRUCTURE:
{docling_data['text'][:15000]}

EXTRACTED TABLES ({len(docling_data['tables'])} tables found):
{json.dumps(docling_data['tables'][:5], indent=2)}
"""

        response_text = processor._ask_claude(prompt, context, max_tokens=4000)

        print("\n" + "="*80)
        print("CLAUDE'S FULL RESPONSE:")
        print("="*80)
        print(response_text)
        print("="*80)

        # Try to parse it
        print("\nStep 4: Parsing JSON...")
        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                extracted_json = response_text[json_start:json_end]
                data = json.loads(extracted_json)

                print("\n[OK] JSON parsed successfully!")
                print("\nExtracted data structure:")
                print(json.dumps(data, indent=2))

                # Check specifically for mineral_resources
                if 'mineral_resources' in data:
                    print(f"\n[OK] Found mineral_resources array with {len(data['mineral_resources'])} entries")
                    for i, res in enumerate(data['mineral_resources'][:3], 1):
                        print(f"\n  Resource {i}:")
                        print(f"    Category: {res.get('category')}")
                        print(f"    Mineral: {res.get('mineral_type')}")
                        print(f"    Tonnage: {res.get('tonnage_mt')} Mt")
                        print(f"    Grade: {res.get('grade')} {res.get('grade_unit')}")
                        print(f"    Contained: {res.get('contained_metal')} {res.get('contained_unit')}")
                else:
                    print("\n[!] NO mineral_resources array in response!")
                    print("    This is why no resources were stored in database")

            else:
                print("\n[!] Could not find JSON in response")

        except json.JSONDecodeError as e:
            print(f"\n[!] JSON parsing failed: {e}")

    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    finally:
        if pdf_path.exists():
            pdf_path.unlink()
            print("\nCleaned up temporary file")

if __name__ == "__main__":
    test_claude_interpretation()
