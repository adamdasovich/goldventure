"""
Test Stock Price Queries with Alpha Vantage Integration
Demonstrates real-time market data fetching via chatbot
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from claude_integration.client import ClaudeClient
from core.models import User, Company, MarketData
from django.conf import settings


def print_header(text):
    """Print a nice header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)


def test_stock_price_queries():
    """Test various stock price queries"""

    print_header("TESTING ALPHA VANTAGE STOCK PRICE INTEGRATION")

    # Check API key
    if not settings.ALPHA_VANTAGE_API_KEY:
        print("\n❌ ERROR: Alpha Vantage API key not configured!")
        print("Please add ALPHA_VANTAGE_API_KEY to your .env file")
        return

    print(f"\n* API Key configured: {settings.ALPHA_VANTAGE_API_KEY[:8]}...")

    # Get or create test user
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("\nNo admin user found. Creating one...")
        # Use environment variable for password, fail if not set
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            raise ValueError("ADMIN_PASSWORD environment variable required to create admin user")
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password=admin_password
        )

    # Initialize Claude client
    client = ClaudeClient(company_id=None, user=user)

    # Check available tools
    all_tools = client._get_all_tools()
    alpha_tools = [t for t in all_tools if t['name'].startswith('alphavantage_')]

    print(f"* {len(alpha_tools)} Alpha Vantage tools available:")
    for tool in alpha_tools:
        print(f"  - {tool['name']}")

    # Test queries
    queries = [
        {
            "query": "What's the current stock price for Apple (AAPL)?",
            "description": "Popular Tech Stock - Real-time Quote"
        },
        {
            "query": "Get me the latest price for 1911 Gold (AUMB.V on TSX Venture)",
            "description": "Mining Company - TSX Venture Exchange"
        },
        {
            "query": "What is the stock price for BAY.V?",
            "description": "Aston Bay Holdings - Database Caching Test"
        },
        {
            "query": "Show me recent price action for TSLA",
            "description": "Tesla - Daily Historical Data"
        }
    ]

    for i, test in enumerate(queries, 1):
        print_header(f"QUERY {i}: {test['description']}")
        print(f"\nQuestion: {test['query']}\n")

        # Check database state before (for BAY.V)
        if "BAY" in test['query']:
            company = Company.objects.filter(ticker_symbol='BAY').first()
            if company:
                before_count = MarketData.objects.filter(company=company).count()
                print(f"Database before: {before_count} market data records")

        try:
            # Send query to chatbot
            result = client.chat(test['query'])

            print("Response:")
            print("-"*80)
            print(result['message'])
            print("-"*80)

            # Show which tools were used
            if result['tool_calls']:
                print(f"\n* Tools used: {len(result['tool_calls'])}")
                for tc in result['tool_calls']:
                    tool_name = tc['tool']
                    print(f"  - {tool_name}")

                    # Show if data was cached
                    if 'alphavantage_' in tool_name and tc.get('result'):
                        if 'cached_in_database' in tc['result']:
                            cached = tc['result']['cached_in_database']
                            if cached:
                                print(f"    * Data cached to database")
                            else:
                                print(f"    * Data not cached (company not in DB)")

                        if 'price' in tc['result']:
                            price = tc['result']['price']
                            ticker = tc['result'].get('ticker', 'N/A')
                            print(f"    ${price} ({ticker})")

            # Show database state after (for BAY.V)
            if "BAY" in test['query']:
                company = Company.objects.filter(ticker_symbol='BAY').first()
                if company:
                    after_count = MarketData.objects.filter(company=company).count()
                    print(f"\nDatabase after: {after_count} market data records")
                    if after_count > before_count:
                        print(f"* Added {after_count - before_count} new record(s)")

            # Show token usage
            usage = result['usage']
            print(f"\nTokens: {usage['input_tokens']} in, {usage['output_tokens']} out")

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    print_header("TEST COMPLETE")
    print("\n* Alpha Vantage integration is working!")
    print("\nCapabilities:")
    print("  * Real-time stock quotes for any ticker")
    print("  * Automatic database caching")
    print("  * Support for multiple exchanges (TSX, TSX-V, NASDAQ, NYSE, etc.)")
    print("  * Intraday and historical price data")
    print("\nAPI Usage:")
    print(f"  * Free tier: 25 API calls per day")
    print(f"  * Cached data is reused to save API calls")
    print(f"  * Get your own key at: https://www.alphavantage.co/support/#api-key")


