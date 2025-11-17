"""
Test Hybrid Document Processor with Real NI 43-101 Report
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from claude_integration.client import ClaudeClient
import json


def print_section(title):
    """Print a section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_document_processing():
    """Test processing a real NI 43-101 report"""

    print_section("TESTING HYBRID DOCUMENT PROCESSOR")

    # Real NI 43-101 report from 1911 Gold
    report_url = "https://www.1911gold.com/_resources/reports/2024-43-101-True-North-Gold-Project.pdf?v=021110"
    company_name = "1911 Gold"

    print(f"\nReport URL: {report_url}")
    print(f"Company: {company_name}")
    print("\nThis will:")
    print("1. Download the PDF")
    print("2. Extract structure and tables with Docling")
    print("3. Interpret data with Claude")
    print("4. Store results in database")

    print_section("INITIALIZING CLAUDE CLIENT")
    client = ClaudeClient()

    all_tools = client._get_all_tools()
    doc_tools = [t for t in all_tools if t['name'].startswith('document_')]

    print(f"* {len(all_tools)} total MCP tools available")
    print(f"* {len(doc_tools)} document processing tools:")
    for tool in doc_tools:
        print(f"  - {tool['name']}")

    print_section("PROCESSING NI 43-101 REPORT")
    print("\nAsking Claude to process the report...")
    print("(This may take 1-2 minutes for a large report)")

    try:
        result = client.chat(
            message=f"Process the NI 43-101 technical report at {report_url} for {company_name}. "
                    f"Extract all resource estimates, economic data, and key findings.",
            conversation_history=[]
        )

        print("\nCLAUDE'S RESPONSE:")
        print("-" * 70)
        print(result['message'])
        print("-" * 70)

        # Show tool calls
        if result['tool_calls']:
            print("\nTOOLS USED:")
            for tc in result['tool_calls']:
                print(f"\n  Tool: {tc['tool']}")
                print(f"  Input: {json.dumps(tc['input'], indent=4)}")

                if tc.get('result'):
                    result_data = tc['result']
                    if isinstance(result_data, dict):
                        # Show key metrics
                        if 'processing_stats' in result_data:
                            print(f"\n  Processing Stats:")
                            for key, value in result_data['processing_stats'].items():
                                print(f"    - {key}: {value}")

                        if 'extracted_data' in result_data:
                            print(f"\n  Extracted Data Summary:")
                            ext_data = result_data['extracted_data']
                            if 'document_info' in ext_data:
                                print(f"    Document: {ext_data['document_info']}")
                            if 'project_info' in ext_data:
                                print(f"    Project: {ext_data['project_info']}")

        # Show token usage
        print(f"\nTokens Used: {result['usage']['input_tokens']} in, "
              f"{result['usage']['output_tokens']} out")

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

    print_section("TEST COMPLETE")


def test_resource_extraction():
    """Test extracting just the resource tables"""

    print_section("TESTING RESOURCE TABLE EXTRACTION")

    report_url = "https://www.1911gold.com/_resources/reports/2024-43-101-True-North-Gold-Project.pdf?v=021110"

    print("\nAsking Claude to extract just the resource estimates...")

    client = ClaudeClient()

    try:
        result = client.chat(
            message=f"Extract the mineral resource estimates from {report_url}",
            conversation_history=[]
        )

        print("\nCLAUDE'S RESPONSE:")
        print("-" * 70)
        print(result['message'])
        print("-" * 70)

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--resources":
        # Test resource extraction only
        test_resource_extraction()
    else:
        # Test full processing
        test_document_processing()

        print("\n" + "="*70)
        print("\nWant to test resource extraction only?")
        print("Run: python test_document_processor.py --resources")
