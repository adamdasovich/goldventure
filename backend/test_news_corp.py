"""
Test News Release Tool with "Corp" variation
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from claude_integration.client import ClaudeClient
from core.models import User

# Get or create test user
user = User.objects.filter(is_superuser=True).first()

if not user:
    print("No admin user found. Creating one...")
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

# Test the chatbot
print("="*80)
print("TESTING NEWS RELEASE TOOL - Corp Variation")
print("="*80)

query = "Can you give me a description of the last 5 news releases for 1911 Gold Corp?"

print(f"\nQuery: {query}\n")
print("Response:")
print("-"*80)

result = client.chat(query)
print(result['message'])

# Show tool calls
if result['tool_calls']:
    print("\n" + "="*80)
    print(f"Tool calls made: {len(result['tool_calls'])}")
    print("="*80)
    for i, tool_call in enumerate(result['tool_calls'], 1):
        print(f"\n{i}. {tool_call['tool']}")
        print(f"   Input: {tool_call['input']}")
        if 'news_releases' in tool_call.get('result', {}):
            print(f"   Result: {len(tool_call['result']['news_releases'])} news releases")
else:
    print("\n" + "="*80)
    print("WARNING: No tool calls made!")
    print("="*80)

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
