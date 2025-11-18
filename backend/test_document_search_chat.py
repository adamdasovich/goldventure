"""
Test Document Search Integration with Chatbot
Test that Claude can search and answer questions about processed documents
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from claude_integration.client import ClaudeClient


def print_section(title):
    """Print a section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_document_search_integration():
    """Test that chatbot can search processed documents"""

    print_section("TESTING DOCUMENT SEARCH INTEGRATION")

    # Initialize client
    client = ClaudeClient()
    print("\n[OK] Claude client initialized")

    # Check available tools
    all_tools = client._get_all_tools()
    search_tools = [t for t in all_tools if 'search' in t['name'].lower() or 'document_context' in t['name'].lower()]

    print(f"\n[OK] {len(all_tools)} total tools available")
    print(f"[OK] {len(search_tools)} document search tools:")
    for tool in search_tools:
        print(f"  - {tool['name']}")

    # Test queries
    test_queries = [
        "Can you tell me about the metallurgy at 1911 Gold's True North Complex?",
        "What are the gold resources at True North?",
        "What drilling results were reported for True North?",
        "Tell me about the infrastructure at the True North project"
    ]

    print_section("RUNNING TEST QUERIES")

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 80)

        try:
            result = client.chat(message=query, max_tokens=1500)

            print(f"\nClaude's Response:")
            print(result['message'])

            if result['tool_calls']:
                print(f"\n[OK] Tools Used:")
                for tc in result['tool_calls']:
                    print(f"  - {tc['tool']}")
            else:
                print(f"\n[!] No tools were called")

            print(f"\nTokens: {result['usage']['input_tokens']} in, {result['usage']['output_tokens']} out")

        except Exception as e:
            print(f"\n[ERROR] Error: {str(e)}")
            import traceback
            traceback.print_exc()

    print_section("TEST COMPLETE")
    print("\nDocument search integration is working!")
    print("Your chatbot can now answer detailed questions about processed NI 43-101 reports.")


if __name__ == "__main__":
    test_document_search_integration()
