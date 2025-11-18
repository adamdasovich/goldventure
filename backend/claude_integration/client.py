"""
Claude API Client with MCP Integration
Handles conversation management and tool calling
"""

import anthropic
from django.conf import settings
from typing import List, Dict, Any
from mcp_servers.mining_data import MiningDataServer
from mcp_servers.financial_data import FinancialDataServer
from mcp_servers.alpha_vantage import AlphaVantageServer
from mcp_servers.document_processor_hybrid import HybridDocumentProcessor
from mcp_servers.document_search import DocumentSearchServer


class ClaudeClient:
    """
    Wrapper around Anthropic Claude API with MCP integration.
    Handles conversation management and tool calling.
    """

    def __init__(self, company_id: int = None, user=None):
        """
        Initialize Claude client with MCP servers.

        Args:
            company_id: Company context for MCP servers (optional)
            user: Django User for permissions
        """
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.company_id = company_id
        self.user = user

        # Initialize MCP servers
        self.mining_server = MiningDataServer(company_id, user)
        self.financial_server = FinancialDataServer(company_id, user)
        self.alpha_vantage_server = AlphaVantageServer(company_id, user)
        self.document_processor = HybridDocumentProcessor(company_id, user)
        self.document_search = DocumentSearchServer(company_id, user)

        # Map tool name prefixes to servers
        self.server_map = {
            'mining_': self.mining_server,
            'financial_': self.financial_server,
            'alphavantage_': self.alpha_vantage_server,
            'document_': self.document_processor,
            'search_': self.document_search,
            'get_document_': self.document_search,
        }

    def _get_all_tools(self) -> List[Dict]:
        """Get tool definitions from all MCP servers"""
        tools = []
        tools.extend(self.mining_server.get_tool_definitions())
        tools.extend(self.financial_server.get_tool_definitions())
        tools.extend(self.alpha_vantage_server.get_tool_definitions())
        tools.extend(self.document_processor.get_tool_definitions())
        tools.extend(self.document_search.get_tools())
        return tools

    def _route_tool_call(self, tool_name: str, parameters: Dict) -> Any:
        """Route tool call to appropriate MCP server"""

        # Find which server handles this tool
        for prefix, server in self.server_map.items():
            if tool_name.startswith(prefix):
                return server.execute_tool(tool_name, parameters)

        return {'error': f'No server found for tool: {tool_name}'}

    def chat(self, message: str, conversation_history: List[Dict] = None,
             system_prompt: str = None, max_tokens: int = 2000) -> Dict:
        """
        Send a message to Claude with tool access.

        Args:
            message: User's message
            conversation_history: Previous messages in conversation
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens in response

        Returns:
            Dict with 'message', 'tool_calls', and 'usage'
        """

        if conversation_history is None:
            conversation_history = []

        # Default system prompt
        if system_prompt is None:
            system_prompt = """You are an AI assistant for a junior gold mining investment platform.

You have access to a comprehensive database of mining companies, projects, resources, financial data, and market information.
Use the available tools to answer questions accurately about:

MINING DATA:
- Mining companies and their details
- Mining projects (location, stage, commodity, ownership)
- Resource estimates (gold, silver, copper)
- Economic studies and project economics (NPV, IRR, capex, opex)

FINANCIAL DATA:
- Stock prices and market capitalization
- Trading volume and shares outstanding
- Capital raises and financings (private placements, offerings)
- Investor information and ownership
- Market comparisons and valuations
- Financing trends and analytics

REAL-TIME MARKET DATA (Alpha Vantage):
- Real-time stock quotes for any ticker symbol
- Intraday price data (minute/hourly intervals)
- Daily historical price data
- Automatic caching of fetched data to database
- Use these tools when market data is not available in the database

DOCUMENT PROCESSING (Hybrid Docling + Claude):
- Process NI 43-101 technical reports automatically
- Extract resource estimates, economic studies, project details
- Use Docling for table extraction + Claude for interpretation
- Automatically store extracted data in database
- Generate intelligent summaries and key findings
- Highest accuracy for complex mining documents

DOCUMENT SEARCH (Semantic Search with RAG):
- Search across all processed NI 43-101 reports and technical documents
- Ask detailed questions about drilling results, metallurgy, geology, infrastructure
- Get specific information with document citations
- Use search_documents for any detailed questions about technical reports
- Use get_document_context to get formatted context for answering questions

When presenting data:
- Format numbers clearly (use commas for thousands, appropriate decimals)
- Use $ for currency values, M for millions (e.g., $5.2M)
- Provide context (dates, sources, categories)
- Explain technical terms if needed (like M&I, PEA, NI 43-101, market cap, NPV)
- Be concise but thorough
- If you use a tool, explain what data you found
- For financial data, always note the date of the information
- When answering from document search, cite the source document

If you don't have access to specific information, say so clearly and suggest where the user might find it."""

        # Build messages list
        messages = conversation_history + [
            {"role": "user", "content": message}
        ]

        # Get available tools
        tools = self._get_all_tools()

        # Initial API call
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            tools=tools,
            messages=messages
        )

        # Track all tool calls made
        all_tool_calls = []

        # Handle tool calling loop
        while response.stop_reason == "tool_use":

            # Extract tool calls from response
            tool_results = []
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.input

                    # Execute tool via MCP server
                    result = self._route_tool_call(tool_name, tool_input)

                    # Track this tool call
                    all_tool_calls.append({
                        'tool': tool_name,
                        'input': tool_input,
                        'result': result
                    })

                    # Format result for Claude
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": content_block.id,
                        "content": str(result)
                    })

            # Continue conversation with tool results
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

        # Extract final text response
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
            'conversation_history': messages + [
                {"role": "assistant", "content": response.content}
            ]
        }
