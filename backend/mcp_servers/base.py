"""
Base MCP Server Implementation
Provides common functionality for all MCP servers
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from decimal import Decimal
from datetime import date


class BaseMCPServer(ABC):
    """
    Base class for all MCP servers.
    Provides common functionality for tool registration and execution.
    """

    def __init__(self, company_id: int = None, user=None):
        """
        Initialize MCP server with user context.

        Args:
            company_id: The company this server operates on (optional for some queries)
            user: Django User object for permission checking
        """
        self.company_id = company_id
        self.user = user
        self._tools = {}
        self._register_tools()

    @abstractmethod
    def _register_tools(self):
        """
        Register all tools this server provides.
        Must be implemented by subclasses.
        """
        pass

    def register_tool(self, name: str, description: str,
                     input_schema: Dict, handler: callable):
        """
        Register a tool with its handler function.

        Args:
            name: Tool name (e.g., "mining_get_resources")
            description: What the tool does
            input_schema: JSON schema for parameters
            handler: Function to execute when tool is called
        """
        self._tools[name] = {
            'definition': {
                'name': name,
                'description': description,
                'input_schema': input_schema
            },
            'handler': handler
        }

    def get_tool_definitions(self) -> List[Dict]:
        """
        Get all tool definitions for Claude API.

        Returns:
            List of tool definition dicts
        """
        return [tool['definition'] for tool in self._tools.values()]

    def execute_tool(self, tool_name: str, parameters: Dict) -> Any:
        """
        Execute a tool by name with given parameters.

        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool

        Returns:
            Tool execution result
        """
        if tool_name not in self._tools:
            return {
                'error': f"Unknown tool: {tool_name}",
                'available_tools': list(self._tools.keys())
            }

        try:
            handler = self._tools[tool_name]['handler']
            result = handler(**parameters)
            return result
        except Exception as e:
            return {
                'error': str(e),
                'tool': tool_name,
                'parameters': parameters
            }

    def _format_decimal(self, value) -> float:
        """Helper to convert Decimal to float"""
        if isinstance(value, Decimal):
            return float(value)
        return value

    def _format_date(self, date_obj) -> str:
        """Helper to convert date to string"""
        if date_obj:
            if isinstance(date_obj, date):
                return date_obj.isoformat()
            return str(date_obj)
        return None