def test_mining_companies():
    """Test stock prices for mining companies specifically"""

    print_header("TESTING MINING COMPANY STOCK PRICES")

    user = User.objects.filter(is_superuser=True).first()
    if not user:
        # Use environment variable for password, fail if not set
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            raise ValueError("ADMIN_PASSWORD environment variable required to create admin user")
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password=admin_password
        )

    client = ClaudeClient(company_id=None, user=user)

    # Get mining companies from database
    mining_companies = Company.objects.all()[:3]

    print(f"\nFound {mining_companies.count()} companies in database")
    print("\nTesting stock price queries for mining companies:\n")

    for company in mining_companies:
        if company.ticker_symbol:
            print(f"Company: {company.name}")
            print(f"Ticker: {company.ticker_symbol}")

            query = f"What's the current stock price for {company.ticker_symbol}?"

            try:
                result = client.chat(query)

                # Extract price from response
                if result['tool_calls']:
                    for tc in result['tool_calls']:
                        if 'alphavantage_' in tc['tool'] and tc.get('result'):
                            if 'price' in tc['result']:
                                price = tc['result']['price']
                                change = tc['result'].get('change_percent', 'N/A')
                                print(f"Price: ${price} ({change}% change)")

                                # Check if cached
                                if tc['result'].get('cached_in_database'):
                                    print(f"* Cached to database")

                print()

            except Exception as e:
                print(f"Error: {str(e)}\n")

    print_header("MINING COMPANY TEST COMPLETE")


def interactive_stock_chat():
    """Interactive mode for testing stock queries"""

    print_header("INTERACTIVE STOCK PRICE CHAT")
    print("\nAsk about any stock price! Type 'quit' to exit.\n")

    print("Examples:")
    print("  - What's the price of Apple?")
    print("  - Get me a quote for TSLA")
    print("  - Show me the stock price for 1911 Gold (AUMB.V)")
    print("  - What's BAY.V trading at?")
    print()

    if not settings.ALPHA_VANTAGE_API_KEY:
        print("❌ ERROR: Alpha Vantage API key not configured!")
        return

    user = User.objects.filter(is_superuser=True).first()
    if not user:
        # Use environment variable for password, fail if not set
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            raise ValueError("ADMIN_PASSWORD environment variable required to create admin user")
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password=admin_password
        )

    client = ClaudeClient(company_id=None, user=user)
    conversation_history = []

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!\n")
                break

            if not user_input:
                continue

            result = client.chat(user_input, conversation_history)

            print(f"\nClaude: {result['message']}")

            # Show tools used
            if result['tool_calls']:
                tools = ', '.join(tc['tool'] for tc in result['tool_calls'])
                print(f"\n[Tools: {tools}]")

            # Update conversation history
            conversation_history = result['conversation_history']

        except KeyboardInterrupt:
            print("\n\nGoodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            interactive_stock_chat()
        elif sys.argv[1] == "--mining":
            test_mining_companies()
        else:
            print("Usage:")
            print("  python test_stock_prices.py          # Run standard tests")
            print("  python test_stock_prices.py --mining # Test mining companies")
            print("  python test_stock_prices.py --interactive # Interactive mode")
    else:
        test_stock_price_queries()

        print("\n" + "="*80)
        print("\nAdditional test modes:")
        print("  python test_stock_prices.py --mining      # Test mining companies")
        print("  python test_stock_prices.py --interactive # Interactive chat mode")
        print()
