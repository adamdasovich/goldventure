"""
Financial Data MCP Server
Provides tools for querying market data, financings, and investor information
"""

import logging
from typing import Dict, List, Any
from .base import BaseMCPServer
from django.db.models import Sum, Avg, Max, Min, Q, F, Count
from django.db.models.functions import TruncDate
from core.models import Company, Financing, Investor, MarketData, StockPrice
from datetime import datetime, timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class FinancialDataServer(BaseMCPServer):
    """
    MCP Server for financial and market data queries.
    Provides tools to query stock prices, financings, investors, and market analytics.
    """

    def _register_tools(self):
        """Register all financial data tools"""

        # Tool 1: Get current market data for a company
        self.register_tool(
            name="financial_get_market_data",
            description=(
                "Get current or recent market data for a mining company including "
                "stock price, market capitalization, volume, and shares outstanding."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name or ticker symbol"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days of historical data (default: 1 for latest)",
                        "default": 1
                    }
                },
                "required": ["company_name"]
            },
            handler=self._get_market_data
        )

        # Tool 2: List all financings
        self.register_tool(
            name="financial_list_financings",
            description=(
                "List capital raises and financings. Can filter by company, "
                "financing type, or date range. Shows amount raised, price per share, and date."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Filter by company name (partial match)"
                    },
                    "financing_type": {
                        "type": "string",
                        "description": "Filter by type: private_placement, public_offering, debt, royalty, other"
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "Minimum amount raised (in millions)"
                    },
                    "recent_only": {
                        "type": "boolean",
                        "description": "Only show financings from last 12 months",
                        "default": False
                    }
                },
                "required": []
            },
            handler=self._list_financings
        )

        # Tool 3: Get financing summary for a company
        self.register_tool(
            name="financial_get_company_financings",
            description=(
                "Get complete financing history and summary for a specific company. "
                "Shows total capital raised, number of financings, average raise size, and details."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name or ticker symbol"
                    }
                },
                "required": ["company_name"]
            },
            handler=self._get_company_financings
        )

        # Tool 4: List investors
        self.register_tool(
            name="financial_list_investors",
            description=(
                "List institutional and major investors in junior mining companies. "
                "Can filter by investor type or minimum investment."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "investor_type": {
                        "type": "string",
                        "description": "Filter by type: institutional, retail, strategic, insider"
                    },
                    "min_ownership": {
                        "type": "number",
                        "description": "Minimum ownership percentage"
                    }
                },
                "required": []
            },
            handler=self._list_investors
        )

        # Tool 5: Market analytics - compare companies
        self.register_tool(
            name="financial_compare_market_caps",
            description=(
                "Compare market capitalizations and valuations across all mining companies. "
                "Returns ranking by market cap, enterprise value metrics, and relative comparisons."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "sort_by": {
                        "type": "string",
                        "description": "Sort by: market_cap, price, volume",
                        "default": "market_cap"
                    }
                },
                "required": []
            },
            handler=self._compare_market_caps
        )

        # Tool 6: Financing analytics
        self.register_tool(
            name="financial_financing_analytics",
            description=(
                "Get aggregate financing statistics and trends across all companies. "
                "Shows total capital raised, average deal size, financing trends by type."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "period_months": {
                        "type": "integer",
                        "description": "Period to analyze in months (default: 12)",
                        "default": 12
                    }
                },
                "required": []
            },
            handler=self._financing_analytics
        )

    # =============================================================================
    # TOOL HANDLERS
    # =============================================================================

    def _get_market_data(self, company_name: str, days: int = 1) -> Dict:
        """Get market data for a company from MarketData or StockPrice tables"""
        try:
            # Find company
            company = Company.objects.filter(
                Q(name__icontains=company_name) | Q(ticker_symbol__iexact=company_name)
            ).first()

            if not company:
                return {"error": f"Company '{company_name}' not found"}

            # Try MarketData first, then fall back to StockPrice
            market_data = MarketData.objects.filter(
                company=company
            ).order_by('-date')[:days]

            source_table = "MarketData"

            # If no MarketData, try StockPrice table
            if not market_data.exists():
                market_data = StockPrice.objects.filter(
                    company=company
                ).order_by('-date')[:days]
                source_table = "StockPrice"

            if not market_data.exists():
                return {
                    "company": company.name,
                    "ticker": company.ticker_symbol,
                    "message": "No market data available"
                }

            data_list = []
            for md in market_data:
                entry = {
                    "date": md.date.isoformat(),
                    "open": float(md.open_price) if md.open_price else None,
                    "high": float(md.high_price) if md.high_price else None,
                    "low": float(md.low_price) if md.low_price else None,
                    "close": float(md.close_price),
                    "volume": md.volume
                }
                # Include change data if available
                if hasattr(md, 'change_amount') and md.change_amount:
                    entry["change"] = float(md.change_amount)
                if hasattr(md, 'change_percent') and md.change_percent:
                    entry["change_percent"] = float(md.change_percent)
                if hasattr(md, 'currency'):
                    entry["currency"] = md.currency
                data_list.append(entry)

            latest = market_data.first()

            result = {
                "company": company.name,
                "ticker": company.ticker_symbol,
                "exchange": company.exchange,
                "source": source_table,
                "latest": {
                    "date": latest.date.isoformat(),
                    "open": float(latest.open_price) if latest.open_price else None,
                    "high": float(latest.high_price) if latest.high_price else None,
                    "low": float(latest.low_price) if latest.low_price else None,
                    "close": float(latest.close_price),
                    "volume": latest.volume
                },
                "historical": data_list if days > 1 else None
            }

            # Add change data to latest if available
            if hasattr(latest, 'change_amount') and latest.change_amount:
                result["latest"]["change"] = float(latest.change_amount)
            if hasattr(latest, 'change_percent') and latest.change_percent:
                result["latest"]["change_percent"] = float(latest.change_percent)
            if hasattr(latest, 'currency'):
                result["latest"]["currency"] = latest.currency

            return result

        except Exception as e:
            logger.error(f"Financial data error: {str(e)}")
            return {"error": "Failed to retrieve financial data. Please try again."}

    def _list_financings(self, company_name: str = None, financing_type: str = None,
                        min_amount: float = None, recent_only: bool = False) -> Dict:
        """List financings with optional filters"""
        try:
            queryset = Financing.objects.all()

            # Apply filters
            if company_name:
                queryset = queryset.filter(
                    Q(company__name__icontains=company_name) |
                    Q(company__ticker_symbol__iexact=company_name)
                )

            if financing_type:
                queryset = queryset.filter(financing_type=financing_type)

            if min_amount:
                queryset = queryset.filter(amount_raised_usd__gte=min_amount * 1_000_000)

            if recent_only:
                one_year_ago = datetime.now().date() - timedelta(days=365)
                queryset = queryset.filter(closing_date__gte=one_year_ago)

            financings = queryset.select_related('company').order_by('-closing_date')

            result = {
                "total_count": financings.count(),
                "financings": []
            }

            for f in financings[:50]:  # Limit to 50 results
                result["financings"].append({
                    "company": f.company.name,
                    "ticker": f.company.ticker_symbol,
                    "type": f.financing_type,
                    "amount_raised_usd": float(f.amount_raised_usd),
                    "price_per_share": float(f.price_per_share) if f.price_per_share else None,
                    "date": f.closing_date.isoformat(),
                })

            # Add summary
            if financings.exists():
                total_raised = financings.aggregate(total=Sum('amount_raised_usd'))['total']
                avg_raise = financings.aggregate(avg=Avg('amount_raised_usd'))['avg']

                result["summary"] = {
                    "total_raised": float(total_raised or 0),
                    "average_raise": float(avg_raise or 0),
                    "currency": "USD"
                }

            return result

        except Exception as e:
            logger.error(f"Financial data error: {str(e)}")
            return {"error": "Failed to retrieve financial data. Please try again."}

    def _get_company_financings(self, company_name: str) -> Dict:
        """Get complete financing history for a company"""
        try:
            # Find company
            company = Company.objects.filter(
                Q(name__icontains=company_name) | Q(ticker_symbol__iexact=company_name)
            ).first()

            if not company:
                return {"error": f"Company '{company_name}' not found"}

            financings = Financing.objects.filter(
                company=company
            ).order_by('-closing_date')

            if not financings.exists():
                return {
                    "company": company.name,
                    "ticker": company.ticker_symbol,
                    "message": "No financing history available"
                }

            # Calculate summary
            total_raised = financings.aggregate(total=Sum('amount_raised_usd'))['total']
            avg_raise = financings.aggregate(avg=Avg('amount_raised_usd'))['avg']

            # Count by type
            type_breakdown = {}
            for f_type in financings.values('financing_type').annotate(
                count=Count('id'),
                total=Sum('amount_raised_usd')
            ):
                type_breakdown[f_type['financing_type']] = {
                    "count": f_type['count'],
                    "total_raised": float(f_type['total'])
                }

            return {
                "company": company.name,
                "ticker": company.ticker_symbol,
                "summary": {
                    "total_financings": financings.count(),
                    "total_raised": float(total_raised or 0),
                    "average_raise": float(avg_raise or 0),
                    "currency": "USD"
                },
                "by_type": type_breakdown,
                "financings": [
                    {
                        "type": f.financing_type,
                        "amount": float(f.amount_raised_usd),
                        "price_per_share": float(f.price_per_share) if f.price_per_share else None,
                        "date": f.closing_date.isoformat()
                    }
                    for f in financings
                ]
            }

        except Exception as e:
            logger.error(f"Financial data error: {str(e)}")
            return {"error": "Failed to retrieve financial data. Please try again."}

    def _list_investors(self, investor_type: str = None, min_ownership: float = None) -> Dict:
        """List investors with optional filters"""
        try:
            queryset = Investor.objects.all()

            if investor_type:
                queryset = queryset.filter(investor_type=investor_type)

            if min_ownership:
                queryset = queryset.filter(ownership_percent__gte=min_ownership)

            investors = queryset.order_by('-ownership_percent')

            return {
                "total_count": investors.count(),
                "investors": [
                    {
                        "name": inv.name,
                        "type": inv.investor_type,
                        "ownership_percent": float(inv.ownership_percent) if inv.ownership_percent else None,
                        "shares_held": inv.shares_held,
                        "contact": inv.contact_email if inv.contact_email else None
                    }
                    for inv in investors[:50]  # Limit to 50
                ]
            }

        except Exception as e:
            logger.error(f"Financial data error: {str(e)}")
            return {"error": "Failed to retrieve financial data. Please try again."}

    def _compare_market_caps(self, sort_by: str = "market_cap") -> Dict:
        """Compare market capitalizations across companies"""
        try:
            # Get latest market data for each company
            companies = Company.objects.filter(is_active=True)

            comparisons = []
            for company in companies:
                latest_data = MarketData.objects.filter(
                    company=company
                ).order_by('-date').first()

                if latest_data:
                    comparisons.append({
                        "company": company.name,
                        "ticker": company.ticker_symbol,
                        "price": float(latest_data.close_price),
                        "volume": latest_data.volume,
                        "date": latest_data.date.isoformat()
                    })

            # Sort
            if sort_by == "price":
                comparisons.sort(key=lambda x: x["price"], reverse=True)
            elif sort_by == "volume":
                comparisons.sort(key=lambda x: x["volume"], reverse=True)
            else:
                # Default to price sorting if no market cap available
                comparisons.sort(key=lambda x: x["price"], reverse=True)

            # Add rankings
            for idx, comp in enumerate(comparisons, 1):
                comp["rank"] = idx

            return {
                "total_companies": len(comparisons),
                "sorted_by": sort_by if sort_by != "market_cap" else "price",
                "companies": comparisons
            }

        except Exception as e:
            logger.error(f"Financial data error: {str(e)}")
            return {"error": "Failed to retrieve financial data. Please try again."}

    def _financing_analytics(self, period_months: int = 12) -> Dict:
        """Get financing analytics and trends"""
        try:
            # Date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=period_months * 30)

            financings = Financing.objects.filter(
                closing_date__gte=start_date,
                closing_date__lte=end_date
            )

            if not financings.exists():
                return {
                    "period": f"{period_months} months",
                    "message": "No financings in this period"
                }

            # Aggregate statistics
            total_raised = financings.aggregate(total=Sum('amount_raised_usd'))['total']
            avg_raise = financings.aggregate(avg=Avg('amount_raised_usd'))['avg']
            max_raise = financings.aggregate(max=Max('amount_raised_usd'))['max']
            min_raise = financings.aggregate(min=Min('amount_raised_usd'))['min']

            # By type
            by_type = {}
            for f_type in financings.values('financing_type').annotate(
                count=Count('id'),
                total=Sum('amount_raised_usd')
            ).order_by('-total'):
                by_type[f_type['financing_type']] = {
                    "count": f_type['count'],
                    "total_raised": float(f_type['total']),
                    "percentage": float(f_type['total']) / float(total_raised) * 100
                }

            # Top companies by capital raised
            top_companies = financings.values(
                'company__name', 'company__ticker_symbol'
            ).annotate(
                total=Sum('amount_raised_usd'),
                count=Count('id')
            ).order_by('-total')[:5]

            return {
                "period": {
                    "months": period_months,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {
                    "total_financings": financings.count(),
                    "total_raised": float(total_raised),
                    "average_raise": float(avg_raise),
                    "largest_raise": float(max_raise),
                    "smallest_raise": float(min_raise),
                    "currency": "USD"
                },
                "by_type": by_type,
                "top_companies": [
                    {
                        "company": tc['company__name'],
                        "ticker": tc['company__ticker_symbol'],
                        "total_raised": float(tc['total']),
                        "number_of_raises": tc['count']
                    }
                    for tc in top_companies
                ]
            }

        except Exception as e:
            logger.error(f"Financial data error: {str(e)}")
            return {"error": "Failed to retrieve financial data. Please try again."}
