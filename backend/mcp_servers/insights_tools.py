"""
Insights Tools MCP Server
=========================

Analytics tools that turn the platform's historical data into investor-facing
insight. Every tool here is callable by the AI assistant.

Tools in this module
--------------------
1.  insights_compare_stock_performance - rank % price moves across companies
2.  insights_catalyst_impact           - event study: how news moves a stock
6.  insights_project_due_diligence     - RAG Q&A across a company's reports
7.  insights_resource_growth           - resource-estimate evolution over time
8.  insights_economic_rerate           - re-rate a PEA/FS at today's gold price
11. insights_daily_briefing            - per-watchlist digest of recent activity

(Tool numbers match the product-planning list; #3/#4/#5/#10 land in a later
batch, #9 was dropped by request.)

Design notes
------------
* All DB access is parameterized Django ORM.
* Companies are soft-deletable; every query filters ``is_deleted=False``.
* Decimals are converted to float for JSON-safe tool results.
* Metal-price tools cover precious metals only (gold/silver/platinum/
  palladium) - base-metal price history does not yet exist on the platform.
"""

import logging
import statistics
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.db.models import Q
from django.utils import timezone

from .base import BaseMCPServer

logger = logging.getLogger(__name__)

# Resource categories that can be summed without double-counting. 'mni'
# (Measured & Indicated combined) and reserve categories overlap these, so
# they are reported separately rather than added in.
ADDITIVE_RESOURCE_CATEGORIES = ['inferred', 'indicated', 'measured']
RESERVE_CATEGORIES = ['proven', 'probable']


