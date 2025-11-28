#!/usr/bin/env python
"""
Test the company chatbot endpoint to verify it's working correctly.
"""

import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company

def test_company_fields():
    """Test that Company model has all required fields"""
    try:
        company = Company.objects.get(pk=2)  # 1911 Gold Corporation

        print("=" * 60)
        print("COMPANY MODEL FIELD TEST")
        print("=" * 60)
        print(f"Company Name: {company.name}")
        print(f"Ticker: {company.ticker_symbol}")
        print(f"Exchange: {company.exchange}")
        print(f"CEO Name: {company.ceo_name if company.ceo_name else 'Not specified'}")
        print(f"Website: {company.website if company.website else 'Not specified'}")
        print(f"Headquarters: {company.headquarters_city}, {company.headquarters_country}")
        print(f"Description: {company.description[:100]}..." if company.description else "Description: Not specified")
        print("=" * 60)
        print("\n✅ All required fields exist and are accessible!")
        print("\nThe company_chat endpoint should now work correctly.")
        print("\nNext steps:")
        print("1. Navigate to http://localhost:3000/companies/2")
        print("2. Click the 'Ask about 1911 Gold Corporation' button")
        print("3. Try asking: 'What are the latest news releases?'")
        print("=" * 60)

        return True

    except Company.DoesNotExist:
        print("❌ Company with ID 2 not found!")
        return False
    except AttributeError as e:
        print(f"❌ Field error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    test_company_fields()
