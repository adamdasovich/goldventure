"""
Tool Registry with Progressive Discovery
Implements token-efficient tool discovery as recommended by Anthropic's
"Code execution with MCP: Building more efficient agents" article.

Key optimizations:
1. Progressive disclosure - search tools by query with configurable detail levels
2. On-demand loading - tools loaded only when needed
3. Category-based filtering - load only relevant tool categories
4. Metadata caching - tool definitions cached to avoid regeneration
"""

from typing import Dict, List, Any, Optional, Literal
from functools import lru_cache
from dataclasses import dataclass
from enum import Enum


class ToolCategory(Enum):
    """Categories for grouping related tools"""
    MINING = "mining"
    FINANCIAL = "financial"
    MARKET = "market"
    DOCUMENTS = "documents"
    NEWS = "news"
    SEARCH = "search"


class DetailLevel(Enum):
    """How much detail to return about tools"""
    NAME_ONLY = "name_only"           # Just tool names (minimal tokens)
    WITH_DESCRIPTION = "description"   # Name + short description
    FULL_SCHEMA = "full"              # Complete schema (for execution)


@dataclass
class ToolMetadata:
    """Lightweight metadata about a tool (for discovery)"""
    name: str
    category: ToolCategory
    description: str
    keywords: List[str]

    def matches_query(self, query: str) -> bool:
        """Check if this tool matches a search query"""
        query_lower = query.lower()
        # Check name, description, and keywords
        if query_lower in self.name.lower():
            return True
        if query_lower in self.description.lower():
            return True
        for keyword in self.keywords:
            if query_lower in keyword.lower():
                return True
        return False


