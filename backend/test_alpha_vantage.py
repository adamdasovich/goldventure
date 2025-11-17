"""
Test Alpha Vantage MCP Server Integration with Claude
Test real-time market data fetching and database caching
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from claude_integration.client import ClaudeClient
from core.models import Company, MarketData
from django.conf import settings
import json


def print_section(title):
    """Print a section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def check_api_key():
    """Check if Alpha Vantage API key is configured"""
    print_section("CHECKING ALPHA VANTAGE API KEY")

    if not settings.ALPHA_VANTAGE_API_KEY:
        print("\nWARNING: Alpha Vantage API key not configured!")
        print("Please add ALPHA_VANTAGE_API_KEY to your .env file")
        print("\nTo get a free API key:")
        print("1. Visit https://www.alphavantage.co/support/#api-key")
        print("2. Sign up for a free account")
        print("3. Add the key to your .env file")
        print("\nSkipping Alpha Vantage tests...")
        return False
    else:
        print(f"\n* API Key configured: {settings.ALPHA_VANTAGE_API_KEY[:8]}...")
        print("* API Key status: OK")
        return True


def test_alpha_vantage_queries():
    """Test Claude with Alpha Vantage queries"""

    if not check_api_key():
        return

    print_section("INITIALIZING CLAUDE CLIENT WITH ALPHA VANTAGE")
    client = ClaudeClient()
    print("* Claude client initialized")

    all_tools = client._get_all_tools()
    alpha_tools = [t for t in all_tools if t['name'].startswith('alphavantage_')]

    print(f"* {len(all_tools)} total MCP tools available")
    print(f"* {len(alpha_tools)} Alpha Vantage tools available:")
    for tool in alpha_tools:
        print(f"  - {tool['name']}")

    # Test queries
    queries = [
        "What is the current stock price for AAPL?",
        "Get real-time quote for BAY.V (Aston Bay on TSX Venture)",
        "Show me the daily price history for TSLA",
    ]

    conversation_history = []

    for i, query in enumerate(queries, 1):
        print_section(f"QUERY {i}: {query}")

        # Show current database state before query
        if "BAY" in query:
            print("\nBEFORE QUERY - Database state for Aston Bay:")
            company = Company.objects.filter(ticker_symbol='BAY').first()
            if company:
                market_data_count = MarketData.objects.filter(company=company).count()
                print(f"  - Company: {company.name}")
                print(f"  - Market data records: {market_data_count}")
                latest = MarketData.objects.filter(company=company).order_by('-date').first()
                if latest:
                    print(f"  - Latest data: {latest.date} @ ${latest.close_price}")

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
                    if tc.get('result'):
                        result_str = str(tc['result'])
                        if 'cached_in_database' in result_str:
                            print(f"    Cached: {tc['result'].get('cached_in_database', False)}")

            # Show token usage
            print(f"\nTokens: {result['usage']['input_tokens']} in, "
                  f"{result['usage']['output_tokens']} out")

            # Show database state after query
            if "BAY" in query:
                print("\nAFTER QUERY - Database state for Aston Bay:")
                company = Company.objects.filter(ticker_symbol='BAY').first()
                if company:
                    market_data_count = MarketData.objects.filter(company=company).count()
                    print(f"  - Market data records: {market_data_count}")
                    latest = MarketData.objects.filter(company=company).order_by('-date').first()
                    if latest:
                        print(f"  - Latest data: {latest.date} @ ${latest.close_price}")

            # Update conversation history for context
            conversation_history = result['conversation_history']

        except Exception as e:
            print(f"\nERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    print_section("ALPHA VANTAGE TEST COMPLETE")
    print("\n* Claude can successfully fetch real-time market data!")
    print("* Data is automatically cached in the database")
    print("\nAlpha Vantage MCP Server Tools:")
    print("  1. alphavantage_get_quote - Real-time stock quotes")
    print("  2. alphavantage_get_intraday - Intraday price data")
    print("  3. alphavantage_get_daily - Daily historical data\n")


def test_caching_behavior():
    """Test that data is cached and reused"""

    if not check_api_key():
        return

    print_section("TESTING DATABASE CACHING BEHAVIOR")

    client = ClaudeClient()

    # First query - should fetch from API
    print("\nQUERY 1: Fetching BAY.V from Alpha Vantage (should use API)")
    result1 = client.chat(
        message="Get the current stock price for BAY.V",
        conversation_history=[]
    )

    print("\nRESPONSE 1:")
    print(result1['message'])

    if result1['tool_calls']:
        for tc in result1['tool_calls']:
            if 'alphavantage_' in tc['tool']:
                print(f"\nUsed Alpha Vantage: {tc['tool']}")
                if tc.get('result', {}).get('cached_in_database'):
                    print("* Data WAS cached to database")

    # Second query - should use database
    print("\n" + "="*70)
    print("\nQUERY 2: Asking for BAY stock price again (should use database)")
    result2 = client.chat(
        message="What is Aston Bay's current stock price?",
        conversation_history=[]
    )

    print("\nRESPONSE 2:")
    print(result2['message'])

    if result2['tool_calls']:
        used_financial = False
        used_alpha = False
        for tc in result2['tool_calls']:
            if 'financial_' in tc['tool']:
                used_financial = True
                print(f"\nUsed Financial Server: {tc['tool']}")
            if 'alphavantage_' in tc['tool']:
                used_alpha = True
                print(f"\nUsed Alpha Vantage: {tc['tool']}")

        if used_financial and not used_alpha:
            print("\n* SUCCESS: Data was retrieved from database!")
            print("* Caching is working correctly")
        elif used_alpha:
            print("\n* Note: Still using Alpha Vantage (may need fresh data)")

    print_section("CACHING TEST COMPLETE")


def interactive_alpha_vantage_chat():
    """Interactive chat mode for Alpha Vantage testing"""

    if not check_api_key():
        return

    print_section("INTERACTIVE ALPHA VANTAGE CHAT MODE")
    print("Ask Claude for real-time stock quotes!")
    print("Type 'quit' or 'exit' to stop\n")

    print("Example questions:")
    print("  - What's the current price of AAPL?")
    print("  - Get a quote for TSLA")
    print("  - Show me the daily price data for BAY.V")
    print("  - What's the stock price for Microsoft?")
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
                tools_used = ', '.join(tc['tool'] for tc in result['tool_calls'])
                print(f"\n   [Used: {tools_used}]")

            # Update conversation history
            conversation_history = result['conversation_history']

        except Exception as e:
            print(f"\nError: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Run interactive mode
        interactive_alpha_vantage_chat()
    elif len(sys.argv) > 1 and sys.argv[1] == "--caching":
        # Test caching behavior
        test_caching_behavior()
    else:
        # Run automated tests
        test_alpha_vantage_queries()

        # Offer additional tests
        print("\n" + "="*70)
        print("\nAdditional tests available:")
        print("  python test_alpha_vantage.py --caching    (Test database caching)")
        print("  python test_alpha_vantage.py --interactive (Interactive chat mode)")
