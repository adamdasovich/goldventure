#!/usr/bin/env python3
"""
GoldVenture Platform - Security Fixes Script
=============================================
Run from the project root: python security_fixes.py

Implements fixes for audit findings:
  C1. Remove hardcoded admin token from CLAUDE.md
  H4. Remove fake random price changes in views.py  
  H6. Make Redis required in production (settings.py)
  H7. Fix Claude chat proxy error leakage (route.ts) - ALREADY APPLIED
  M6. Add CONN_HEALTH_CHECKS to database config (settings.py)
  M9. Make BACKEND_URL required in production (route.ts) - ALREADY APPLIED
  L5. Add db_backup.json to .gitignore
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
fixes_applied = []
fixes_failed = []

def safe_replace(filepath, old_text, new_text, description):
    """Replace text in a file, handling both LF and CRLF line endings."""
    full_path = PROJECT_ROOT / filepath
    if not full_path.exists():
        fixes_failed.append(f"{description}: File not found: {filepath}")
        return False
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if old_text in content:
        content = content.replace(old_text, new_text)
    elif old_text.replace('\n', '\r\n') in content:
        content = content.replace(old_text.replace('\n', '\r\n'), new_text.replace('\n', '\r\n'))
    else:
        fixes_failed.append(f"{description}: Text pattern not found in {filepath}")
        return False
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    fixes_applied.append(description)
    return True


# ============================================================================
# FIX C1: Remove hardcoded admin token from CLAUDE.md
# ============================================================================
print("\n🔴 C1: Removing hardcoded admin token from CLAUDE.md...")

claude_md = PROJECT_ROOT / 'CLAUDE.md'
if claude_md.exists():
    with open(claude_md, 'r', encoding='utf-8') as f:
        content = f.read()
    
    token = 'REDACTED_TOKEN'
    if token in content:
        # Replace the Admin Token line
        content = content.replace(
            f'**Admin Token:** `{token}`',
            '> **SECURITY:** Admin token is stored in the `ADMIN_API_TOKEN` environment variable on the server.\n> Never hardcode tokens in this file — it is committed to Git.'
        )
        # Replace the curl example with the token
        content = content.replace(
            f'curl -H "Authorization: Token {token}"',
            '# Use the token from your environment:\ncurl -H "Authorization: Token $ADMIN_API_TOKEN"'
        )
        
        with open(claude_md, 'w', encoding='utf-8') as f:
            f.write(content)
        
        fixes_applied.append('C1: Removed hardcoded admin token from CLAUDE.md')
        print("  ✅ Token removed from CLAUDE.md")
    else:
        print("  ⏭️  Token not found (may already be removed)")


# ============================================================================
# FIX H4: Remove fake random price changes in views.py
# ============================================================================
print("\n🟠 H4: Removing fake random price changes from views.py...")

views_path = PROJECT_ROOT / 'backend' / 'core' / 'views.py'
if views_path.exists():
    with open(views_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'random.uniform(-2.5, 2.5)' in content:
        # Replace the random price generation block
        content = content.replace(
            "import random\n                    results.append({\n"
            "                        'metal': info['name'],\n"
            "                        'symbol': info['symbol'],\n"
            "                        'price': fallback_prices[info['symbol']],\n"
            "                        'change_percent': round(random.uniform(-2.5, 2.5), 2),\n"
            "                        'unit': info['unit'],\n"
            "                        'currency': 'USD',\n"
            "                        'last_updated': datetime.now().isoformat(),\n"
            "                        'source': 'Estimated',\n"
            "                        'note': 'API limit reached'\n"
            "                    })",
            "results.append({\n"
            "                        'metal': info['name'],\n"
            "                        'symbol': info['symbol'],\n"
            "                        'price': fallback_prices[info['symbol']],\n"
            "                        'change_percent': None,  # Don't fabricate price changes\n"
            "                        'unit': info['unit'],\n"
            "                        'currency': 'USD',\n"
            "                        'last_updated': datetime.now().isoformat(),\n"
            "                        'source': 'Estimated (stale)',\n"
            "                        'stale': True,\n"
            "                        'note': 'Real-time data temporarily unavailable'\n"
            "                    })"
        )
        
        # Also try CRLF version
        if 'random.uniform(-2.5, 2.5)' in content:
            content = content.replace(
                "import random\r\n                    results.append({\r\n"
                "                        'metal': info['name'],\r\n"
                "                        'symbol': info['symbol'],\r\n"
                "                        'price': fallback_prices[info['symbol']],\r\n"
                "                        'change_percent': round(random.uniform(-2.5, 2.5), 2),\r\n"
                "                        'unit': info['unit'],\r\n"
                "                        'currency': 'USD',\r\n"
                "                        'last_updated': datetime.now().isoformat(),\r\n"
                "                        'source': 'Estimated',\r\n"
                "                        'note': 'API limit reached'\r\n"
                "                    })",
                "results.append({\r\n"
                "                        'metal': info['name'],\r\n"
                "                        'symbol': info['symbol'],\r\n"
                "                        'price': fallback_prices[info['symbol']],\r\n"
                "                        'change_percent': None,  # Don't fabricate price changes\r\n"
                "                        'unit': info['unit'],\r\n"
                "                        'currency': 'USD',\r\n"
                "                        'last_updated': datetime.now().isoformat(),\r\n"
                "                        'source': 'Estimated (stale)',\r\n"
                "                        'stale': True,\r\n"
                "                        'note': 'Real-time data temporarily unavailable'\r\n"
                "                    })"
            )
        
        if 'random.uniform' not in content:
            with open(views_path, 'w', encoding='utf-8') as f:
                f.write(content)
            fixes_applied.append('H4: Removed fake random price changes')
            print("  ✅ Fake random price changes removed")
        else:
            # Fallback: use regex approach
            import re
            pattern = r"import random\s*\n\s*results\.append\(\{[^}]*random\.uniform\(-2\.5,\s*2\.5\)[^}]*\}\)"
            replacement = """results.append({
                        'metal': info['name'],
                        'symbol': info['symbol'],
                        'price': fallback_prices[info['symbol']],
                        'change_percent': None,
                        'unit': info['unit'],
                        'currency': 'USD',
                        'last_updated': datetime.now().isoformat(),
                        'source': 'Estimated (stale)',
                        'stale': True,
                        'note': 'Real-time data temporarily unavailable'
                    })"""
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            if new_content != content:
                with open(views_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                fixes_applied.append('H4: Removed fake random price changes (regex)')
                print("  ✅ Fake random price changes removed (via regex)")
            else:
                fixes_failed.append('H4: Could not match random price pattern in views.py')
                print("  ❌ Could not find pattern to replace")
    else:
        print("  ⏭️  random.uniform not found (may already be fixed)")


# ============================================================================
# FIX H6 + M6: Redis required in production + CONN_HEALTH_CHECKS
# ============================================================================
print("\n🟠 H6: Making Redis required in production...")

settings_path = PROJECT_ROOT / 'backend' / 'config' / 'settings.py'
if settings_path.exists():
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changed = False
    
    # Add ImproperlyConfigured import if not present
    if 'ImproperlyConfigured' not in content:
        for old, new in [
            ('from dotenv import load_dotenv', 'from django.core.exceptions import ImproperlyConfigured\nfrom dotenv import load_dotenv'),
        ]:
            if old in content:
                content = content.replace(old, new, 1)
                changed = True
                break
    
    # Add Redis requirement - insert check before the existing Redis block
    if 'ImproperlyConfigured("REDIS_URL' not in content:
        # Find the line "if REDIS_URL and not DEBUG:"
        for variant in ['if REDIS_URL and not DEBUG:', 'if REDIS_URL and not DEBUG:\r\n']:
            if variant in content:
                nl = '\r\n' if '\r\n' in variant else '\n'
                insert_before = variant
                insert_text = (
                    f"if not DEBUG and not REDIS_URL:{nl}"
                    f"    raise ImproperlyConfigured(\"REDIS_URL is required in production for WebSocket and caching support\"){nl}"
                    f"{nl}"
                )
                content = content.replace(insert_before, insert_text + insert_before, 1)
                changed = True
                fixes_applied.append('H6: Redis now required in production')
                print("  ✅ Redis requirement added")
                break
    
    # Add CONN_HEALTH_CHECKS
    if 'CONN_HEALTH_CHECKS' not in content and 'CONN_MAX_AGE' in content:
        for variant in ["'CONN_MAX_AGE': 600,", "'CONN_MAX_AGE': 600,"]:
            if variant in content:
                nl = '\r\n' if '\r\n' in content[:1000] else '\n'
                content = content.replace(
                    variant,
                    f"{variant}{nl}        'CONN_HEALTH_CHECKS': True,  # Django 4.1+ — validates connections before reuse",
                    1
                )
                changed = True
                fixes_applied.append('M6: Added CONN_HEALTH_CHECKS to database config')
                print("  ✅ CONN_HEALTH_CHECKS added")
                break
    
    if changed:
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        print("  ⏭️  Settings already configured")


# ============================================================================
# FIX L5: Add db_backup.json to .gitignore
# ============================================================================
print("\n🔵 L5: Adding db_backup.json to .gitignore...")

gitignore_path = PROJECT_ROOT / '.gitignore'
if gitignore_path.exists():
    with open(gitignore_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'db_backup.json' not in content:
        nl = '\r\n' if '\r\n' in content else '\n'
        with open(gitignore_path, 'a', encoding='utf-8') as f:
            f.write(f"{nl}# Database backups (should never be committed){nl}db_backup.json{nl}backend/db_backup.json{nl}")
        fixes_applied.append('L5: Added db_backup.json to .gitignore')
        print("  ✅ Added to .gitignore")
    else:
        print("  ⏭️  Already in .gitignore")


# ============================================================================
# Clean up this script
# ============================================================================
# Remove the temporary fix_claude_md.py if it exists
fix_script = PROJECT_ROOT / 'fix_claude_md.py'
if fix_script.exists():
    fix_script.unlink()
    print("\n🧹 Removed temporary fix_claude_md.py")


# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 60)
print("SECURITY FIXES SUMMARY")
print("=" * 60)

if fixes_applied:
    print(f"\n✅ {len(fixes_applied)} fixes applied:")
    for fix in fixes_applied:
        print(f"   ✅ {fix}")

if fixes_failed:
    print(f"\n❌ {len(fixes_failed)} issues:")
    for fix in fixes_failed:
        print(f"   ❌ {fix}")

already_done = [
    "H7: Claude chat proxy error leakage (route.ts rewritten)",
    "M9: BACKEND_URL required (route.ts rewritten)",
    "C3: DOMPurify already implemented in frontend/lib/sanitize.ts",
]
print(f"\n✅ {len(already_done)} already applied (before this script):")
for fix in already_done:
    print(f"   ✅ {fix}")

print(f"""
{'=' * 60}
MANUAL STEPS STILL REQUIRED:
{'=' * 60}

