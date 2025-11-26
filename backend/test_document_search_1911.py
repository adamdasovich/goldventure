"""
Test Document Search for 1911 Gold Property Ownership
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from claude_integration.client import ClaudeClient
from core.models import User, Company
from mcp_servers.document_search import DocumentSearchServer


def test_direct_search():
    """Test direct search for property ownership info"""

    print("="*80)
    print("TESTING DIRECT DOCUMENT SEARCH - Property Ownership")
    print("="*80)

    # Get company
    company = Company.objects.filter(name__icontains='1911 Gold').first()
    if not company:
        print("ERROR: 1911 Gold not found in database")
        return

    print(f"\nCompany: {company.name}")
    print(f"Company ID: {company.id}")

    # Get user
    user = User.objects.filter(is_superuser=True).first()

    # Initialize document search server
    search_server = DocumentSearchServer(company.id, user)

    # Test search queries
    queries = [
        "property ownership history prior owner previous",
        "who owned the property before 1911 Gold",
        "previous owner acquisition history",
        "property acquisition tenure"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'-'*80}")
        print(f"Query {i}: {query}")
        print(f"{'-'*80}")

        result = search_server.handle_tool_call('search_documents', {
            'query': query,
            'company_id': company.id,
            'top_k': 3
        })

        if 'error' in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"Found {result.get('total_results', 0)} results")

            for j, doc_result in enumerate(result.get('results', []), 1):
                print(f"\n  Result {j}:")
                print(f"    Relevance: {doc_result.get('relevance_score', 0):.3f}")
                print(f"    Document: {doc_result.get('document_title', 'N/A')}")
                print(f"    Content: {doc_result.get('content', '')[:200]}...")


def test_chatbot_query():
    """Test chatbot with property ownership question"""

    print("\n" + "="*80)
    print("TESTING CHATBOT - Property Ownership Question")
    print("="*80)

    user = User.objects.filter(is_superuser=True).first()
    company = Company.objects.filter(name__icontains='1911 Gold').first()

    client = ClaudeClient(company_id=company.id if company else None, user=user)

    query = "Can you tell me what company owned 1911 Gold Corp properties prior to them?"

    print(f"\nQuestion: {query}\n")

    result = client.chat(query)

    print("Response:")
    print("-"*80)
    print(result['message'])
    print("-"*80)

    # Show tool usage
    if result['tool_calls']:
        print(f"\nTools used: {len(result['tool_calls'])}")
        for tc in result['tool_calls']:
            print(f"  - {tc['tool']}")
            if 'search_documents' in tc['tool']:
                print(f"    Query: {tc['input'].get('query', 'N/A')}")
                if tc.get('result'):
                    print(f"    Results: {tc['result'].get('total_results', 0)}")
    else:
        print("\n* WARNING: No tools were used!")
        print("* The chatbot should have used search_documents tool")

    print(f"\nTokens: {result['usage']['input_tokens']} in, {result['usage']['output_tokens']} out")


if __name__ == "__main__":
    # Test direct search first
    test_direct_search()

    # Then test via chatbot
    test_chatbot_query()
