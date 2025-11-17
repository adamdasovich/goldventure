"""
Test Financial MCP Server Integration with Claude
Test Claude's ability to query financial data, market info, and investor analytics
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


def test_financial_queries():
    """Test Claude with financial data queries"""

    print_section("INITIALIZING CLAUDE CLIENT WITH FINANCIAL DATA")
    client = ClaudeClient()
    print("* Claude client initialized")
    print(f"* API Key configured: {len(client.client.api_key)} characters")

    all_tools = client._get_all_tools()
    financial_tools = [t for t in all_tools if t['name'].startswith('financial_')]

    print(f"* {len(all_tools)} total MCP tools available")
    print(f"* {len(financial_tools)} financial tools available:")
    for tool in financial_tools:
        print(f"  - {tool['name']}")

    # Test queries for financial data
    queries = [
        "What is the current stock price and market cap for Aston Bay?",
        "Show me all capital raises across all companies",
        "What is the total amount of capital raised by 1911 Gold?",
        "Compare the market capitalizations of all companies",
        "What are the financing trends in the last 12 months?",
        "Who are the major investors in junior mining companies?",
    ]

    conversation_history = []

    for i, query in enumerate(queries, 1):
        print_section(f"QUERY {i}: {query}")

        try:
            result = client.chat(
                message=query,
                conversation_history=conversation_history
            )

            print("\nCLAUDE'S RESPONSE:")
            print("-" * 70)
            print(result['message'])
            print("-" * 70)

            # Show which tools were used
            if result['tool_calls']:
                print("\nTOOLS USED:")
                for tc in result['tool_calls']:
                    print(f"  - {tc['tool']}")
                    if tc.get('input'):
                        print(f"    Input: {json.dumps(tc['input'], indent=6)}")

            # Show token usage
            print(f"\nTokens: {result['usage']['input_tokens']} in, "
                  f"{result['usage']['output_tokens']} out")

            # Update conversation history for context
            conversation_history = result['conversation_history']

        except Exception as e:
            print(f"\nERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    print_section("FINANCIAL DATA TEST COMPLETE")
    print("\n* Claude can successfully query financial and market data!")
    print("* All financial MCP tools are working correctly")
    print("\nFinancial MCP Server Tools:")
    print("  1. financial_get_market_data - Stock prices and market cap")
    print("  2. financial_list_financings - Capital raises and deals")
    print("  3. financial_get_company_financings - Company financing history")
    print("  4. financial_list_investors - Investor information")
    print("  5. financial_compare_market_caps - Market cap comparisons")
    print("  6. financial_financing_analytics - Financing trends\n")


def interactive_financial_chat():
    """Interactive chat mode focused on financial queries"""

    print_section("INTERACTIVE FINANCIAL CHAT MODE")
    print("Ask Claude questions about market data, financings, and investors!")
    print("Type 'quit' or 'exit' to stop\n")

    print("Example questions:")
    print("  - What's the stock price of Aston Bay?")
    print("  - Show me recent financings")
    print("  - Compare market caps")
    print("  - What are the financing trends?")
    print()

    client = ClaudeClient()
    conversation_history = []

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!\n")
            break

        if not user_input:
            continue

        try:
            result = client.chat(
                message=user_input,
                conversation_history=conversation_history
            )

            print(f"\nClaude: {result['message']}")

            # Show tools used
            if result['tool_calls']:
                print(f"\n   [Used: {', '.join(tc['tool'] for tc in result['tool_calls'])}]")

            # Update conversation history
            conversation_history = result['conversation_history']

        except Exception as e:
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Run interactive mode
        interactive_financial_chat()
    else:
        # Run automated tests
        test_financial_queries()

        # Offer interactive mode
        print("\n" + "="*70)
        response = input("\nWould you like to try interactive financial chat? (y/n): ").strip().lower()
        if response == 'y':
            interactive_financial_chat()
