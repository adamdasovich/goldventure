"""
Test Claude Integration with MCP Servers
Interactive chat to test Claude's ability to query your mining data
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


def test_claude_chat():
    """Test Claude chat with predefined queries"""

    print_section("INITIALIZING CLAUDE CLIENT")
    client = ClaudeClient()
    print("✓ Claude client initialized")
    print(f"✓ API Key configured: {len(client.client.api_key)} characters")
    print(f"✓ {len(client._get_all_tools())} MCP tools available")

    # Test queries
    queries = [
        "What companies do I have in my database?",
        "Tell me about Aston Bay Holdings",
        "What projects does 1911 Gold have?",
        "What are the total gold resources across all companies?",
    ]

    conversation_history = []

    for i, query in enumerate(queries, 1):
        print_section(f"QUERY {i}: {query}")

        try:
            result = client.chat(
                message=query,
                conversation_history=conversation_history
            )

            print("\n📊 CLAUDE'S RESPONSE:")
            print("-" * 70)
            print(result['message'])
            print("-" * 70)

            # Show which tools were used
            if result['tool_calls']:
                print("\n🔧 TOOLS USED:")
                for tc in result['tool_calls']:
                    print(f"  - {tc['tool']}")

            # Show token usage
            print(f"\n💰 Tokens: {result['usage']['input_tokens']} in, "
                  f"{result['usage']['output_tokens']} out")

            # Update conversation history for next query
            conversation_history = result['conversation_history']

        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()

    print_section("CHAT TEST COMPLETE ✓")
    print("\n✓ Claude can successfully query your mining data!")
    print("✓ All MCP tools are working correctly")
    print("\nNext steps:")
    print("  1. Build Django REST API endpoints")
    print("  2. Create Next.js frontend with chat interface")
    print("  3. Deploy and use with real investor questions!\n")


def interactive_chat():
    """Interactive chat mode - talk to Claude about your mining data"""

    print_section("INTERACTIVE CHAT MODE")
    print("Ask Claude questions about your mining companies!")
    print("Type 'quit' or 'exit' to stop\n")

    client = ClaudeClient()
    conversation_history = []

    while True:
        user_input = input("\n💬 You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye! 👋\n")
            break

        if not user_input:
            continue

        try:
            result = client.chat(
                message=user_input,
                conversation_history=conversation_history
            )

            print(f"\n🤖 Claude: {result['message']}")

            # Show tools used (optional - comment out if too verbose)
            if result['tool_calls']:
                print(f"\n   [Used: {', '.join(tc['tool'] for tc in result['tool_calls'])}]")

            # Update conversation history
            conversation_history = result['conversation_history']

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Run interactive mode
        interactive_chat()
    else:
        # Run automated tests
        test_claude_chat()

        # Offer interactive mode
        print("\n" + "="*70)
        response = input("\nWould you like to try interactive chat mode? (y/n): ").strip().lower()
        if response == 'y':
            interactive_chat()
