"""
Industry Data MCP Server

Two datasets the assistant previously could not see at all:

* MetalPrice — spot prices for the ten metals the platform tracks. Nothing
  read this table, so the assistant could not answer "what is gold doing?"
  from our own data. Alpha Vantage could quote a company's shares but not a
  commodity.

* NewsArticle — 1,950 industry articles (Mining.com, Northern Miner and the
  like) behind the homepage feed. Every news tool pointed at NewsRelease,
  which is company press releases only, so industry coverage was invisible.

Both are industry-wide context rather than company-specific, which is why
they share a server.
"""

from datetime import timedelta
from typing import Dict, List

from django.db.models import Q
from django.utils import timezone

from core.models import MetalPrice, NewsArticle

# Accept what a person would actually type, not just the stored code.
METAL_ALIASES = {
    'gold': 'XAU', 'xau': 'XAU', 'au': 'XAU',
    'silver': 'XAG', 'xag': 'XAG', 'ag': 'XAG',
    'platinum': 'XPT', 'xpt': 'XPT', 'pt': 'XPT',
    'palladium': 'XPD', 'xpd': 'XPD', 'pd': 'XPD',
    'copper': 'CU', 'cu': 'CU',
    'nickel': 'NI', 'ni': 'NI',
    'lithium': 'LI', 'li': 'LI',
    'cobalt': 'CO', 'co': 'CO',
    'rare earth': 'REE', 'rare earths': 'REE', 'ree': 'REE',
    'uranium': 'U', 'u': 'U', 'u3o8': 'U',
}
METAL_NAMES = dict(MetalPrice.METAL_CHOICES)


