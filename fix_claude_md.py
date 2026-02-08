"""Quick script to remove hardcoded token from CLAUDE.md"""
import os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CLAUDE.md')

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the hardcoded token section
old_text = '**Admin Token:** `REDACTED_TOKEN`'
new_text = ('> **SECURITY:** Admin token is stored in the `ADMIN_API_TOKEN` environment variable on the server.\n'
            '> Never hardcode tokens in this file — it is committed to Git.')

if old_text in content:
    content = content.replace(old_text, new_text)
    print(f"✅ Replaced hardcoded admin token reference")
else:
    print(f"❌ Token text not found - may already be removed")

# Also replace the curl example with the token
old_curl = 'curl -H "Authorization: Token REDACTED_TOKEN"'
new_curl = '# Use the token from your environment:\ncurl -H "Authorization: Token $ADMIN_API_TOKEN"'

if old_curl in content:
    content = content.replace(old_curl, new_curl)
    print(f"✅ Replaced hardcoded token in curl example")

# Also update the "Trigger Manual Scrape" section that references {token}
old_trigger = '-H "Authorization: Token {token}"'
new_trigger = '-H "Authorization: Token $ADMIN_API_TOKEN"'
if old_trigger in content:
    content = content.replace(old_trigger, new_trigger)
    print(f"✅ Updated trigger scrape token reference")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDone! Token has been removed from CLAUDE.md")
print("⚠️  IMPORTANT: You still need to rotate the token on the server!")
print("   Run: python manage.py drf_create_token <admin_username> --reset")