🔴 CRITICAL — Do these NOW:
  1. ROTATE the admin API token on production server:
     ssh root@137.184.168.166
     cd /var/www/goldventure/backend && source venv/bin/activate
     python manage.py drf_create_token <admin_username> --reset

  2. ROTATE all API keys:
     - Anthropic: https://console.anthropic.com/settings/keys
     - AWS: https://console.aws.amazon.com/iam/
     - Alpha Vantage: https://www.alphavantage.co/support/#api-key
     - Twelve Data: https://twelvedata.com/account/api-keys
     Update backend/.env and server env vars with new keys

  3. PURGE old token from Git history (if repo was ever shared):
     pip install git-filter-repo
     git filter-repo --replace-text <(echo 'REDACTED_TOKEN==>REDACTED')

🟠 HIGH — This week:
  4. Install and configure CSP header:
     pip install django-csp
     # Add to settings.py MIDDLEWARE and CSP_* settings

  5. DEPLOY to production:
     git add -A && git commit -m "Security fixes from Feb 2026 audit" && git push
     ssh root@137.184.168.166
     cd /var/www/goldventure && git pull
     systemctl restart celery-worker celery-beat
     # Restart gunicorn if backend changes affect it

  6. Optionally delete this script after running:
     del security_fixes.py
""")