class IndustryDataServer:
    """MCP server for metals prices and industry-wide news."""

    def __init__(self, company_id: int = None, user=None):
        self.company_id = company_id
        self.user = user

    def get_tool_definitions(self) -> List[Dict]:
        return [
            {
                "name": "industry_get_metal_prices",
                "description": (
                    "Current spot prices for the metals this platform tracks "
                    "(gold, silver, platinum, palladium, copper, nickel, "
                    "lithium, cobalt, rare earths, uranium), with the latest "
                    "daily change. Use for questions like 'what is gold "
                    "doing?', 'how has copper moved?', or when a valuation "
                    "needs today's metal price. Omit `metal` for all of them."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "metal": {
                            "type": "string",
                            "description": (
                                "Metal name or code, e.g. 'gold', 'XAU', "
                                "'copper'. Omit for every tracked metal."
                            ),
                        }
                    },
                    "required": [],
                },
            },
            {
                "name": "industry_metal_price_history",
                "description": (
                    "Daily price history for one metal, for trend or "
                    "correlation questions ('how has gold moved this "
                    "quarter?'). Returns dated closes plus the change over "
                    "the window."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "metal": {
                            "type": "string",
                            "description": "Metal name or code, e.g. 'gold'.",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Days of history (default 30, max 365).",
                            "default": 30,
                        },
                    },
                    "required": ["metal"],
                },
            },
            {
                "name": "industry_latest_news",
                "description": (
                    "Recent mining-industry news articles from outside "
                    "publications (Mining.com, Northern Miner and similar). "
                    "This is trade press about the sector — distinct from "
                    "company press releases, which the news_* and search_news_* "
                    "tools cover. Use for 'what is happening in the industry?' "
                    "or sector-level context."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "days_back": {
                            "type": "integer",
                            "description": "How far back to look (default 7).",
                            "default": 7,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max articles (default 20, max 50).",
                            "default": 20,
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "industry_search_news",
                "description": (
                    "Search industry news articles by keyword across titles "
                    "and summaries — e.g. 'lithium prices', 'permitting', "
                    "'M&A'. Searches trade press, not company releases."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Word or phrase to search for.",
                        },
                        "days_back": {
                            "type": "integer",
                            "description": "Limit to the last N days (default 90).",
                            "default": 90,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Max articles (default 20, max 50).",
                            "default": 20,
                        },
                    },
                    "required": ["keyword"],
                },
            },
        ]

    def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        if tool_name == "industry_get_metal_prices":
            return self._get_metal_prices(parameters)
        if tool_name == "industry_metal_price_history":
            return self._metal_price_history(parameters)
        if tool_name == "industry_latest_news":
            return self._latest_news(parameters)
        if tool_name == "industry_search_news":
            return self._search_news(parameters)
        return {
            "error": f"Unknown tool: {tool_name}",
            "available_tools": [t["name"] for t in self.get_tool_definitions()],
        }

    # ------------------------------------------------------------------ metals

    @staticmethod
    def _resolve_metal(raw):
        """A metal code from whatever the caller typed, or None."""
        key = (raw or "").strip().lower()
        return METAL_ALIASES.get(key)

    @staticmethod
    def _price_row(row):
        return {
            "metal": METAL_NAMES.get(row.metal, row.metal),
            "code": row.metal,
            "bid": float(row.bid_price),
            "ask": float(row.ask_price),
            "change": float(row.change_amount),
            "change_percent": float(row.change_percent),
            "high": float(row.high_price) if row.high_price is not None else None,
            "low": float(row.low_price) if row.low_price is not None else None,
            "unit": row.unit,
            "source": row.source,
            "as_of": row.scraped_at.isoformat(),
        }

    def _get_metal_prices(self, parameters: Dict) -> Dict:
        raw = parameters.get("metal")
        codes = list(METAL_NAMES)
        if raw:
            code = self._resolve_metal(raw)
            if not code:
                return {
                    "error": f"Unknown metal: {raw!r}",
                    "known_metals": sorted(set(METAL_ALIASES)),
                }
            codes = [code]

        prices = []
        for code in codes:
            row = (MetalPrice.objects.filter(metal=code)
                   .order_by("-scraped_at").first())
            if row:
                prices.append(self._price_row(row))

        if not prices:
            return {"found": False,
                    "message": "No metal prices stored for that selection."}
        return {"found": True, "count": len(prices), "prices": prices}

    def _metal_price_history(self, parameters: Dict) -> Dict:
        code = self._resolve_metal(parameters.get("metal"))
        if not code:
            return {
                "error": f"Unknown metal: {parameters.get('metal')!r}",
                "known_metals": sorted(set(METAL_ALIASES)),
            }
        days = max(1, min(int(parameters.get("days", 30) or 30), 365))
        since = timezone.now() - timedelta(days=days)

        rows = list(
            MetalPrice.objects.filter(metal=code, scraped_at__gte=since)
            .order_by("scraped_at")
        )
        if not rows:
            return {"found": False, "metal": METAL_NAMES.get(code, code),
                    "message": f"No prices stored in the last {days} days."}

        first, last = float(rows[0].bid_price), float(rows[-1].bid_price)
        return {
            "found": True,
            "metal": METAL_NAMES.get(code, code),
            "code": code,
            "days": days,
            "points": len(rows),
            "first": {"date": rows[0].scraped_at.date().isoformat(), "bid": first},
            "latest": {"date": rows[-1].scraped_at.date().isoformat(), "bid": last},
            "change": round(last - first, 2),
            "change_percent": round((last - first) / first * 100, 2) if first else 0,
            "history": [
                {"date": r.scraped_at.date().isoformat(), "bid": float(r.bid_price)}
                for r in rows
            ],
        }

    # -------------------------------------------------------------------- news

    @staticmethod
    def _article_row(a):
        return {
            "title": a.title,
            "url": a.url,
            "source": a.source.name if a.source_id else None,
            "published": a.published_at.date().isoformat() if a.published_at else None,
            "author": a.author or None,
            "summary": (a.summary or "")[:400] or None,
        }

    def _latest_news(self, parameters: Dict) -> Dict:
        days = max(1, min(int(parameters.get("days_back", 7) or 7), 365))
        limit = max(1, min(int(parameters.get("limit", 20) or 20), 50))
        since = timezone.now() - timedelta(days=days)

        qs = (NewsArticle.objects
              .filter(is_visible=True, published_at__gte=since)
              .select_related("source").order_by("-published_at")[:limit])
        rows = [self._article_row(a) for a in qs]
        return {
            "found": bool(rows),
            "date_range": f"Last {days} days",
            "count": len(rows),
            "articles": rows,
        }

    def _search_news(self, parameters: Dict) -> Dict:
        keyword = (parameters.get("keyword") or "").strip()
        if not keyword:
            return {"error": "keyword is required"}
        days = max(1, min(int(parameters.get("days_back", 90) or 90), 3650))
        limit = max(1, min(int(parameters.get("limit", 20) or 20), 50))
        since = timezone.now() - timedelta(days=days)

        qs = (NewsArticle.objects
              .filter(Q(title__icontains=keyword) | Q(summary__icontains=keyword),
                      is_visible=True, published_at__gte=since)
              .select_related("source").order_by("-published_at")[:limit])
        rows = [self._article_row(a) for a in qs]
        return {
            "found": bool(rows),
            "keyword": keyword,
            "date_range": f"Last {days} days",
            "count": len(rows),
            "articles": rows,
        }
