"""
Optimized Claude API Client with MCP Integration

Implements token-efficiency strategies from Anthropic's
"Code execution with MCP: Building more efficient agents" article:

1. Progressive tool discovery - Only load relevant tools based on query
2. Lazy tool loading - Tools loaded on-demand, not all at once
3. In-environment data filtering - Filter results before returning to Claude
4. Result caching - Cache frequently accessed data
5. Smart aggregation - Aggregate large results to reduce tokens

Expected improvements:
- 50-90% reduction in tool definition tokens
- Significant reduction in result payload tokens
- Faster response times for follow-up queries
"""

import anthropic
from django.conf import settings
from django.core.cache import cache
from typing import List, Dict, Any, Optional
import hashlib
import json

from mcp_servers.tool_registry import get_registry, ToolCategory, DetailLevel
from mcp_servers.data_filter import DataFilter, FilterConfig, TokenEstimator


class OptimizedClaudeClient:
    """
    Token-efficient Claude client with progressive tool discovery.

    Key differences from original ClaudeClient:
    1. Uses ToolRegistry for progressive discovery instead of loading all tools
    2. Analyzes user query to load only relevant tool categories
    3. Caches tool results to avoid redundant queries
    4. Filters large results before returning to Claude
    """

    # Cache TTL in seconds
    CACHE_TTL = 300  # 5 minutes

    def __init__(self, company_id: int = None, user=None):
        """Initialize optimized Claude client."""
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.company_id = company_id
        self.user = user
        self.registry = get_registry()

        # Lazy-loaded server instances
        self._servers = {}

        # Session-level result cache (for multi-turn conversations)
        self._result_cache = {}

        # Track which tools have been used this session
        self._used_tools = set()

    def _get_server(self, server_type: str):
        """Lazy load server instances"""
        if server_type not in self._servers:
            if server_type == "mining":
                from mcp_servers.mining_data import MiningDataServer
                self._servers[server_type] = MiningDataServer(self.company_id, self.user)
            elif server_type == "financial":
                from mcp_servers.financial_data import FinancialDataServer
                self._servers[server_type] = FinancialDataServer(self.company_id, self.user)
            elif server_type == "alpha_vantage":
                from mcp_servers.alpha_vantage import AlphaVantageServer
                self._servers[server_type] = AlphaVantageServer(self.company_id, self.user)
            elif server_type == "document_processor":
                from mcp_servers.document_processor_hybrid import HybridDocumentProcessor
                self._servers[server_type] = HybridDocumentProcessor(self.company_id, self.user)
            elif server_type == "document_search":
                from mcp_servers.document_search import DocumentSearchServer
                self._servers[server_type] = DocumentSearchServer(self.company_id, self.user)
            elif server_type == "news_release":
                from mcp_servers.news_release_server import NewsReleaseServer
                self._servers[server_type] = NewsReleaseServer(self.company_id, self.user)
            elif server_type == "glossary":
                from mcp_servers.glossary_server import GlossaryServer
                self._servers[server_type] = GlossaryServer(self.company_id, self.user)

        return self._servers.get(server_type)

    def _get_tools_for_query(self, query: str) -> List[Dict]:
        """
        Get relevant tools based on query analysis.

        Instead of loading all 22+ tools, this analyzes the query
        and loads only the relevant categories.
        """
        # Get recommended categories
        categories = self.registry.get_recommended_tools(query)

        # Get full tool definitions for those categories
        tools = self.registry.get_tools_for_categories(
            categories, self.company_id, self.user
        )

        # Always include the meta-tools for discovery
        tools.extend(self._get_discovery_tools())

        return tools

    def _get_discovery_tools(self) -> List[Dict]:
        """
        Get meta-tools for progressive discovery.

        These allow Claude to search for additional tools if needed.
        """
        return [
            {
                "name": "search_available_tools",
                "description": (
                    "Search for available tools by keyword. Use this if you need "
                    "a tool that wasn't loaded in the initial context. Returns tool "
                    "names and descriptions matching the query."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'stock price', 'news', 'document')"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["mining", "financial", "market", "documents", "news", "search"],
                            "description": "Optional: filter by tool category"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "load_tool",
                "description": (
                    "Load a specific tool by name. Use this after finding a tool "
                    "via search_available_tools. Returns the full tool schema."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tool_name": {
                            "type": "string",
                            "description": "Exact name of the tool to load"
                        }
                    },
                    "required": ["tool_name"]
                }
            }
        ]

    def _route_tool_call(self, tool_name: str, parameters: Dict) -> Any:
        """Route tool call to appropriate server with caching and filtering."""

        # Handle meta-tools
        if tool_name == "search_available_tools":
            return self._handle_search_tools(parameters)
        elif tool_name == "load_tool":
            return self._handle_load_tool(parameters)

        # Check cache first
        cache_key = self._get_cache_key(tool_name, parameters)
        cached_result = self._result_cache.get(cache_key)
        if cached_result is not None:
            return {"_cached": True, **cached_result}

        # Route to appropriate server
        result = self._execute_tool(tool_name, parameters)

        # Filter result if too large
        if TokenEstimator.should_filter(result, max_tokens=3000):
            result = DataFilter.filter_result(result, FilterConfig(
                max_items=30,
                max_string_length=400,
                summarize_lists=True,
                summarize_threshold=15
            ))

        # Cache result
        self._result_cache[cache_key] = result
        self._used_tools.add(tool_name)

        return result

    def _execute_tool(self, tool_name: str, parameters: Dict) -> Any:
        """Execute a tool on the appropriate server."""
        # Determine server type from tool name
        server_type = None
        if tool_name.startswith("mining_"):
            server_type = "mining"
        elif tool_name.startswith("financial_"):
            server_type = "financial"
        elif tool_name.startswith("alphavantage_"):
            server_type = "alpha_vantage"
        elif tool_name.startswith("document_"):
            server_type = "document_processor"
        elif tool_name.startswith("search_") or tool_name.startswith("get_document_"):
            server_type = "document_search"
        elif "news" in tool_name:
            server_type = "news_release"
        elif tool_name.startswith("glossary_"):
            server_type = "glossary"

        if not server_type:
            return {"error": f"Unknown tool: {tool_name}"}

        server = self._get_server(server_type)
        if not server:
            return {"error": f"Server not available for: {tool_name}"}

        return server.execute_tool(tool_name, parameters)

    def _handle_search_tools(self, parameters: Dict) -> Dict:
        """Handle the search_available_tools meta-tool."""
        query = parameters.get("query", "")
        category_str = parameters.get("category")

        category = None
        if category_str:
            category_map = {
                "mining": ToolCategory.MINING,
                "financial": ToolCategory.FINANCIAL,
                "market": ToolCategory.MARKET,
                "documents": ToolCategory.DOCUMENTS,
                "news": ToolCategory.NEWS,
                "search": ToolCategory.SEARCH,
            }
            category = category_map.get(category_str)

        return self.registry.search_tools(
            query=query,
            category=category,
            detail_level=DetailLevel.WITH_DESCRIPTION,
            limit=10
        )

    def _handle_load_tool(self, parameters: Dict) -> Dict:
        """Handle the load_tool meta-tool."""
        tool_name = parameters.get("tool_name")
        schema = self.registry.get_tool_schema(tool_name)

        if schema:
            return {"success": True, "tool": schema}
        else:
            return {"error": f"Tool '{tool_name}' not found"}

    def _get_cache_key(self, tool_name: str, parameters: Dict) -> str:
        """Generate cache key for tool results."""
        param_str = json.dumps(parameters, sort_keys=True)
        key_str = f"{tool_name}:{param_str}:{self.company_id}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def chat(self, message: str, conversation_history: List[Dict] = None,
             system_prompt: str = None, max_tokens: int = 2000) -> Dict:
        """
        Send a message to Claude with optimized tool loading.

        Key optimizations:
        1. Tools are selected based on query analysis
        2. Results are filtered before returning
        3. Caching reduces redundant tool calls
        """
        if conversation_history is None:
            conversation_history = []

        # Optimized system prompt (shorter, focused)
        if system_prompt is None:
            system_prompt = self._get_optimized_system_prompt()

        # Build messages
        messages = conversation_history + [
            {"role": "user", "content": message}
        ]

        # Get relevant tools based on query
        tools = self._get_tools_for_query(message)

        # Track token usage for optimization metrics
        initial_tool_tokens = TokenEstimator.estimate_tokens(tools)

        # Initial API call
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        all_tool_calls = []
        tools_loaded_dynamically = []

        # Handle tool calling loop
        while response.stop_reason == "tool_use":
            tool_results = []

            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input

                    # Execute tool
                    result = self._route_tool_call(tool_name, tool_input)

                    # Track tool call
                    all_tool_calls.append({
                        'tool': tool_name,
                        'input': tool_input,
                        'result_tokens': TokenEstimator.estimate_tokens(result),
                        'cached': result.get('_cached', False) if isinstance(result, dict) else False
                    })

                    # If load_tool was called, add the new tool to available tools
                    if tool_name == "load_tool" and result.get("success"):
                        new_tool = result.get("tool")
                        if new_tool and new_tool not in tools:
                            tools.append(new_tool)
                            tools_loaded_dynamically.append(new_tool.get("name"))

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": str(result)
                    })

            # Continue conversation
            messages.extend([
                {"role": "assistant", "content": response.content},
                {"role": "user", "content": tool_results}
            ])

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system=system_prompt,
                tools=tools,
                messages=messages
            )

        # Extract final response
        final_message = ""
        for content_block in response.content:
            if hasattr(content_block, "text"):
                final_message += content_block.text

        return {
            'message': final_message,
            'tool_calls': all_tool_calls,
            'usage': {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens
            },
            'optimization_metrics': {
                'initial_tool_tokens': initial_tool_tokens,
                'tools_loaded': len(tools),
                'tools_loaded_dynamically': tools_loaded_dynamically,
                'cached_results': sum(1 for tc in all_tool_calls if tc.get('cached')),
                'total_tool_calls': len(all_tool_calls)
            },
            'conversation_history': messages + [
                {"role": "assistant", "content": response.content}
            ]
        }

    def _get_optimized_system_prompt(self) -> str:
        """
        Get a shorter, more focused system prompt.

        The original prompt was ~1500 tokens. This optimized version
        provides the same guidance in fewer tokens.
        """
        return """You are an AI assistant for a junior gold mining investment platform.

You have access to tools for querying:
- Mining: companies, projects, resources (gold/silver/copper)
- Financial: stock prices, market cap, financings, investors
- Market: real-time quotes via Alpha Vantage
- Documents: NI 43-101 reports, technical document search
- News: company releases and announcements

IMPORTANT: If you need a tool that isn't available, use search_available_tools to find it, then load_tool to access it.

When presenting data:
- Use clear formatting ($5.2M, commas for thousands)
- Provide context (dates, sources)
- Explain technical terms if needed (M&I, PEA, NPV)
- Cite document sources when using search results

If data is unavailable, say so clearly."""

    def get_session_stats(self) -> Dict:
        """Get statistics about this session for optimization analysis."""
        return {
            'tools_used': list(self._used_tools),
            'unique_tools': len(self._used_tools),
            'cached_results': len(self._result_cache),
            'servers_loaded': list(self._servers.keys())
        }

    def clear_cache(self):
        """Clear the session result cache."""
        self._result_cache.clear()
