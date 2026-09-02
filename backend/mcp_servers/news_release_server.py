"""
News Release MCP Server
Provides tools for accessing company news releases from the database
"""

from typing import Dict, List
from datetime import datetime, timedelta
from django.db.models import Count, Max
from core.models import NewsRelease, Company


class NewsReleaseServer:
    """MCP Server for news release data"""

    def __init__(self, company_id: int = None, user=None):
        self.company_id = company_id
        self.user = user

    def get_tool_definitions(self) -> List[Dict]:
        """Return tool definitions for Claude"""
        return [
            {
                "name": "get_latest_news_releases",
                "description": "Get the latest news releases for a company. Returns title, date, URL, and summary if available. Use this when user asks about recent news, press releases, or latest announcements from a company.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Name of the mining company (e.g., '1911 Gold Corporation', 'Aston Bay Holdings')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of news releases to return (default 5, max 20)",
                            "default": 5
                        },
                        "days_back": {
                            "type": "integer",
                            "description": "Number of days to look back (default 180 days / 6 months)",
                            "default": 180
                        }
                    },
                    "required": ["company_name"]
                }
            },
            {
                "name": "search_news_releases",
                "description": "Search news releases by keyword or topic. Use this when user asks about specific topics in news (e.g., 'drilling results', 'financing', 'resource update').",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Name of the mining company"
                        },
                        "keyword": {
                            "type": "string",
                            "description": "Keyword to search for in news titles and URLs (e.g., 'drill', 'financing', 'resource')"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of results to return (default 10)",
                            "default": 10
                        }
                    },
                    "required": ["company_name", "keyword"]
                }
            },
            {
                "name": "get_news_by_date_range",
                "description": "Get news releases within a specific date range. Use when user asks about news from a specific time period.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Name of the mining company"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (defaults to today)"
                        }
                    },
                    "required": ["company_name", "start_date"]
                }
            },
            {
                "name": "get_recent_news_all_companies",
                "description": "Get recent news releases across ALL companies. Use when user asks what companies have news out recently, this week, or today. Returns companies grouped by name with their latest news titles and dates. Does NOT require a company name.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "days_back": {
                            "type": "integer",
                            "description": "Number of days to look back (default 7 for 'this week', use 1 for 'today', 30 for 'this month')",
                            "default": 7
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of companies to return (default 50)",
                            "default": 50
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "search_news_all_companies",
                "description": "Search news releases by keyword across ALL companies. Use when user asks about specific topics across the industry like NI 43-101, PEA, PFS, feasibility study, drill results, financing, resource estimate, etc. Does NOT require a company name. Returns matching news grouped by company.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Keyword to search for in news titles (e.g., 'PEA', 'NI 43-101', 'feasibility', 'drill results', 'resource estimate', 'financing')"
                        },
                        "days_back": {
                            "type": "integer",
                            "description": "Number of days to look back (default 30, use 7 for 'this week', 90 for 'this quarter')",
                            "default": 30
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default 50)",
                            "default": 50
                        }
                    },
                    "required": ["keyword"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute a tool by name"""

        if tool_name == "get_latest_news_releases":
            return self._get_latest_news(parameters)
        elif tool_name == "search_news_releases":
            return self._search_news(parameters)
        elif tool_name == "get_news_by_date_range":
            return self._get_news_by_date_range(parameters)
        elif tool_name == "get_recent_news_all_companies":
            return self._get_recent_news_all_companies(parameters)
        elif tool_name == "search_news_all_companies":
            return self._search_news_all_companies(parameters)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def _get_latest_news(self, parameters: Dict) -> Dict:
        """Get latest news releases for a company"""

        company_name = parameters.get('company_name')
        limit = min(parameters.get('limit', 5), 20)  # Max 20
        days_back = parameters.get('days_back', 180)

        try:
            # Find company
            company = Company.objects.filter(Company.name_q(company_name)).first()
            if not company:
                return {
                    "error": f"Company '{company_name}' not found",
                    "suggestion": "Try a different company name or check spelling"
                }

            # Get news releases
            cutoff_date = datetime.now().date() - timedelta(days=days_back)
            news_releases = NewsRelease.objects.filter(
                company=company,
                release_date__gte=cutoff_date
            ).order_by('-release_date')[:limit]

            if not news_releases:
                return {
                    "company": company.name,
                    "message": f"No news releases found in the last {days_back} days",
                    "news_releases": []
                }

            # Format results
            results = []
            for nr in news_releases:
                results.append({
                    "title": nr.title,
                    "date": nr.release_date.isoformat(),
                    "url": nr.url,
                    "type": nr.get_release_type_display(),
                    "summary": nr.summary or "No summary available",
                    "is_material": nr.is_material
                })

            return {
                "company": company.name,
                "count": len(results),
                "date_range": f"Last {days_back} days",
                "news_releases": results
            }

        except Exception as e:
            return {"error": f"Error retrieving news: {str(e)}"}

    def _search_news(self, parameters: Dict) -> Dict:
        """Search news releases by keyword"""

        company_name = parameters.get('company_name')
        keyword = parameters.get('keyword', '').lower()
        limit = min(parameters.get('limit', 10), 20)

        try:
            # Find company
            company = Company.objects.filter(Company.name_q(company_name)).first()
            if not company:
                return {
                    "error": f"Company '{company_name}' not found"
                }

            # Search in title and URL
            news_releases = NewsRelease.objects.filter(
                company=company
            ).filter(
                title__icontains=keyword
            ).order_by('-release_date')[:limit]

            if not news_releases:
                return {
                    "company": company.name,
                    "keyword": keyword,
                    "message": f"No news releases found matching '{keyword}'",
                    "news_releases": []
                }

            # Format results
            results = []
            for nr in news_releases:
                results.append({
                    "title": nr.title,
                    "date": nr.release_date.isoformat(),
                    "url": nr.url,
                    "type": nr.get_release_type_display(),
                    "summary": nr.summary or "No summary available"
                })

            return {
                "company": company.name,
                "keyword": keyword,
                "count": len(results),
                "news_releases": results
            }

        except Exception as e:
            return {"error": f"Error searching news: {str(e)}"}

    def _get_news_by_date_range(self, parameters: Dict) -> Dict:
        """Get news releases within a date range"""

        company_name = parameters.get('company_name')
        start_date_str = parameters.get('start_date')
        end_date_str = parameters.get('end_date', datetime.now().date().isoformat())

        try:
            # Parse dates
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            # Find company
            company = Company.objects.filter(Company.name_q(company_name)).first()
            if not company:
                return {
                    "error": f"Company '{company_name}' not found"
                }

            # Get news releases in date range
            news_releases = NewsRelease.objects.filter(
                company=company,
                release_date__gte=start_date,
                release_date__lte=end_date
            ).order_by('-release_date')

            # Format results
            results = []
            for nr in news_releases:
                results.append({
                    "title": nr.title,
                    "date": nr.release_date.isoformat(),
                    "url": nr.url,
                    "type": nr.get_release_type_display(),
                    "summary": nr.summary or "No summary available"
                })

            return {
                "company": company.name,
                "date_range": f"{start_date} to {end_date}",
                "count": len(results),
                "news_releases": results
            }

        except ValueError as e:
            return {"error": f"Invalid date format. Use YYYY-MM-DD: {str(e)}"}
        except Exception as e:
            return {"error": f"Error retrieving news: {str(e)}"}

    def _get_recent_news_all_companies(self, parameters: Dict) -> Dict:
        """Get recent news across all companies, grouped by company"""

        days_back = parameters.get('days_back', 7)
        limit = min(parameters.get('limit', 50), 100)

        try:
            cutoff_date = datetime.now().date() - timedelta(days=days_back)

            # Get companies that have news in the date range, with counts
            companies_with_news = (
                NewsRelease.objects
                .filter(release_date__gte=cutoff_date)
                .values('company__id', 'company__name', 'company__ticker_symbol', 'company__exchange')
                .annotate(
                    news_count=Count('id'),
                    latest_date=Max('release_date')
                )
                .order_by('-latest_date')[:limit]
            )

            if not companies_with_news:
                return {
                    "message": f"No companies have published news in the last {days_back} days",
                    "date_range": f"Last {days_back} days (since {cutoff_date.isoformat()})",
                    "companies": []
                }

            # For each company, get their recent news titles (up to 3 per company)
            results = []
            for company_data in companies_with_news:
                recent_news = (
                    NewsRelease.objects
                    .filter(
                        company_id=company_data['company__id'],
                        release_date__gte=cutoff_date
                    )
                    .order_by('-release_date')[:3]
                )

                news_items = [
                    {
                        "title": nr.title,
                        "date": nr.release_date.isoformat(),
                        "url": nr.url,
                    }
                    for nr in recent_news
                ]

                ticker = company_data['company__ticker_symbol'] or ''
                exchange = company_data['company__exchange'] or ''
                ticker_display = f"{ticker}.{exchange.upper()}" if ticker and exchange else ticker

                results.append({
                    "company": company_data['company__name'],
                    "ticker": ticker_display,
                    "news_count": company_data['news_count'],
                    "latest_date": company_data['latest_date'].isoformat(),
                    "recent_news": news_items,
                })

            return {
                "date_range": f"Last {days_back} days (since {cutoff_date.isoformat()})",
                "total_companies_with_news": len(results),
                "companies": results
            }

        except Exception as e:
            return {"error": f"Error retrieving cross-company news: {str(e)}"}

    def _search_news_all_companies(self, parameters: Dict) -> Dict:
        """Search news releases by keyword across all companies"""

        keyword = parameters.get('keyword', '').strip()
        days_back = parameters.get('days_back', 30)
        limit = min(parameters.get('limit', 50), 100)

        if not keyword:
            return {"error": "keyword is required"}

        try:
            cutoff_date = datetime.now().date() - timedelta(days=days_back)

            # Search in title across all companies
            news_releases = (
                NewsRelease.objects
                .filter(
                    release_date__gte=cutoff_date,
                    title__icontains=keyword
                )
                .select_related('company')
                .order_by('-release_date')[:limit]
            )

            if not news_releases:
                return {
                    "keyword": keyword,
                    "date_range": f"Last {days_back} days (since {cutoff_date.isoformat()})",
                    "message": f"No news releases found matching '{keyword}' in the last {days_back} days",
                    "total_results": 0,
                    "results": []
                }

            results = []
            for nr in news_releases:
                ticker = nr.company.ticker_symbol or ''
                exchange = nr.company.exchange or ''
                ticker_display = f"{ticker}.{exchange.upper()}" if ticker and exchange else ticker

                results.append({
                    "company": nr.company.name,
                    "ticker": ticker_display,
                    "title": nr.title,
                    "date": nr.release_date.isoformat(),
                    "url": nr.url,
                    "type": nr.get_release_type_display(),
                })

            return {
                "keyword": keyword,
                "date_range": f"Last {days_back} days (since {cutoff_date.isoformat()})",
                "total_results": len(results),
                "results": results
            }

        except Exception as e:
            return {"error": f"Error searching news across companies: {str(e)}"}
