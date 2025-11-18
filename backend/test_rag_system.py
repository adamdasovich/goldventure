"""
Test RAG (Retrieval-Augmented Generation) System
Tests document chunking, embedding, and semantic search
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Document, DocumentChunk
from mcp_servers.rag_utils import RAGManager
from mcp_servers.document_search import DocumentSearchServer

def test_rag_with_existing_document():
    """Test RAG system using an already processed document"""

    print("="*80)
    print("RAG SYSTEM TEST")
    print("="*80)

    # Get the Aston Bay document (ID 4 from our tests)
    try:
        document = Document.objects.get(id=4)
        print(f"\n1. Found document: {document.title}")
        print(f"   Company: {document.company.name}")
        print(f"   Date: {document.document_date}")
    except Document.DoesNotExist:
        print("\n[ERROR] Document ID 4 not found. Please run test_aston_bay.py first.")
        return

    # Check if we have Docling data stored
    print("\n2. Checking for stored document text...")
    # Note: We need to re-process to get the full text since it's not stored yet
    print("   [INFO] Full text not stored in database yet")
    print("   [INFO] In production, we'll need to re-process or store text during initial processing")

    # For now, let's manually test with some sample text
    sample_text = """
    Initial Mineral Resource Estimate and Technical Report on the Storm Copper Project

    SUMMARY OF MINERAL RESOURCES:
    The Storm Copper Project contains the following indicated and inferred resources:

    Indicated Resources:
    - 8.229 million tonnes at 1.47% Cu and 4.5 g/t Ag
    - This represents approximately 121,000 tonnes of contained copper
    - And approximately 1.2 million ounces of contained silver

    Inferred Resources:
    - 3.387 million tonnes at 1.30% Cu and 3.1 g/t Ag
    - This represents approximately 44,000 tonnes of contained copper
    - And approximately 337,000 ounces of contained silver

    SEAL ZINC DEPOSIT:
    The Seal zone contains high-grade zinc mineralization:
    - 1.006 million tonnes at 10.24% Zn and 46.6 g/t Ag (Inferred)
    - This represents approximately 103,000 tonnes of contained zinc
    - And approximately 1.5 million ounces of contained silver

    MINERALIZED ZONES:
    The property contains multiple mineralized zones including:
    - Chinook Zone: Main copper-silver mineralization
    - Cyclone Zone: High-grade copper discovery
    - Cirrus Zone: Near-surface copper mineralization
    - Corona Zone: Exploration target
    - Lightning Ridge: Copper-silver showings
    - Thunder Zone: Geophysical anomaly with drill intersections

    DRILLING RESULTS:
    Recent drilling at the Chinook zone returned:
    - Hole SC22-001: 15.2 meters at 2.4% Cu
    - Hole SC22-002: 22.3 meters at 1.8% Cu and 5.2 g/t Ag
    - Hole SC22-003: 10.5 meters at 3.1% Cu

    METALLURGICAL TESTING:
    Preliminary metallurgical tests indicate:
    - Copper recoveries of 90-95% through flotation
    - Silver recoveries of 75-80%
    - Concentrate grades of 20-25% Cu
    """

    # Store the chunks
    print("\n3. Storing document chunks in RAG system...")
    rag_manager = RAGManager()
    try:
        chunks_stored = rag_manager.store_document_chunks(document, sample_text)
        print(f"   [OK] Stored {chunks_stored} chunks")
    except Exception as e:
        print(f"   [ERROR] Failed to store chunks: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # Verify chunks in database
    db_chunks = DocumentChunk.objects.filter(document=document).count()
    print(f"   [OK] Verified {db_chunks} chunks in PostgreSQL database")

    # Test semantic search
    print("\n4. Testing semantic search...")
    test_queries = [
        "What are the copper resources at Storm?",
        "Tell me about the Seal zinc deposit",
        "What were the drilling results?",
        "Which zones have been identified?",
        "What are the metallurgical recoveries?"
    ]

    search_server = DocumentSearchServer()

    for query in test_queries:
        print(f"\n   Query: '{query}'")
        result = search_server._search_documents(query, company_name="Aston Bay Holdings Ltd.", max_results=2)

        if result.get('found'):
            print(f"   [OK] Found {result['total_results']} relevant chunks")
            for res in result['results']:
                print(f"      Rank {res['rank']}: {res['text'][:150]}...")
        else:
            print(f"   [!] No results found")

    # Test getting context for a question
    print("\n5. Testing context retrieval for question answering...")
    question = "What are the total indicated and inferred copper resources?"
    context_result = search_server._get_document_context(question, company_name="Aston Bay Holdings Ltd.")

    if context_result.get('success'):
        print(f"   [OK] Retrieved context:")
        print(f"\n{context_result['context'][:500]}...")
    else:
        print(f"   [ERROR] {context_result.get('error')}")

    print("\n" + "="*80)
    print("RAG SYSTEM TEST COMPLETE")
    print("="*80)
    print("\nNEXT STEPS:")
    print("1. Your chatbot can now use the 'search_documents' tool to find information")
    print("2. When processing new documents, full text will automatically be chunked and embedded")
    print("3. Users can ask detailed questions and get answers with document citations")


if __name__ == "__main__":
    test_rag_with_existing_document()
