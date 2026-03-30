from django.db import models
from django.utils import timezone
from .users import Company




# ============================================================================
# MARKET DATA & INTELLIGENCE
# ============================================================================

class MarketData(models.Model):
    """Daily market data for companies"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='market_data')
    date = models.DateField()

    # Price data
    open_price = models.DecimalField(max_digits=10, decimal_places=4)
    high_price = models.DecimalField(max_digits=10, decimal_places=4)
    low_price = models.DecimalField(max_digits=10, decimal_places=4)
    close_price = models.DecimalField(max_digits=10, decimal_places=4)
    volume = models.BigIntegerField()

    # Change data (added 2026-01-22 to sync with StockPrice model)
    change_amount = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    change_percent = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    # Currency (added 2026-01-22)
    currency = models.CharField(max_length=3, default='CAD')

    # Source tracking (added 2026-01-22)
    source = models.CharField(max_length=50, default='Unknown')

    # Calculated
    market_cap_usd = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'market_data'
        unique_together = ['company', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['company', '-date']),
        ]




class CommodityPrice(models.Model):
    """Precious metals, base metals, and critical minerals prices"""
    COMMODITIES = [
        ('gold', 'Gold (USD/oz)'),
        ('silver', 'Silver (USD/oz)'),
        ('copper', 'Copper (USD/lb)'),
        ('lithium', 'Lithium Carbonate (USD/tonne)'),
        ('nickel', 'Nickel (USD/lb)'),
        ('cobalt', 'Cobalt (USD/lb)'),
        ('zinc', 'Zinc (USD/lb)'),
        ('lead', 'Lead (USD/lb)'),
        ('uranium', 'Uranium (USD/lb)'),
        ('rare_earths', 'Rare Earth Oxides (USD/kg)'),
    ]

    commodity = models.CharField(max_length=20, choices=COMMODITIES)
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'commodity_prices'
        unique_together = ['commodity', 'date']
        ordering = ['-date']


# ============================================================================
# COMMUNICATIONS & DOCUMENTS
# ============================================================================




# ============================================================================
# METALS PRICING
# ============================================================================

class MetalPrice(models.Model):
    """
    Stores historical precious metals and critical minerals prices.
    Updated twice daily via scheduled task.
    """
    METAL_CHOICES = [
        ('XAU', 'Gold'),
        ('XAG', 'Silver'),
        ('XPT', 'Platinum'),
        ('XPD', 'Palladium'),
        ('CU', 'Copper'),
        ('NI', 'Nickel'),
        ('LI', 'Lithium'),
        ('CO', 'Cobalt'),
        ('REE', 'Rare Earth Elements'),
        ('U', 'Uranium'),
    ]

    metal = models.CharField(max_length=3, choices=METAL_CHOICES)
    bid_price = models.DecimalField(max_digits=12, decimal_places=2)
    ask_price = models.DecimalField(max_digits=12, decimal_places=2)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    change_percent = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # Daily high/low prices (added 2026-01-22)
    high_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    low_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Source tracking
    source = models.CharField(max_length=50, default='Kitco')
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'metal_prices'
        ordering = ['-scraped_at', 'metal']
        indexes = [
            models.Index(fields=['metal', '-scraped_at']),
            models.Index(fields=['-scraped_at']),
        ]

    def __str__(self):
        return f"{self.get_metal_display()}: ${self.bid_price} ({self.scraped_at.strftime('%Y-%m-%d %H:%M')})"

    @property
    def mid_price(self):
        """Calculate mid-market price"""
        return (self.bid_price + self.ask_price) / 2

    @classmethod
    def get_latest_prices(cls):
        """Get the most recent price for each metal (single query)"""
        latest_prices = cls.objects.order_by('metal', '-scraped_at').distinct('metal')
        return {price.metal: price for price in latest_prices}




class StockPrice(models.Model):
    """
    Stores daily closing stock prices and volume for companies.
    Updated daily after market close (4:30 PM ET weekdays).
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='stock_prices')

    # Price data
    close_price = models.DecimalField(max_digits=12, decimal_places=4)
    volume = models.BigIntegerField(default=0)

    # Optional additional data if available
    open_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    high_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    low_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    # Change calculations
    change_amount = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    change_percent = models.DecimalField(max_digits=8, decimal_places=4, default=0)

    # Currency
    currency = models.CharField(max_length=3, default='CAD')  # Most TSX/TSXV stocks are CAD

    # Source tracking
    source = models.CharField(max_length=50, default='Alpha Vantage')
    date = models.DateField()  # The trading date
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_prices'
        ordering = ['-date', 'company__ticker_symbol']
        unique_together = ['company', 'date']  # One record per company per day
        indexes = [
            models.Index(fields=['company', '-date']),
            models.Index(fields=['-date']),
            models.Index(fields=['company', 'date']),
        ]

    def __str__(self):
        return f"{self.company.ticker_symbol}: ${self.close_price} ({self.date})"

    @classmethod
    def get_latest_prices(cls):
        """Get the most recent price for each company (single query)"""
        latest_prices = cls.objects.order_by('company_id', '-date').distinct('company_id').select_related('company')
        return {price.company.ticker_symbol: price for price in latest_prices}

    @classmethod
    def get_company_history(cls, company, days=30):
        """Get price history for a company"""
        from datetime import timedelta
        from django.utils import timezone

        start_date = timezone.now().date() - timedelta(days=days)
        return cls.objects.filter(
            company=company,
            date__gte=start_date
        ).order_by('date')

    @classmethod
    def get_price_on_date(cls, company, target_date):
        """Get the price for a specific company on a specific date"""
        return cls.objects.filter(
            company=company,
            date=target_date
        ).first()


# ============================================================================
# GLOSSARY MODEL
# ============================================================================

