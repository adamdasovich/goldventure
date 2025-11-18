"""
Document Search MCP Server
Provides semantic search across processed NI 43-101 reports and other documents
"""

from .base import BaseMCPServer
from .rag_utils import RAGManager
from typing import Dict, List


class DocumentSearchServer(BaseMCPServer):
    """MCP Server for semantic document search using RAG"""

    def __init__(self, company_id: int = None, user=None):
        super().__init__(company_id=company_id, user=user)
        self.rag_manager = RAGManager()

    def _register_tools(self):
        """Register tools with the MCP server (required by base class)"""
        pass  # Tools are returned dynamically via get_tools()

    def get_tools(self) -> List[Dict]:
        """Define available tools for document search"""
        return [
            {
                "name": "search_documents",
                "description": """Search across all processed NI 43-101 technical reports and company documents.

                This tool performs semantic search to find relevant information from processed documents.
                Use this when users ask questions about:
                - Resource estimates and mineral resources
                - Drilling results and exploration data
                - Metallurgical test results
                - Mining methods and infrastructure
                - Geological descriptions
                - Any specific details from technical reports

                The search returns relevant document sections with their sources.""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The user's question or search query"
                        },
                        "company_name": {
                            "type": "string",
                            "description": "Optional: Filter results to a specific company (e.g., 'Aston Bay', '1911 Gold')"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of relevant chunks to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_document_context",
                "description": """Get formatted context from documents to answer a specific question.

                This tool retrieves relevant document sections and formats them as context
                that can be used to answer the user's question with citations.

                Use this when you need to provide detailed answers backed by document content.""",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question to find context for"
                        },
                        "company_name": {
                            "type": "string",
                            "description": "Optional: Filter to a specific company"
                        }
                    },
                    "required": ["question"]
                }
            }
        ]

    def _search_documents(self, query: str, company_name: str = None, max_results: int = 5) -> Dict:
        """Search documents and return results"""
        try:
            results = self.rag_manager.search_documents(
                query=query,
                n_results=max_results,
                filter_company=company_name
            )

            if not results:
                return {
                    "found": False,
                    "message": f"No relevant information found for: {query}",
                    "results": []
                }

            # Format results for return
            formatted_results = []
            for idx, result in enumerate(results, 1):
                meta = result['metadata']
                formatted_results.append({
                    "rank": idx,
                    "relevance_score": 1 - result['distance'] if result.get('distance') else None,
                    "text": result['text'],
                    "source": {
                        "document_title": meta['document_title'],
                        "document_date": meta['document_date'],
                        "company": meta['company'],
                        "document_type": meta['document_type'],
                        "document_id": meta['document_id']
                    }
                })

            return {
                "found": True,
                "total_results": len(formatted_results),
                "query": query,
                "results": formatted_results
            }

        except Exception as e:
            return {
                "error": f"Search failed: {str(e)}",
                "found": False,
                "results": []
            }

    def _get_document_context(self, question: str, company_name: str = None) -> Dict:
        """Get formatted context for answering a question"""
        try:
            context = self.rag_manager.get_context_for_query(
                query=question,
                company=company_name,
                max_chunks=5
            )

            return {
                "success": True,
                "question": question,
                "context": context,
                "message": "Use this context to answer the user's question. Cite the sources in your response."
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get context: {str(e)}",
                "context": ""
            }

    def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute a tool by name (required by ClaudeClient)"""
        return self.handle_tool_call(tool_name, parameters)

    def handle_tool_call(self, tool_name: str, tool_input: Dict) -> Dict:
        """Route tool calls to appropriate handlers"""
        if tool_name == "search_documents":
            return self._search_documents(
                query=tool_input['query'],
                company_name=tool_input.get('company_name'),
                max_results=tool_input.get('max_results', 5)
            )

        elif tool_name == "get_document_context":
            return self._get_document_context(
                question=tool_input['question'],
                company_name=tool_input.get('company_name')
            )

        else:
            return {"error": f"Unknown tool: {tool_name}"}
