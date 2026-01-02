"""
Glossary MCP Server
Provides access to mining industry glossary terms for Claude chatbot
"""

from typing import Dict, List, Any
from .base import BaseMCPServer
from core.models import GlossaryTerm


class GlossaryMCPServer(BaseMCPServer):
    """
    MCP server for querying mining glossary terms.
    Allows Claude to look up technical mining terminology and definitions.
    """

    def __init__(self, company_id: int = None, user=None):
        """Initialize glossary server (doesn't require company context)"""
        super().__init__(company_id=None, user=user)

    def _register_tools(self):
        """Register glossary lookup tools"""

        self.register_tool(
            name="glossary_search",
            description="Search for mining industry glossary terms and definitions. Use this when users ask about technical mining terminology like 'NI 43-101', 'indicated resource', 'feasibility study', etc.",
            input_schema={
                "type": "object",
                "properties": {
                    "term": {
                        "type": "string",
                        "description": "The mining term to look up (e.g., 'NI 43-101', 'Indicated Resource', 'Feasibility Study')"
                    }
                },
                "required": ["term"]
            },
            handler=self._search_term
        )

        self.register_tool(
            name="glossary_list_by_category",
            description="List all glossary terms in a specific category (reporting, geology, finance, regulatory, operations)",
            input_schema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["reporting", "geology", "finance", "regulatory", "operations", "general"],
                        "description": "Category of terms to list"
                    }
                },
                "required": ["category"]
            },
            handler=self._list_by_category
        )

        self.register_tool(
            name="glossary_list_all",
            description="List all available glossary terms (returns term names only for overview)",
            input_schema={
                "type": "object",
                "properties": {}
            },
            handler=self._list_all_terms
        )

    def _search_term(self, params: Dict) -> Dict[str, Any]:
        """
        Search for a specific glossary term.
        Returns exact match or suggestions if no exact match found.
        """
        term_query = params.get("term", "").strip()

        if not term_query:
            return {
                "error": "Please provide a term to search for"
            }

        # Try exact match (case-insensitive)
        exact_match = GlossaryTerm.objects.filter(term__iexact=term_query).first()

        if exact_match:
            return {
                "term": exact_match.term,
                "definition": exact_match.definition,
                "category": exact_match.get_category_display(),
                "related_links": exact_match.related_links or [],
                "exact_match": True
            }

        # Try partial match
        partial_matches = GlossaryTerm.objects.filter(
            term__icontains=term_query
        ).values('term', 'definition', 'category')[:5]

        if partial_matches:
            return {
                "exact_match": False,
                "searched_term": term_query,
                "suggestions": list(partial_matches),
                "message": f"No exact match for '{term_query}'. Here are some similar terms:"
            }

        return {
            "error": f"No glossary term found matching '{term_query}'",
            "searched_term": term_query
        }

    def _list_by_category(self, params: Dict) -> Dict[str, Any]:
        """List all terms in a specific category"""
        category = params.get("category")

        terms = GlossaryTerm.objects.filter(category=category).values(
            'term', 'definition', 'category'
        ).order_by('term')

        return {
            "category": category,
            "count": len(terms),
            "terms": list(terms)
        }

    def _list_all_terms(self, params: Dict) -> Dict[str, Any]:
        """List all available glossary terms (names only for overview)"""
        terms = GlossaryTerm.objects.all().values('term', 'category').order_by('term')

        # Group by category for better overview
        by_category = {}
        for term in terms:
            cat = term['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(term['term'])

        return {
            "total_terms": len(terms),
            "by_category": by_category,
            "all_terms": [t['term'] for t in terms]
        }
