"""
Direct test of document processor - bypassing chat interface
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mcp_servers.document_processor_hybrid import HybridDocumentProcessor
import json

def test_direct_processing():
    """Call the processor directly to see what happens"""

    print("="*70)
    print("DIRECT DOCUMENT PROCESSOR TEST")
    print("="*70)

    processor = HybridDocumentProcessor()

    report_url = "https://www.1911gold.com/_resources/reports/2024-43-101-True-North-Gold-Project.pdf?v=021110"
    company_name = "1911 Gold"

    print(f"\nProcessing: {report_url}")
    print(f"Company: {company_name}")
    print("\nThis will take ~1 hour on CPU...")
    print("Press Ctrl+C to cancel\n")

    try:
        result = processor._process_ni43101_hybrid(
            document_url=report_url,
            company_name=company_name,
            project_name="True North Gold Project"
        )

        print("\n" + "="*70)
        print("RESULT:")
        print("="*70)
        print(json.dumps(result, indent=2, default=str))

        if result.get('success'):
            print("\n" + "="*70)
            print("SUCCESS - Data stored in database!")
            print("="*70)
            print(f"Document ID: {result.get('document_id')}")
            print(f"Resources stored: {result.get('processing_stats', {}).get('resources_stored', 0)}")
            print(f"Economic study stored: {result.get('processing_stats', {}).get('economic_study_stored', False)}")
        else:
            print("\n" + "="*70)
            print("FAILED")
            print("="*70)
            if 'error' in result:
                print(f"Error: {result['error']}")
            if 'warning' in result:
                print(f"Warning: {result['warning']}")
                print(f"Raw analysis: {result.get('raw_analysis', '')[:500]}")

    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\nEXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_processing()
