"""
Add sample market data and financing data for testing
"""

import os
import django
from datetime import date, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company, MarketData, Financing


def add_market_data():
    """Add sample market data for companies"""

    print("\n=== Adding Market Data ===\n")

    # Get companies
    aston_bay = Company.objects.filter(ticker_symbol='BAY').first()
    gold_1911 = Company.objects.filter(ticker_symbol='AUMB').first()

    if not aston_bay or not gold_1911:
        print("ERROR: Companies not found!")
        return

    # Clear existing market data
    MarketData.objects.all().delete()
    print("* Cleared existing market data")

    # Add market data for Aston Bay
    print(f"Adding market data for {aston_bay.name}...")

    MarketData.objects.create(
        company=aston_bay,
        date=date.today(),
        open_price=Decimal('0.17'),
        high_price=Decimal('0.19'),
        low_price=Decimal('0.17'),
        close_price=Decimal('0.18'),
        volume=125000
    )

    # Add historical data (30 days)
    for i in range(1, 31):
        past_date = date.today() - timedelta(days=i)
        close_variation = Decimal('0.18') + (Decimal(i % 5) - Decimal('2')) * Decimal('0.01')
        close = max(Decimal('0.15'), close_variation)

        MarketData.objects.create(
            company=aston_bay,
            date=past_date,
            open_price=close - Decimal('0.01'),
            high_price=close + Decimal('0.01'),
            low_price=close - Decimal('0.02'),
            close_price=close,
            volume=100000 + (i * 1000)
        )

    print(f"  * Added 31 days of market data for {aston_bay.ticker_symbol}")

    # Add market data for 1911 Gold
    print(f"\nAdding market data for {gold_1911.name}...")

    MarketData.objects.create(
        company=gold_1911,
        date=date.today(),
        open_price=Decimal('1.40'),
        high_price=Decimal('1.45'),
        low_price=Decimal('1.38'),
        close_price=Decimal('1.43'),
        volume=250000
    )

    # Add historical data (30 days)
    for i in range(1, 31):
        past_date = date.today() - timedelta(days=i)
        close_variation = Decimal('1.43') + (Decimal(i % 7) - Decimal('3')) * Decimal('0.05')
        close = max(Decimal('1.20'), close_variation)

        MarketData.objects.create(
            company=gold_1911,
            date=past_date,
            open_price=close - Decimal('0.03'),
            high_price=close + Decimal('0.05'),
            low_price=close - Decimal('0.05'),
            close_price=close,
            volume=200000 + (i * 2000)
        )

    print(f"  * Added 31 days of market data for {gold_1911.ticker_symbol}")


def add_financing_data():
    """Add sample financing data"""

    print("\n=== Adding Financing Data ===\n")

    # Get companies
    aston_bay = Company.objects.filter(ticker_symbol='BAY').first()
    gold_1911 = Company.objects.filter(ticker_symbol='AUMB').first()

    if not aston_bay or not gold_1911:
        print("ERROR: Companies not found!")
        return

    # Clear existing financing data
    Financing.objects.all().delete()
    print("* Cleared existing financing data")

    # Aston Bay financings
    print(f"Adding financings for {aston_bay.name}...")

    Financing.objects.create(
        company=aston_bay,
        financing_type='private_placement',
        status='closed',
        amount_raised_usd=Decimal('3500000'),  # $3.5M USD
        price_per_share=Decimal('0.15'),
        shares_issued=23333333,
        announced_date=date(2024, 10, 1),
        closing_date=date(2024, 10, 15)
    )

    Financing.objects.create(
        company=aston_bay,
        financing_type='private_placement',
        status='closed',
        amount_raised_usd=Decimal('2800000'),  # $2.8M USD
        price_per_share=Decimal('0.20'),
        shares_issued=14000000,
        announced_date=date(2024, 3, 10),
        closing_date=date(2024, 3, 20)
    )

    Financing.objects.create(
        company=aston_bay,
        financing_type='private_placement',
        status='closed',
        amount_raised_usd=Decimal('5000000'),  # $5.0M USD
        price_per_share=Decimal('0.25'),
        shares_issued=20000000,
        announced_date=date(2023, 8, 1),
        closing_date=date(2023, 8, 10)
    )

    print(f"  * Added 3 financings totaling $11.3M USD")

    # 1911 Gold financings
    print(f"\nAdding financings for {gold_1911.name}...")

    Financing.objects.create(
        company=gold_1911,
        financing_type='private_placement',
        status='closed',
        amount_raised_usd=Decimal('8500000'),  # $8.5M USD
        price_per_share=Decimal('1.25'),
        shares_issued=6800000,
        announced_date=date(2024, 10, 25),
        closing_date=date(2024, 11, 5)
    )

    Financing.objects.create(
        company=gold_1911,
        financing_type='bought_deal',
        status='closed',
        amount_raised_usd=Decimal('15000000'),  # $15M USD
        price_per_share=Decimal('1.50'),
        shares_issued=10000000,
        announced_date=date(2024, 6, 1),
        closing_date=date(2024, 6, 12)
    )

    Financing.objects.create(
        company=gold_1911,
        financing_type='private_placement',
        status='closed',
        amount_raised_usd=Decimal('6200000'),  # $6.2M USD
        price_per_share=Decimal('1.10'),
        shares_issued=5636364,
        announced_date=date(2023, 11, 20),
        closing_date=date(2023, 12, 1)
    )

    Financing.objects.create(
        company=gold_1911,
        financing_type='debt',
        status='closed',
        amount_raised_usd=Decimal('10000000'),  # $10M USD
        price_per_share=None,
        shares_issued=None,
        announced_date=date(2023, 5, 10),
        closing_date=date(2023, 5, 15)
    )

    print(f"  * Added 4 financings totaling $39.7M USD")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("  ADDING SAMPLE FINANCIAL DATA")
    print("="*70)

    add_market_data()
    add_financing_data()

    print("\n" + "="*70)
    print("  DATA ADDED SUCCESSFULLY!")
    print("="*70)
    print("\nYou can now ask Claude:")
    print("  - 'What is the stock price of Aston Bay?'")
    print("  - 'Compare market caps of all companies'")
    print("  - 'Show me all capital raises'")
    print("  - 'What is 1911 Gold's financing history?'")
    print()
