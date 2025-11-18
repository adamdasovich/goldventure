"""
Test 1911 Gold NI 43-101 Report Processing with RAG System
Process the True North Gold Project report with full text storage
"""

import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mcp_servers.document_processor_hybrid import HybridDocumentProcessor
from core.models import Company, Document, Project, ResourceEstimate, DocumentChunk
from mcp_servers.document_search import DocumentSearchServer

def print_section(title):
    """Print a section header"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print("\n" + "="*80)
    print(f"  [{timestamp}] {title}")
    print("="*80)

def test_1911_gold_processing():
    """Test processing 1911 Gold NI 43-101 report with RAG"""

    print_section("1911 GOLD NI 43-101 REPORT PROCESSING WITH RAG")

    report_url = "https://www.1911gold.com/_resources/reports/2024-43-101-True-North-Gold-Project.pdf"
    company_name = "1911 Gold"
    project_name = "True North Gold Project"

    print(f"\nReport URL: {report_url}")
    print(f"Company: {company_name}")
    print(f"Project: {project_name}")
    print(f"\nExpected processing time: 60-80 minutes")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if company exists
    print_section("STEP 1: Checking Database")
    companies = Company.objects.filter(name__icontains="1911")
    if companies.exists():
        print(f"[OK] Found company: {companies.first().name}")
    else:
        print("[!] Company '1911 Gold' not found in database")
        print("    Creating company record...")
        Company.objects.create(
            name="1911 Gold Corporation",
            ticker_symbol="AUMB.TO",
            exchange="TSX-V"
        )
        print("[OK] Company created")

    # Initialize processor
    print_section("STEP 2: Initializing Document Processor")
    processor = HybridDocumentProcessor()
    print("[OK] Processor initialized with RAG support")

    # Process document
    print_section("STEP 3: Processing Document")
    print("This will:")
    print("  1. Download PDF (~30 seconds)")
    print("  2. Extract with Docling (~60-75 minutes)")
    print("  3. Interpret with Claude (~10-20 seconds)")
    print("  4. Store structured data in database (~1 second)")
    print("  5. Chunk and embed full text for RAG (~5-10 seconds)")

    try:
        start_time = datetime.now()

        result = processor._process_ni43101_hybrid(
            document_url=report_url,
            company_name=company_name,
            project_name=project_name
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print_section("STEP 4: Processing Complete!")
        print(f"Total time: {duration:.1f} seconds ({duration/60:.1f} minutes)")

        # Display results
        print_section("RESULTS")
        import json
        print(json.dumps(result, indent=2, default=str))

        if result.get('success'):
            doc_id = result.get('document_id')
            doc = Document.objects.get(id=doc_id)

            print_section("STEP 5: Verifying Database Storage")

            # Check structured data
            print("\n[OK] Document stored:")
            print(f"  ID: {doc.id}")
            print(f"  Title: {doc.title}")
            print(f"  Company: {doc.company.name}")
            print(f"  Project: {doc.project.name if doc.project else 'None'}")
            print(f"  Date: {doc.document_date}")

            if doc.project:
                print(f"\n[OK] Project found: {doc.project.name}")

                # Check resources
                resources = ResourceEstimate.objects.filter(project=doc.project)
                print(f"\n[OK] Resource Estimates: {resources.count()}")
                for res in resources:
                    if res.gold_grade_gpt:
                        print(f"  - {res.category.title()}: {res.tonnes:,.0f} tonnes @ {res.gold_grade_gpt} g/t Au")
                    elif res.copper_grade_pct:
                        print(f"  - {res.category.title()}: {res.tonnes:,.0f} tonnes @ {res.copper_grade_pct}% Cu")

            # Check RAG chunks
            chunks = DocumentChunk.objects.filter(document=doc)
            print(f"\n[OK] Document Chunks for RAG: {chunks.count()}")
            if chunks.exists():
                total_tokens = sum(c.token_count for c in chunks)
                print(f"  Total tokens: {total_tokens:,}")
                print(f"  Average chunk size: {total_tokens // chunks.count()} tokens")

            # Test semantic search
            print_section("STEP 6: Testing Semantic Search")
            test_queries = [
                "What are the total gold resources?",
                "What is the mining method?",
                "What are the metallurgical recoveries?",
                "Tell me about the infrastructure"
            ]

            search_server = DocumentSearchServer()

            for query in test_queries:
                print(f"\n  Query: '{query}'")
                result = search_server._search_documents(
                    query=query,
                    company_name=doc.company.name,
                    max_results=2
                )

                if result.get('found'):
                    print(f"  [OK] Found {result['total_results']} relevant chunks")
                    for res in result['results'][:1]:  # Show first result only
                        print(f"      Preview: {res['text'][:200]}...")
                else:
                    print(f"  [!] No results found")

            print_section("SUCCESS!")
            print("\nThe 1911 Gold report has been processed and is ready for queries!")
            print("\nYou can now ask your chatbot:")
            print("  - 'What are the gold resources at True North?'")
            print("  - 'What were the drilling results?'")
            print("  - 'Tell me about the metallurgy'")
            print("  - And any other detailed questions about the report!")

        else:
            print_section("PROCESSING FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")

    except KeyboardInterrupt:
        print("\n\n[!] Cancelled by user")
    except Exception as e:
        print_section("ERROR OCCURRED")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_1911_gold_processing()
