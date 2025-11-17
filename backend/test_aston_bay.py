"""
Test Aston Bay NI 43-101 Report Processing with Detailed Logging
"""

import os
import django
import json
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from mcp_servers.document_processor_hybrid import HybridDocumentProcessor
from core.models import Company, Document, Project, ResourceEstimate, EconomicStudy


def print_section(title):
    """Print a section header"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print("\n" + "="*80)
    print(f"  [{timestamp}] {title}")
    print("="*80)


def test_aston_bay_processing():
    """Test processing Aston Bay NI 43-101 report"""

    print_section("ASTON BAY NI 43-101 REPORT PROCESSING TEST")

    report_url = "https://astonbayholdings.com/site/assets/files/1399/aston_bay_storm-seal_2025.pdf"
    company_name = "Aston Bay"
    project_name = "Storm Copper Project"

    print(f"\nReport URL: {report_url}")
    print(f"Company: {company_name}")
    print(f"Project: {project_name}")
    print(f"\nExpected processing time: 50-70 minutes")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if company exists
    print_section("STEP 1: Checking Database")

    companies = Company.objects.filter(name__icontains='Aston')
    if companies.exists():
        print(f"[OK] Found company: {companies.first().name}")
        company = companies.first()
    else:
        print("[!] Company 'Aston Bay' not found in database")
        print("  Creating company record...")
        company = Company.objects.create(
            name="Aston Bay Holdings",
            ticker_symbol="BAY",
            exchange="TSXV",
            description="Junior exploration company"
        )
        print(f"[OK] Created company: {company.name}")

    # Initialize processor
    print_section("STEP 2: Initializing Document Processor")
    processor = HybridDocumentProcessor()
    print("[OK] Processor initialized")

    # Start processing
    print_section("STEP 3: Processing Document")
    print("This will:")
    print("  1. Download PDF (~30 seconds)")
    print("  2. Extract with Docling (~45-60 minutes)")
    print("  3. Interpret with Claude (~10-20 seconds)")
    print("  4. Store in database (~1 second)")

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

        # Show results
        print("\n" + "="*80)
        print("RESULTS:")
        print("="*80)
        print(json.dumps(result, indent=2, default=str))

        # Check what was stored
        print_section("STEP 5: Verifying Database Storage")

        if result.get('success'):
            doc_id = result.get('document_id')
            doc = Document.objects.get(id=doc_id)

            print(f"\n[OK] Document stored:")
            print(f"  ID: {doc.id}")
            print(f"  Title: {doc.title}")
            print(f"  Company: {doc.company.name}")
            print(f"  Project: {doc.project.name if doc.project else 'NO PROJECT LINKED'}")
            print(f"  Date: {doc.document_date}")
            print(f"  URL: {doc.file_url[:80]}...")

            if doc.project:
                print(f"\n[OK] Project found:")
                print(f"  Name: {doc.project.name}")
                print(f"  Location: {doc.project.location}")
                print(f"  Stage: {doc.project.project_stage}")

                # Check resources
                resources = ResourceEstimate.objects.filter(project=doc.project)
                print(f"\n[OK] Resource Estimates: {resources.count()}")
                for i, res in enumerate(resources[:10], 1):
                    grade_str = f"{res.grade_gpt}g/t" if res.grade_gpt else f"{res.grade_percent}%"
                    metal_str = f"{res.contained_metal_oz:,}oz" if res.contained_metal_oz else "N/A"
                    print(f"  {i}. {res.resource_category.upper()}: {res.tonnage_mt}Mt @ {grade_str} = {metal_str} {res.mineral_type}")

                # Check economics
                econ_studies = EconomicStudy.objects.filter(project=doc.project)
                print(f"\n[OK] Economic Studies: {econ_studies.count()}")
                for i, econ in enumerate(econ_studies, 1):
                    npv_millions = float(econ.npv_usd) / 1_000_000
                    print(f"  {i}. {econ.study_type.upper()}: NPV ${npv_millions:.1f}M @ {econ.discount_rate}% | IRR {econ.irr}%")
            else:
                print("\n[!] WARNING: No project was linked to the document!")
                print("  This means no resources or economics were stored.")

            # Show processing stats
            stats = result.get('processing_stats', {})
            print(f"\nProcessing Statistics:")
            print(f"  Tables extracted: {stats.get('tables_extracted', 0)}")
            print(f"  Pages processed: {stats.get('pages_processed', 0)}")
            print(f"  Resources stored: {stats.get('resources_stored', 0)}")
            print(f"  Economic study stored: {stats.get('economic_study_stored', False)}")

            # Show extracted data summary
            extracted = result.get('extracted_data', {})
            if extracted.get('document_info'):
                print(f"\nDocument Info:")
                print(f"  {json.dumps(extracted['document_info'], indent=4)}")
            if extracted.get('project_info'):
                print(f"\nProject Info:")
                print(f"  {json.dumps(extracted['project_info'], indent=4)}")
            if extracted.get('key_findings'):
                print(f"\nKey Findings:")
                print(f"  {json.dumps(extracted['key_findings'], indent=4, default=str)}")

        else:
            print("\n[!] PROCESSING FAILED")
            if 'error' in result:
                print(f"\nError: {result['error']}")
            if 'warning' in result:
                print(f"\nWarning: {result['warning']}")
                if 'raw_analysis' in result:
                    print(f"\nClaude's raw response (first 1000 chars):")
                    print(result['raw_analysis'][:1000])
            if 'docling_stats' in result:
                print(f"\nDocling Stats:")
                print(f"  {json.dumps(result['docling_stats'], indent=2)}")

        print_section("TEST COMPLETE")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("INTERRUPTED BY USER")
        print("="*80)
    except Exception as e:
        print("\n\n" + "="*80)
        print("EXCEPTION OCCURRED")
        print("="*80)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_aston_bay_processing()