class ToolRegistry:
    """
    Central registry for all MCP tools with progressive discovery.

    Instead of loading all 22+ tool definitions into Claude's context,
    this registry allows Claude to:
    1. Search for relevant tools by query
    2. Get tool metadata at different detail levels
    3. Only load full schemas when actually needed

    This can reduce token usage by 90%+ for many queries.
    """

    def __init__(self):
        self._tool_metadata: Dict[str, ToolMetadata] = {}
        self._tool_servers: Dict[str, str] = {}  # tool_name -> server_type
        self._server_instances: Dict[str, Any] = {}
        self._full_definitions_cache: Dict[str, Dict] = {}
        self._register_all_tool_metadata()

    def _register_all_tool_metadata(self):
        """Register metadata for all available tools (lightweight, no schemas)"""

        # Mining tools
        self._register_metadata("mining_list_companies", ToolCategory.MINING,
            "List all mining companies with basic info",
            ["companies", "list", "ticker", "exchange", "overview"])

        self._register_metadata("mining_get_company_details", ToolCategory.MINING,
            "Get comprehensive details about a specific mining company",
            ["company", "details", "info", "projects", "management", "contact"])

        self._register_metadata("mining_list_projects", ToolCategory.MINING,
            "List mining projects with filtering options",
            ["projects", "list", "filter", "stage", "country", "commodity"])

        self._register_metadata("mining_get_project_details", ToolCategory.MINING,
            "Get detailed project information including resources and economics",
            ["project", "details", "resources", "economics", "location"])

        self._register_metadata("mining_get_total_resources", ToolCategory.MINING,
            "Calculate total gold/silver/copper resources across projects",
            ["resources", "total", "gold", "silver", "copper", "ounces", "aggregate"])

        # Financial tools
        self._register_metadata("financial_get_market_data", ToolCategory.FINANCIAL,
            "Get stock price, market cap, volume for a company",
            ["price", "stock", "market cap", "volume", "shares", "quote"])

        self._register_metadata("financial_list_financings", ToolCategory.FINANCIAL,
            "List capital raises and financings",
            ["financing", "capital", "raise", "placement", "offering"])

        self._register_metadata("financial_get_company_financings", ToolCategory.FINANCIAL,
            "Get complete financing history for a company",
            ["financing", "history", "capital", "raised", "company"])

        self._register_metadata("financial_list_investors", ToolCategory.FINANCIAL,
            "List institutional and major investors",
            ["investors", "institutional", "ownership", "shareholders"])

        self._register_metadata("financial_compare_market_caps", ToolCategory.FINANCIAL,
            "Compare market caps and valuations across companies",
            ["compare", "market cap", "valuation", "ranking"])

        self._register_metadata("financial_financing_analytics", ToolCategory.FINANCIAL,
            "Get aggregate financing statistics and trends",
            ["analytics", "trends", "statistics", "financing", "aggregate"])

        # Real-time market tools
        self._register_metadata("alphavantage_get_quote", ToolCategory.MARKET,
            "Get real-time stock quote for any ticker",
            ["quote", "real-time", "price", "live", "current"])

        self._register_metadata("alphavantage_get_intraday", ToolCategory.MARKET,
            "Get intraday price data (1min to 60min intervals)",
            ["intraday", "minute", "hourly", "price", "historical"])

        self._register_metadata("alphavantage_get_daily", ToolCategory.MARKET,
            "Get daily historical price data",
            ["daily", "historical", "price", "chart", "history"])

        # Document tools
        self._register_metadata("document_process_ni43101_hybrid", ToolCategory.DOCUMENTS,
            "Process NI 43-101 technical reports",
            ["document", "NI 43-101", "report", "process", "extract", "technical"])

        self._register_metadata("document_extract_resource_tables", ToolCategory.DOCUMENTS,
            "Extract resource tables from documents",
            ["table", "extract", "resources", "document"])

        self._register_metadata("document_extract_economics_hybrid", ToolCategory.DOCUMENTS,
            "Extract economic data (NPV, IRR, capex, opex)",
            ["economics", "NPV", "IRR", "capex", "opex", "extract"])

        # Search/RAG tools
        self._register_metadata("search_documents", ToolCategory.SEARCH,
            "Semantic search across processed documents",
            ["search", "semantic", "documents", "RAG", "query"])

        self._register_metadata("get_document_context", ToolCategory.SEARCH,
            "Get formatted context for answering questions with citations",
            ["context", "citations", "answer", "documents"])

        # News tools
        self._register_metadata("get_latest_news_releases", ToolCategory.NEWS,
            "Get latest news releases for a company",
            ["news", "latest", "releases", "press", "announcements"])

        self._register_metadata("search_news_releases", ToolCategory.NEWS,
            "Search news releases by keyword or topic",
            ["news", "search", "keyword", "topic"])

        self._register_metadata("get_news_by_date_range", ToolCategory.NEWS,
            "Get news within a specific date range",
            ["news", "date", "range", "historical"])

    def _register_metadata(self, name: str, category: ToolCategory,
                          description: str, keywords: List[str]):
        """Register tool metadata"""
        self._tool_metadata[name] = ToolMetadata(
            name=name,
            category=category,
            description=description,
            keywords=keywords
        )
        # Map tool to server type based on prefix
        if name.startswith("mining_"):
            self._tool_servers[name] = "mining"
        elif name.startswith("financial_"):
            self._tool_servers[name] = "financial"
        elif name.startswith("alphavantage_"):
            self._tool_servers[name] = "alpha_vantage"
        elif name.startswith("document_"):
            self._tool_servers[name] = "document_processor"
        elif name.startswith("search_") or name.startswith("get_document_"):
            self._tool_servers[name] = "document_search"
        elif "news" in name:
            self._tool_servers[name] = "news_release"

    def search_tools(self, query: str = None,
                    category: ToolCategory = None,
                    detail_level: DetailLevel = DetailLevel.WITH_DESCRIPTION,
                    limit: int = 10) -> Dict:
        """
        Search for tools matching a query or category.

        This is the primary progressive discovery method. Claude can call this
        to find relevant tools without loading all tool schemas.

        Args:
            query: Search query (searches name, description, keywords)
            category: Filter by tool category
            detail_level: How much detail to return
            limit: Maximum number of tools to return

        Returns:
            Dict with matching tools at requested detail level
        """
        matching_tools = []

        for name, metadata in self._tool_metadata.items():
            # Filter by category if specified
            if category and metadata.category != category:
                continue

            # Filter by query if specified
            if query and not metadata.matches_query(query):
                continue

            matching_tools.append(metadata)

        # Limit results
        matching_tools = matching_tools[:limit]

        # Format based on detail level
        if detail_level == DetailLevel.NAME_ONLY:
            return {
                "tools": [t.name for t in matching_tools],
                "total_found": len(matching_tools),
                "hint": "Use get_tool_schema to get full details for a specific tool"
            }

        elif detail_level == DetailLevel.WITH_DESCRIPTION:
            return {
                "tools": [
                    {"name": t.name, "description": t.description, "category": t.category.value}
                    for t in matching_tools
                ],
                "total_found": len(matching_tools),
                "hint": "Use get_tool_schema to get full schema for execution"
            }

        else:  # FULL_SCHEMA
            return {
                "tools": [
                    self.get_tool_schema(t.name)
                    for t in matching_tools
                ],
                "total_found": len(matching_tools)
            }

    def get_tool_schema(self, tool_name: str) -> Optional[Dict]:
        """
        Get the full schema for a specific tool (for execution).

        This loads the complete tool definition only when needed.
        """
        if tool_name not in self._tool_metadata:
            return None

        # Check cache first
        if tool_name in self._full_definitions_cache:
            return self._full_definitions_cache[tool_name]

        # Load from appropriate server (lazy loading)
        server_type = self._tool_servers.get(tool_name)
        if not server_type:
            return None

        # Get tool definition from server
        server = self._get_server_instance(server_type)
        if server:
            for tool_def in server.get_tool_definitions():
                if tool_def.get('name') == tool_name:
                    self._full_definitions_cache[tool_name] = tool_def
                    return tool_def

        return None

    def _get_server_instance(self, server_type: str, company_id: int = None, user=None):
        """Lazy load server instances"""
        cache_key = f"{server_type}_{company_id}"

        if cache_key not in self._server_instances:
            if server_type == "mining":
                from mcp_servers.mining_data import MiningDataServer
                self._server_instances[cache_key] = MiningDataServer(company_id, user)
            elif server_type == "financial":
                from mcp_servers.financial_data import FinancialDataServer
                self._server_instances[cache_key] = FinancialDataServer(company_id, user)
            elif server_type == "alpha_vantage":
                from mcp_servers.alpha_vantage import AlphaVantageServer
                self._server_instances[cache_key] = AlphaVantageServer(company_id, user)
            elif server_type == "document_processor":
                from mcp_servers.document_processor_hybrid import HybridDocumentProcessor
                self._server_instances[cache_key] = HybridDocumentProcessor(company_id, user)
            elif server_type == "document_search":
                from mcp_servers.document_search import DocumentSearchServer
                self._server_instances[cache_key] = DocumentSearchServer(company_id, user)
            elif server_type == "news_release":
                from mcp_servers.news_release_server import NewsReleaseServer
                self._server_instances[cache_key] = NewsReleaseServer(company_id, user)

        return self._server_instances.get(cache_key)

    def get_tools_for_categories(self, categories: List[ToolCategory],
                                  company_id: int = None, user=None) -> List[Dict]:
        """
        Get full tool definitions for specific categories only.

        This is useful when the context makes it clear which tools are relevant.
        For example, if user asks about stock prices, only load financial/market tools.
        """
        tools = []

        for name, metadata in self._tool_metadata.items():
            if metadata.category in categories:
                schema = self.get_tool_schema(name)
                if schema:
                    tools.append(schema)

        return tools

    def get_recommended_tools(self, user_query: str) -> List[str]:
        """
        Analyze user query and recommend which tool categories to load.

        This helps the ClaudeClient decide which tools to include in the context.
        """
        query_lower = user_query.lower()
        recommended_categories = set()

        # Mining-related keywords
        if any(kw in query_lower for kw in ["company", "companies", "project", "resource",
                                            "gold", "silver", "copper", "mine", "mining",
                                            "ounces", "tonnes", "grade"]):
            recommended_categories.add(ToolCategory.MINING)

        # Financial keywords
        if any(kw in query_lower for kw in ["price", "stock", "market cap", "financing",
                                            "investor", "capital", "shares", "valuation",
                                            "trading", "volume"]):
            recommended_categories.add(ToolCategory.FINANCIAL)

        # Real-time market keywords
        if any(kw in query_lower for kw in ["quote", "real-time", "live", "intraday",
                                            "current price", "today's price"]):
            recommended_categories.add(ToolCategory.MARKET)

        # Document keywords
        if any(kw in query_lower for kw in ["document", "report", "ni 43-101", "technical",
                                            "extract", "process", "pdf"]):
            recommended_categories.add(ToolCategory.DOCUMENTS)

        # Search/RAG keywords
        if any(kw in query_lower for kw in ["search", "find", "look for", "drilling",
                                            "metallurgy", "geology", "infrastructure"]):
            recommended_categories.add(ToolCategory.SEARCH)

        # News keywords
        if any(kw in query_lower for kw in ["news", "release", "announcement", "press",
                                            "latest", "recent"]):
            recommended_categories.add(ToolCategory.NEWS)

        # If no specific categories detected, return common ones
        if not recommended_categories:
            recommended_categories = {ToolCategory.MINING, ToolCategory.FINANCIAL}

        return list(recommended_categories)


# Singleton instance
_registry = None

def get_registry() -> ToolRegistry:
    """Get the global tool registry instance"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
