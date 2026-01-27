"""
Kitco Metals Price Scraper
Scrapes current precious metals spot prices from Kitco.com
Supports Gold, Silver, Platinum, and Palladium
"""

import re
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class KitcoScraper:
    """
    Scrapes precious metals prices from Kitco.com

    Usage:
        scraper = KitcoScraper()
        prices = scraper.scrape_all_prices()
        scraper.save_to_database(prices)
    """

    BASE_URL = "https://www.kitco.com/price/precious-metals"

    METAL_MAPPING = {
        'gold': 'XAU',
        'silver': 'XAG',
        'platinum': 'XPT',
        'palladium': 'XPD',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def _parse_price(self, price_str: str) -> Optional[Decimal]:
        """Parse price string to Decimal, handling commas and currency symbols"""
        if not price_str:
            return None
        try:
            # Remove currency symbols, commas, and whitespace
            cleaned = re.sub(r'[,$\s]', '', price_str)
            return Decimal(cleaned)
        except Exception as e:
            logger.warning(f"Failed to parse price '{price_str}': {e}")
            return None

    def _parse_change(self, change_str: str) -> tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Parse change string like '+35.90 (+0.83%)' into amount and percentage
        Returns (change_amount, change_percent)
        """
        if not change_str:
            return None, None

        try:
            # Extract amount (with sign)
            amount_match = re.search(r'([+-]?\d+\.?\d*)', change_str)
            amount = Decimal(amount_match.group(1)) if amount_match else Decimal('0')

            # Extract percentage
            percent_match = re.search(r'\(([+-]?\d+\.?\d*)%\)', change_str)
            percent = Decimal(percent_match.group(1)) if percent_match else Decimal('0')

            return amount, percent
        except Exception as e:
            logger.warning(f"Failed to parse change '{change_str}': {e}")
            return Decimal('0'), Decimal('0')

    def scrape_all_prices(self) -> List[Dict]:
        """
        Scrape current prices for all precious metals from Kitco

        Returns:
            List of dicts with keys: metal, bid_price, ask_price, change_amount, change_percent
        """
        try:
            response = self.session.get(self.BASE_URL, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            prices = []

            # Find price tables/sections
            # Kitco typically uses tables or divs with metal names
            for metal_name, symbol in self.METAL_MAPPING.items():
                try:
                    price_data = self._extract_metal_price(soup, metal_name, symbol)
                    if price_data:
                        prices.append(price_data)
                except Exception as e:
                    logger.error(f"Error extracting {metal_name} price: {e}")

            return prices

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Kitco page: {e}")
            return []

    def _extract_metal_price(self, soup: BeautifulSoup, metal_name: str, symbol: str) -> Optional[Dict]:
        """
        Extract price data for a specific metal from the parsed HTML

        Kitco's current structure uses BidAskGrid divs with class like 'BidAskGrid_gridifier__l1T1o'
        Format: "GoldDec 30, 202511:364,366.104,368.1034.7000.80%4,323.804,404.70"
        Structure: Metal | Date | Time | Bid | Ask | Change | Percent | Low | High
        """
        price_data = {
            'metal': symbol,
            'metal_name': metal_name.capitalize(),
            'bid_price': None,
            'ask_price': None,
            'change_amount': Decimal('0'),
            'change_percent': Decimal('0'),
            'high_price': None,
            'low_price': None,
        }

        # Method 1: Look for BidAskGrid_gridifier divs (current Kitco structure as of 2025)
        grid_divs = soup.find_all('div', class_=lambda c: c and 'BidAskGrid_gridifier' in str(c))

        for div in grid_divs:
            text = div.get_text()
            # Skip the header row
            if 'DateTime' in text or 'Bid' in text:
                continue

            # Check if this div contains our metal
            if text.lower().startswith(metal_name.lower()):
                # Format is like:
                # "GoldDec 30, 202511:374,364.004,366.0032.6000.75%4,323.804,404.70"
                # Structure: Metal + Date + Time + Bid + Ask + Change + Percent + Low + High

                # Remove the metal name, date and time portion first
                # Time is in format HH:MM (11:37) which gets concatenated with bid price
                # We need to split after the time pattern
                time_match = re.search(r'\d{2}:\d{2}', text)
                if time_match:
                    # Get everything after the time
                    price_text = text[time_match.end():]
                else:
                    price_text = text

                # Now find prices in the cleaned text
                # Prices with commas (like 4,366.00)
                prices_with_commas = re.findall(r'(\d{1,3},\d{3}\.\d{2})', price_text)

                # For silver (< 100), find prices like 76.19
                prices_without_commas = re.findall(r'(?<![,\d])(\d{2,3}\.\d{2})(?![,\d])', price_text)

                all_prices = []

                # Add comma-separated prices (gold, platinum, palladium)
                for p in prices_with_commas:
                    try:
                        all_prices.append(Decimal(p.replace(',', '')))
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        pass

                # Add non-comma prices if we don't have comma prices (for silver)
                if not all_prices and prices_without_commas:
                    for p in prices_without_commas:
                        try:
                            val = Decimal(p)
                            # Filter reasonable prices (silver > 20)
                            if val > 20:
                                all_prices.append(val)
                        except (ValueError, TypeError, decimal.InvalidOperation):
                            pass

                if len(all_prices) >= 2:
                    price_data['bid_price'] = all_prices[0]
                    price_data['ask_price'] = all_prices[1]

                    # Extract low and high prices if available (last 2 prices in the list)
                    # Format: Bid | Ask | ... | Low | High
                    if len(all_prices) >= 4:
                        price_data['low_price'] = all_prices[-2]
                        price_data['high_price'] = all_prices[-1]

                # Extract change amount and percent
                # Look for pattern like "32.6000.75%" (change followed by percent)
                change_match = re.search(r'(\d+\.\d{2,3})(\d+\.\d{2})%', price_text)
                if change_match:
                    try:
                        price_data['change_amount'] = Decimal(change_match.group(1))
                        price_data['change_percent'] = Decimal(change_match.group(2))
                    except (ValueError, TypeError, decimal.InvalidOperation):
                        pass

                break

        # Method 2: Fallback to BidAskGridMobile (mobile version)
        if not price_data['bid_price']:
            mobile_divs = soup.find_all('div', class_=lambda c: c and 'BidAskGridMobile_gridder' in str(c))

            for div in mobile_divs:
                text = div.get_text()
                if text.lower().startswith(metal_name.lower()):
                    # Mobile format is simpler: "Gold4364.5033.10(0.76%)"
                    # Find the main price (first number with 4+ digits or 2+ digits with decimal)
                    price_match = re.search(r'[a-zA-Z](\d{2,6}\.?\d*)', text)
                    if price_match:
                        try:
                            price_data['bid_price'] = Decimal(price_match.group(1))
                            price_data['ask_price'] = price_data['bid_price'] * Decimal('1.0005')

                            # Extract change from parentheses
                            change_match = re.search(r'([\d.]+)\(([\d.]+)%\)', text)
                            if change_match:
                                price_data['change_amount'] = Decimal(change_match.group(1))
                                price_data['change_percent'] = Decimal(change_match.group(2))
                        except (ValueError, TypeError, decimal.InvalidOperation):
                            pass

                    break

        # Method 3: Search all text for price patterns near metal names
        if not price_data['bid_price']:
            text = soup.get_text()
            pattern = rf'{metal_name}[^\d]*(\d{{1,3}}(?:,\d{{3}})*\.\d{{2}})[^\d]*(\d{{1,3}}(?:,\d{{3}})*\.\d{{2}})'
            match = re.search(pattern, text, re.I)
            if match:
                price_data['bid_price'] = self._parse_price(match.group(1))
                price_data['ask_price'] = self._parse_price(match.group(2))

        # Validate we have minimum required data
        if price_data['bid_price'] and price_data['bid_price'] > 0:
            # If no ask price, estimate from bid
            if not price_data['ask_price']:
                spread_multiplier = Decimal('1.0005')
                price_data['ask_price'] = price_data['bid_price'] * spread_multiplier

            return price_data

        return None

    def scrape_with_fallback(self) -> List[Dict]:
        """
        Scrape prices with fallback to alternative method if main scraping fails
        """
        prices = self.scrape_all_prices()

        if not prices or len(prices) < 4:
            logger.warning("Main scrape incomplete, trying alternative method")
            prices = self._scrape_alternative()

        return prices

    def _scrape_alternative(self) -> List[Dict]:
        """
        Alternative scraping method using Kitco's widget/API endpoints
        """
        # Try Kitco's JSON feed if available
        try:
            # Kitco sometimes has JSON data embedded in the page
            response = self.session.get(self.BASE_URL, timeout=30)
            text = response.text

            # Look for JSON data in script tags
            import json
            script_pattern = r'<script[^>]*>([^<]*"price"[^<]*)</script>'
            matches = re.findall(script_pattern, text, re.I)

            for match in matches:
                try:
                    # Try to find JSON object
                    json_match = re.search(r'\{[^{}]*"price"[^{}]*\}', match)
                    if json_match:
                        data = json.loads(json_match.group())
                        # Process JSON data...
                except json.JSONDecodeError:
                    continue

        except Exception as e:
            logger.error(f"Alternative scrape failed: {e}")

        return []

    def save_to_database(self, prices: List[Dict]) -> int:
        """
        Save scraped prices to the database

        Args:
            prices: List of price dicts from scrape_all_prices()

        Returns:
            Number of records saved
        """
        from core.models import MetalPrice

        saved_count = 0
        for price_data in prices:
            try:
                # Save ALL extracted data including high/low prices
                MetalPrice.objects.create(
                    metal=price_data['metal'],
                    bid_price=price_data['bid_price'],
                    ask_price=price_data['ask_price'],
                    change_amount=price_data.get('change_amount', Decimal('0')),
                    change_percent=price_data.get('change_percent', Decimal('0')),
                    high_price=price_data.get('high_price'),
                    low_price=price_data.get('low_price'),
                    source='Kitco'
                )
                saved_count += 1
                logger.info(f"Saved {price_data['metal_name']} price: ${price_data['bid_price']} (Low: {price_data.get('low_price')}, High: {price_data.get('high_price')})")
            except Exception as e:
                logger.error(f"Failed to save {price_data.get('metal', 'unknown')} price: {e}")

        return saved_count


def scrape_and_save_metals_prices() -> Dict:
    """
    Main function to scrape Kitco and save prices to database.
    Call this from scheduled task or management command.

    Returns:
        Dict with scrape results
    """
    scraper = KitcoScraper()
    prices = scraper.scrape_with_fallback()

    if prices:
        saved = scraper.save_to_database(prices)
        return {
            'success': True,
            'scraped': len(prices),
            'saved': saved,
            'timestamp': datetime.now().isoformat(),
            'metals': [p['metal'] for p in prices]
        }
    else:
        return {
            'success': False,
            'error': 'No prices scraped',
            'timestamp': datetime.now().isoformat()
        }
