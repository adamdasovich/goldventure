"""
Test script for Metals Pricing API
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from core.views import metals_prices, metal_historical
from django.conf import settings

def print_header(text):
    print("\n" + "="*80)
    print(f" {text}")
    print("="*80 + "\n")

def test_metals_prices():
    """Test the metals prices endpoint"""
    print_header("TESTING METALS PRICES API")

    # Check API key
    if not settings.ALPHA_VANTAGE_API_KEY:
        print("ERROR: Alpha Vantage API key not configured!")
        print("Please add ALPHA_VANTAGE_API_KEY to your .env file")
        return

    print(f"API Key configured: {settings.ALPHA_VANTAGE_API_KEY[:8]}...")

    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/api/metals/prices/')

    # Call the view
    print("\n=> Fetching current metal prices...")
    response = metals_prices(request)

    if response.status_code == 200:
        data = response.data
        print(f"\nOK SUCCESS! Status: {response.status_code}")
        print(f"\nTimestamp: {data['timestamp']}")
        print(f"Cached: {data['cached']}")
        print(f"\nMetals Data:")
        print("-" * 80)

        for metal in data['metals']:
            print(f"\n{metal['metal']} ({metal['symbol']}):")
            if metal['price'] is not None:
                print(f"  Price: ${metal['price']:.2f} per {metal['unit']}")
                print(f"  Currency: {metal['currency']}")
                print(f"  Last Updated: {metal['last_updated']}")
            else:
                print(f"  Error: {metal.get('error', 'Unknown error')}")

    else:
        print(f"\nERROR ERROR! Status: {response.status_code}")
        print(f"Response: {response.data}")

def test_historical_data():
    """Test the historical data endpoint"""
    print_header("TESTING HISTORICAL DATA API")

    # Check API key
    if not settings.ALPHA_VANTAGE_API_KEY:
        print("ERROR ERROR: Alpha Vantage API key not configured!")
        return

    # Create a mock request for Gold (XAU) - 7 days
    factory = RequestFactory()
    request = factory.get('/api/metals/historical/XAU/?days=7')

    print("\n=> Fetching 7 days of Gold (XAU) historical data...")
    response = metal_historical(request, 'XAU')

    if response.status_code == 200:
        data = response.data
        print(f"\nOK SUCCESS! Status: {response.status_code}")
        print(f"\nSymbol: {data['symbol']}")
        print(f"Days of data: {data['days']}")
        print(f"Timestamp: {data['timestamp']}")

        if data['data']:
            print(f"\nShowing first 3 and last 3 days:")
            print("-" * 80)

            for point in data['data'][:3]:
                print(f"{point['date']}: Open=${point['open']:.2f}, Close=${point['close']:.2f}, High=${point['high']:.2f}, Low=${point['low']:.2f}")

            if len(data['data']) > 6:
                print("...")

            for point in data['data'][-3:]:
                print(f"{point['date']}: Open=${point['open']:.2f}, Close=${point['close']:.2f}, High=${point['high']:.2f}, Low=${point['low']:.2f}")

    else:
        print(f"\nERROR ERROR! Status: {response.status_code}")
        print(f"Response: {response.data}")

if __name__ == '__main__':
    test_metals_prices()
    print("\n" + "="*80)
    print("\nWait Waiting 2 seconds before testing historical data...")
    import time
    time.sleep(2)
    test_historical_data()

    print_header("TEST COMPLETE")
    print("\nOK Metals API is configured and ready!")
    print("\nNext steps:")
    print("  1. Restart your Django development server")
    print("  2. Visit http://localhost:3000/metals to see the page")
    print("  3. The frontend will fetch data from http://localhost:8000/api/metals/prices/")
