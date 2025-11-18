"""
Quick test of metallurgy query
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from claude_integration.client import ClaudeClient

print("="*80)
print("TESTING METALLURGY QUERY")
print("="*80)

client = ClaudeClient()

query = "Can you tell me about the metallurgy at 1911 Gold's True North Complex?"

print(f"\nQuery: {query}\n")
print("-" * 80)

result = client.chat(message=query, max_tokens=2000)

print("\nClaude's Response:")
print(result['message'])

if result['tool_calls']:
    print(f"\n\nTools Used:")
    for tc in result['tool_calls']:
        print(f"  - {tc['tool']}")
        if 'error' in str(tc.get('result', '')):
            print(f"    ERROR: {tc['result']}")

print(f"\n\nTokens: {result['usage']['input_tokens']} in, {result['usage']['output_tokens']} out")
print("\n" + "="*80)