def _f(value) -> Optional[float]:
    """Convert a Decimal/number to float for JSON output; pass through None."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return value


def _pct(part: float, whole: float) -> Optional[float]:
    """Percentage change helper, guarding division by zero."""
    if not whole:
        return None
    return round((part - whole) / whole * 100, 2)


class InsightsToolsServer(BaseMCPServer):
    """MCP server exposing historical-data analytics tools."""

    def __init__(self, company_id: int = None, user=None):
        super().__init__(company_id=company_id, user=user)
        self._rag_manager = None  # lazily built - heavy (ChromaDB + embeddings)

    def _register_tools(self):
        """Required by BaseMCPServer; schemas are returned via get_tool_definitions()."""
        pass

    # ------------------------------------------------------------------ #
    # Shared helpers
    # ------------------------------------------------------------------ #

    @property
    def rag_manager(self):
        if self._rag_manager is None:
            from .rag_utils import RAGManager
            self._rag_manager = RAGManager()
        return self._rag_manager

    @staticmethod
    def _resolve_company(identifier: str):
        """
        Resolve a name or ticker to a single non-deleted Company.
        Exact ticker match wins; otherwise a partial name match.
        """
        from core.models import Company

        ident = (identifier or "").strip()
        if not ident:
            return None
        active = Company.objects.filter(is_deleted=False)
        match = active.filter(ticker_symbol__iexact=ident).first()
        if match:
            return match
        return active.filter(
            Q(name__icontains=ident) | Q(legal_name__icontains=ident)
        ).first()

    @staticmethod
    def _ticker_display(company) -> str:
        ticker = company.ticker_symbol or ""
        exchange = (company.exchange or "").upper()
        return f"{ticker}.{exchange}" if ticker and exchange else (ticker or company.name)

    # ------------------------------------------------------------------ #
    # Tool definitions
    # ------------------------------------------------------------------ #

    def get_tool_definitions(self) -> List[Dict]:
        return [
            {
                "name": "insights_compare_stock_performance",
                "description": (
                    "Compare share-price performance of 2-10 mining companies "
                    "over a chosen window. Returns each company's % price change, "
                    "daily volatility, and a best-to-worst ranking. Use when the "
                    "user wants to compare how companies' stocks have done, or "
                    "the % move of one or more stocks over a period."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "companies": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "2-10 company names or tickers to compare "
                                "(e.g. ['Aston Bay', 'GROY', '1911 Gold'])."
                            ),
                        },
                        "days": {
                            "type": "integer",
                            "description": "Look-back window in calendar days (default 90, max 400).",
                            "default": 90,
                        },
                    },
                    "required": ["companies"],
                },
            },
            {
                "name": "insights_catalyst_impact",
                "description": (
                    "Event study for one company: measures how its share price "
                    "historically reacted to each TYPE of news (drill results, "
                    "resource updates, financings, etc.) at 1, 5 and 20 trading "
                    "days after the release. Reveals which catalysts actually "
                    "move the stock. Use when the user asks whether a company's "
                    "news moves its price, or which news matters."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Company name or ticker.",
                        },
                        "days_back": {
                            "type": "integer",
                            "description": "How far back to include news events (default 365).",
                            "default": 365,
                        },
                    },
                    "required": ["company_name"],
                },
            },
            {
                "name": "insights_project_due_diligence",
                "description": (
                    "Answer a due-diligence question about a company by semantic "
                    "search across its processed NI 43-101 technical reports and "
                    "documents (RAG). Returns relevant report passages with "
                    "citations to synthesize an answer. Use for technical "
                    "questions: metallurgy, infrastructure, permitting, "
                    "geology, qualified-person statements, project risks."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Company whose reports to search.",
                        },
                        "question": {
                            "type": "string",
                            "description": "The due-diligence question to answer.",
                        },
                        "max_sections": {
                            "type": "integer",
                            "description": "Number of report passages to return (default 6, max 15).",
                            "default": 6,
                        },
                    },
                    "required": ["company_name", "question"],
                },
            },
            {
                "name": "insights_resource_growth",
                "description": (
                    "Track how a company's mineral resource estimates have "
                    "evolved across successive NI 43-101 reports - contained "
                    "ounces, grade, and tonnage by category over time. Use when "
                    "the user asks whether a project's resource is growing, or "
                    "wants the resource history of a company/project."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Company name or ticker.",
                        },
                        "project_name": {
                            "type": "string",
                            "description": "Optional. Restrict to one project of the company.",
                        },
                    },
                    "required": ["company_name"],
                },
            },
            {
                "name": "insights_economic_rerate",
                "description": (
                    "Re-rate a project's economic study (PEA/PFS/FS) at today's "
                    "gold price. Economic studies bake in a gold-price assumption; "
                    "this tool compares it to the live gold price and estimates "
                    "the revalued NPV and lifetime cash-flow uplift. GOLD "
                    "projects only. Use when the user asks what a project is "
                    "worth at the current gold price, or how stale a study is."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Company name or ticker.",
                        },
                        "project_name": {
                            "type": "string",
                            "description": "Optional. Restrict to one project of the company.",
                        },
                        "current_gold_price": {
                            "type": "number",
                            "description": (
                                "Optional override for the current gold price "
                                "(USD/oz). If omitted, the latest stored price "
                                "is used."
                            ),
                        },
                    },
                    "required": ["company_name"],
                },
            },
            {
                "name": "insights_daily_briefing",
                "description": (
                    "Generate a digest of recent activity across the current "
                    "user's watchlist: price moves, news releases, new "
                    "financings and newly added documents per company. Use when "
                    "the user asks for a briefing, a watchlist summary, or "
                    "'what happened with my companies'. Requires a logged-in user."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "watchlist_name": {
                            "type": "string",
                            "description": (
                                "Optional. Which watchlist to summarize; "
                                "defaults to the user's default watchlist."
                            ),
                        },
                        "days_back": {
                            "type": "integer",
                            "description": "Activity window in days (default 7, max 60).",
                            "default": 7,
                        },
                    },
                    "required": [],
                },
            },
        ]

    # ------------------------------------------------------------------ #
    # Routing
    # ------------------------------------------------------------------ #

    def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        handlers = {
            "insights_compare_stock_performance": self._compare_stock_performance,
            "insights_catalyst_impact": self._catalyst_impact,
            "insights_project_due_diligence": self._project_due_diligence,
            "insights_resource_growth": self._resource_growth,
            "insights_economic_rerate": self._economic_rerate,
            "insights_daily_briefing": self._daily_briefing,
        }
        handler = handlers.get(tool_name)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            return handler(parameters or {})
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            logger.error("InsightsToolsServer.%s failed: %s", tool_name, e, exc_info=True)
            return {"error": f"Tool '{tool_name}' failed: {e}"}

    handle_tool_call = execute_tool

    # ------------------------------------------------------------------ #
    # Tool 1: Stock performance comparison
    # ------------------------------------------------------------------ #

    def _compare_stock_performance(self, params: Dict) -> Dict:
        from core.models import StockPrice

        companies = params.get("companies") or []
        if not isinstance(companies, list) or len(companies) < 1:
            return {"error": "Provide a 'companies' list with at least one name/ticker."}
        if len(companies) > 10:
            return {"error": "Compare at most 10 companies at once."}
        days = max(7, min(int(params.get("days", 90)), 400))

        results = []
        unresolved = []
        for ident in companies:
            company = self._resolve_company(ident)
            if company is None:
                unresolved.append(ident)
                continue

            history = list(StockPrice.get_company_history(company, days=days))
            if len(history) < 2:
                results.append({
                    "company": company.name,
                    "ticker": self._ticker_display(company),
                    "error": "Not enough price history in this window.",
                    "data_points": len(history),
                })
                continue

            first, last = history[0], history[-1]
            start_price = _f(first.close_price)
            end_price = _f(last.close_price)

            # Daily % returns for volatility.
            returns = []
            for prev, curr in zip(history, history[1:]):
                if prev.close_price:
                    returns.append(
                        float(curr.close_price - prev.close_price) / float(prev.close_price)
                    )
            volatility = (
                round(statistics.pstdev(returns) * 100, 2) if len(returns) >= 2 else None
            )

            results.append({
                "company": company.name,
                "ticker": self._ticker_display(company),
                "currency": last.currency,
                "start_date": first.date.isoformat(),
                "start_price": start_price,
                "end_date": last.date.isoformat(),
                "end_price": end_price,
                "pct_change": _pct(end_price, start_price),
                "daily_volatility_pct": volatility,
                "data_points": len(history),
            })

        ranked = sorted(
            [r for r in results if r.get("pct_change") is not None],
            key=lambda r: r["pct_change"],
            reverse=True,
        )

        return {
            "window_days": days,
            "companies_compared": len(ranked),
            "ranking_best_to_worst": [r["ticker"] for r in ranked],
            "best_performer": ranked[0] if ranked else None,
            "worst_performer": ranked[-1] if ranked else None,
            "results": results,
            "unresolved_inputs": unresolved,
        }

    # ------------------------------------------------------------------ #
    # Tool 2: Catalyst impact (event study)
    # ------------------------------------------------------------------ #

    def _catalyst_impact(self, params: Dict) -> Dict:
        from core.models import NewsRelease, StockPrice

        company = self._resolve_company(params.get("company_name"))
        if company is None:
            return {"error": f"Company '{params.get('company_name')}' not found."}
        days_back = max(30, min(int(params.get("days_back", 365)), 1095))

        # Full price history as an ordered list so we can step trading days.
        prices = list(
            StockPrice.objects.filter(company=company).order_by("date")
        )
        if len(prices) < 22:
            return {
                "company": company.name,
                "found": False,
                "message": "Not enough price history for an event study (need 20+ trading days).",
            }
        price_dates = [p.date for p in prices]

        cutoff = timezone.now().date() - timedelta(days=days_back)
        events = NewsRelease.objects.filter(
            company=company, release_date__gte=cutoff
        ).order_by("release_date")

        horizons = {"1d": 1, "5d": 5, "20d": 20}
        # by_type[release_type][horizon] -> list of % reactions
        by_type: Dict[str, Dict[str, List[float]]] = {}
        analyzed = 0

        for ev in events:
            # First trading day on/after the release date.
            idx = next(
                (i for i, d in enumerate(price_dates) if d >= ev.release_date), None
            )
            if idx is None:
                continue
            base = float(prices[idx].close_price or 0)
            if base <= 0:
                continue

            analyzed += 1
            bucket = by_type.setdefault(
                ev.release_type, {h: [] for h in horizons}
            )
            for label, offset in horizons.items():
                tgt = idx + offset
                if tgt < len(prices) and prices[tgt].close_price:
                    reaction = (float(prices[tgt].close_price) - base) / base * 100
                    bucket[label].append(round(reaction, 2))

        if analyzed == 0:
            return {
                "company": company.name,
                "found": False,
                "message": f"No news releases found in the last {days_back} days.",
            }

        type_display = dict(NewsRelease.RELEASE_TYPES)
        summary = []
        for rtype, horizon_data in by_type.items():
            entry = {
                "release_type": type_display.get(rtype, rtype),
                "event_count": len(horizon_data["1d"]) or len(horizon_data["5d"]),
            }
            for label in horizons:
                values = horizon_data[label]
                entry[f"avg_change_{label}"] = (
                    round(statistics.mean(values), 2) if values else None
                )
                entry[f"sample_{label}"] = len(values)
            summary.append(entry)

        summary.sort(key=lambda e: e["event_count"], reverse=True)

        return {
            "company": company.name,
            "ticker": self._ticker_display(company),
            "found": True,
            "window_days": days_back,
            "total_events_analyzed": analyzed,
            "by_catalyst_type": summary,
            "note": (
                "Average % share-price change measured at 1/5/20 trading days "
                "after each release. Small samples (sample_* < 4) are weak "
                "evidence - treat as directional only."
            ),
        }

    # ------------------------------------------------------------------ #
    # Tool 6: Project due-diligence (RAG)
    # ------------------------------------------------------------------ #

    def _project_due_diligence(self, params: Dict) -> Dict:
        company = self._resolve_company(params.get("company_name"))
        if company is None:
            return {"error": f"Company '{params.get('company_name')}' not found."}
        question = (params.get("question") or "").strip()
        if not question:
            return {"error": "A 'question' is required."}
        max_sections = max(1, min(int(params.get("max_sections", 6)), 15))

        results = self.rag_manager.search_documents(
            query=question, n_results=max_sections, filter_company=company.name
        )
        if not results:
            return {
                "company": company.name,
                "question": question,
                "found": False,
                "message": (
                    f"No processed report content found for {company.name}. "
                    "The company may not have any NI 43-101 reports ingested yet."
                ),
            }

        sections = []
        documents_seen = {}
        for idx, r in enumerate(results, 1):
            meta = r.get("metadata", {}) or {}
            doc_id = meta.get("document_id")
            title = meta.get("document_title", "Unknown report")
            documents_seen.setdefault(doc_id, title)
            sections.append({
                "rank": idx,
                "text": r.get("text", ""),
                "source": {
                    "document_id": doc_id,
                    "document_title": title,
                    "document_date": meta.get("document_date"),
                    "document_type": meta.get("document_type"),
                },
            })

        return {
            "company": company.name,
            "question": question,
            "found": True,
            "sections": sections,
            "source_documents": [
                {"document_id": k, "title": v} for k, v in documents_seen.items()
            ],
            "hint": (
                "Synthesize an answer from these passages and cite the document "
                "title and date for each claim. State clearly if the passages do "
                "not fully answer the question."
            ),
        }

    # ------------------------------------------------------------------ #
    # Tool 7: Resource growth over time
    # ------------------------------------------------------------------ #

    def _resource_growth(self, params: Dict) -> Dict:
        from core.models import Project, ResourceEstimate

        company = self._resolve_company(params.get("company_name"))
        if company is None:
            return {"error": f"Company '{params.get('company_name')}' not found."}

        projects = Project.objects.filter(company=company)
        project_name = (params.get("project_name") or "").strip()
        if project_name:
            projects = projects.filter(name__icontains=project_name)
        projects = list(projects)
        if not projects:
            return {
                "company": company.name,
                "found": False,
                "message": "No matching projects found for this company.",
            }

        category_display = dict(ResourceEstimate.RESOURCE_CATEGORIES)
        project_reports = []

        for project in projects:
            estimates = ResourceEstimate.objects.filter(project=project).order_by(
                "report_date"
            )
            # Group estimate rows by report_date (one report can list several
            # categories).
            by_date: Dict[str, List[ResourceEstimate]] = {}
            for est in estimates:
                by_date.setdefault(est.report_date.isoformat(), []).append(est)
            if not by_date:
                continue

            timeline = []
            for report_date, rows in sorted(by_date.items()):
                categories = []
                additive_gold = 0.0
                reserve_gold = 0.0
                for r in rows:
                    gold_oz = _f(r.gold_ounces) or 0.0
                    if r.category in ADDITIVE_RESOURCE_CATEGORIES:
                        additive_gold += gold_oz
                    elif r.category in RESERVE_CATEGORIES:
                        reserve_gold += gold_oz
                    categories.append({
                        "category": category_display.get(r.category, r.category),
                        "tonnes": _f(r.tonnes),
                        "gold_grade_gpt": _f(r.gold_grade_gpt),
                        "gold_ounces": _f(r.gold_ounces),
                        "silver_ounces": _f(r.silver_ounces),
                    })
                timeline.append({
                    "report_date": report_date,
                    "standard": rows[0].get_standard_display(),
                    "categories": categories,
                    "resource_gold_oz_excl_reserves": round(additive_gold, 0) or None,
                    "reserve_gold_oz": round(reserve_gold, 0) or None,
                })

            growth = None
            if len(timeline) >= 2:
                first, last = timeline[0], timeline[-1]
                f_oz = first["resource_gold_oz_excl_reserves"]
                l_oz = last["resource_gold_oz_excl_reserves"]
                if f_oz and l_oz:
                    growth = {
                        "first_report": first["report_date"],
                        "latest_report": last["report_date"],
                        "first_resource_gold_oz": f_oz,
                        "latest_resource_gold_oz": l_oz,
                        "change_pct": _pct(l_oz, f_oz),
                    }

            project_reports.append({
                "project": project.name,
                "primary_commodity": project.primary_commodity,
                "estimate_count": len(timeline),
                "timeline": timeline,
                "growth_summary": growth,
            })

        if not project_reports:
            return {
                "company": company.name,
                "found": False,
                "message": "No resource estimates are on record for this company.",
            }

        return {
            "company": company.name,
            "found": True,
            "projects": project_reports,
            "note": (
                "'resource_gold_oz_excl_reserves' sums Inferred + Indicated + "
                "Measured only. Measured & Indicated (combined) and reserve "
                "categories are listed separately to avoid double-counting."
            ),
        }

    # ------------------------------------------------------------------ #
    # Tool 8: Economic study re-rate at today's gold price
    # ------------------------------------------------------------------ #

    def _economic_rerate(self, params: Dict) -> Dict:
        from core.models import EconomicStudy, MetalPrice, Project

        company = self._resolve_company(params.get("company_name"))
        if company is None:
            return {"error": f"Company '{params.get('company_name')}' not found."}

        # Current gold price: explicit override, else latest stored XAU price.
        current_price = params.get("current_gold_price")
        price_source = "user-provided"
        if current_price is None:
            latest = MetalPrice.get_latest_prices().get("XAU")
            if latest is None:
                return {
                    "error": "No stored gold price available; pass current_gold_price."
                }
            current_price = float(latest.mid_price)
            price_source = f"stored Kitco price ({latest.scraped_at.date().isoformat()})"
        current_price = float(current_price)

        projects = Project.objects.filter(company=company)
        project_name = (params.get("project_name") or "").strip()
        if project_name:
            projects = projects.filter(name__icontains=project_name)

        studies = EconomicStudy.objects.filter(project__in=projects).select_related(
            "project"
        ).order_by("-release_date")
        if not studies:
            return {
                "company": company.name,
                "found": False,
                "message": "No economic studies (PEA/PFS/FS) on record for this company.",
            }

        rerated = []
        for study in studies:
            entry = {
                "project": study.project.name,
                "study_type": study.get_study_type_display(),
                "release_date": study.release_date.isoformat(),
                "original_npv_5pct_usd_m": _f(study.npv_5_usd),
                "original_irr_pct": _f(study.irr_percent),
                "gold_price_assumption": _f(study.gold_price_assumption),
                "aisc_per_oz": _f(study.aisc_per_oz),
                "annual_production_oz": study.annual_production_oz,
                "mine_life_years": _f(study.mine_life_years),
                "current_gold_price": round(current_price, 2),
            }

            assumed = _f(study.gold_price_assumption)
            aisc = _f(study.aisc_per_oz)

            if not assumed:
                entry["rerate"] = None
                entry["rerate_note"] = "Study has no gold-price assumption on record."
                rerated.append(entry)
                continue

            entry["price_delta_per_oz"] = round(current_price - assumed, 2)
            entry["price_change_pct"] = _pct(current_price, assumed)

            # Lifetime undiscounted pre-tax cash-flow swing from the price move.
            if study.annual_production_oz and study.mine_life_years:
                lifetime_oz = study.annual_production_oz * float(study.mine_life_years)
                entry["lifetime_pretax_delta_usd_m"] = round(
                    lifetime_oz * (current_price - assumed) / 1_000_000, 1
                )

            # Margin-leverage NPV re-rate (rule of thumb): NPV scales roughly
            # with operating margin per ounce when the cost base is fixed.
            if aisc is not None and study.npv_5_usd is not None:
                margin_old = assumed - aisc
                margin_new = current_price - aisc
                if margin_old > 0:
                    leverage = margin_new / margin_old
                    entry["margin_leverage_factor"] = round(leverage, 2)
                    entry["rerated_npv_estimate_usd_m"] = round(
                        _f(study.npv_5_usd) * leverage, 1
                    )
                else:
                    entry["rerate_note"] = (
                        "Original margin (assumed price - AISC) is non-positive; "
                        "leverage re-rate not meaningful."
                    )
            else:
                entry["rerate_note"] = (
                    "Missing AISC or original NPV; only the lifetime cash-flow "
                    "delta could be estimated."
                )

            rerated.append(entry)

        return {
            "company": company.name,
            "found": True,
            "current_gold_price_used": round(current_price, 2),
            "price_source": price_source,
            "studies": rerated,
            "methodology": (
                "Re-rate is an approximation. 'rerated_npv_estimate' scales the "
                "original NPV by the change in operating margin per ounce "
                "(margin = gold price - AISC) - a standard rule of thumb, NOT a "
                "rebuilt cash-flow model. It ignores taxes, royalties, "
                "sustaining-capital changes and grade/recovery effects. Treat "
                "as indicative."
            ),
        }

    # ------------------------------------------------------------------ #
    # Tool 11: Daily briefing for a user's watchlist
    # ------------------------------------------------------------------ #

    def _daily_briefing(self, params: Dict) -> Dict:
        from core.models import (
            Document, Financing, NewsRelease, StockPrice, Watchlist,
        )

        if self.user is None or not getattr(self.user, "is_authenticated", False):
            return {"error": "A logged-in user is required to build a watchlist briefing."}

        days_back = max(1, min(int(params.get("days_back", 7)), 60))
        watchlist_name = (params.get("watchlist_name") or "").strip()

        watchlists = Watchlist.objects.filter(user=self.user)
        if watchlist_name:
            watchlist = watchlists.filter(name__icontains=watchlist_name).first()
        else:
            watchlist = watchlists.filter(is_default=True).first() or watchlists.first()

        if watchlist is None:
            return {
                "found": False,
                "message": (
                    "You don't have any watchlists yet. Add companies to a "
                    "watchlist to get a briefing."
                ),
            }

        companies = list(watchlist.companies.filter(is_deleted=False))
        if not companies:
            return {
                "found": False,
                "watchlist": watchlist.name,
                "message": "This watchlist has no companies in it.",
            }

        cutoff_date = timezone.now().date() - timedelta(days=days_back)
        briefing = []

        for company in companies:
            # Price move over the window.
            history = list(StockPrice.get_company_history(company, days=days_back))
            price_block = None
            if len(history) >= 2:
                first, last = history[0], history[-1]
                price_block = {
                    "latest_close": _f(last.close_price),
                    "as_of": last.date.isoformat(),
                    "change_pct": _pct(_f(last.close_price), _f(first.close_price)),
                    "currency": last.currency,
                }
            elif history:
                price_block = {
                    "latest_close": _f(history[-1].close_price),
                    "as_of": history[-1].date.isoformat(),
                    "change_pct": None,
                    "currency": history[-1].currency,
                }

            news = NewsRelease.objects.filter(
                company=company, release_date__gte=cutoff_date
            ).order_by("-release_date")[:5]

            financings = Financing.objects.filter(
                company=company, is_deleted=False, announced_date__gte=cutoff_date
            ).order_by("-announced_date")[:5]

            documents = Document.objects.filter(
                company=company, created_at__date__gte=cutoff_date
            ).order_by("-created_at")[:5]

            briefing.append({
                "company": company.name,
                "ticker": self._ticker_display(company),
                "price": price_block,
                "news_releases": [
                    {
                        "title": n.title,
                        "date": n.release_date.isoformat(),
                        "type": n.get_release_type_display(),
                        "url": n.url,
                    }
                    for n in news
                ],
                "new_financings": [
                    {
                        "type": f.get_financing_type_display(),
                        "status": f.get_status_display(),
                        "amount_usd": _f(f.amount_raised_usd),
                        "announced_date": f.announced_date.isoformat(),
                    }
                    for f in financings
                ],
                "new_documents": [
                    {
                        "title": d.title,
                        "type": d.get_document_type_display(),
                        "document_date": (
                            d.document_date.isoformat() if d.document_date else None
                        ),
                    }
                    for d in documents
                ],
                "activity_count": len(news) + len(financings) + len(documents),
            })

        # Most active first - that's what the reader wants to see.
        briefing.sort(key=lambda c: c["activity_count"], reverse=True)

        return {
            "found": True,
            "watchlist": watchlist.name,
            "window_days": days_back,
            "company_count": len(companies),
            "companies": briefing,
            "hint": (
                "Write a concise briefing, one short paragraph per company, "
                "leading with the companies that have the most activity. Note "
                "companies with no activity only briefly."
            ),
        }
