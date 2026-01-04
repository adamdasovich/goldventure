"""
Glossary MCP Server
Provides tools for accessing mining glossary terms and definitions
"""

from typing import Dict, List
from core.models import GlossaryTerm
from django.db.models import Q


class GlossaryServer:
    """MCP Server for glossary term lookups"""

    def __init__(self, company_id: int = None, user=None):
        self.company_id = company_id
        self.user = user

    def get_tool_definitions(self) -> List[Dict]:
        """Return tool definitions for Claude"""
        return [
            {
                "name": "glossary_search",
                "description": "Search the mining industry glossary for term definitions. Use this when users ask about mining terminology, technical terms, standards (like NI 43-101), or need explanations of industry concepts (e.g., 'What is M&I?', 'Define PEA', 'Explain TSXV'). Returns the term name, definition, category, and related links if available.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "term": {
                            "type": "string",
                            "description": "The mining term to search for (e.g., 'NI 43-101', 'Indicated Resource', 'PEA'). Can be partial - will search term names and definitions."
                        }
                    },
                    "required": ["term"]
                }
            },
            {
                "name": "glossary_list_by_category",
                "description": "Get all glossary terms in a specific category. Use when user asks about a type of terms (e.g., 'reporting terms', 'geological terms', 'financial terms').",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Category to filter by",
                            "enum": ["reporting", "geology", "finance", "regulatory", "operations", "general"]
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of terms to return (default 20)",
                            "default": 20
                        }
                    },
                    "required": ["category"]
                }
            },
            {
                "name": "glossary_list_all",
                "description": "Get a list of all available glossary terms with their categories. Use when user wants to browse available terms or get an overview of the glossary.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "include_definitions": {
                            "type": "boolean",
                            "description": "Whether to include full definitions (default false - just returns term names and categories)",
                            "default": False
                        }
                    }
                }
            }
        ]

    def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute a tool by name"""

        if tool_name == "glossary_search":
            return self._search_glossary(parameters)
        elif tool_name == "glossary_list_by_category":
            return self._get_by_category(parameters)
        elif tool_name == "glossary_list_all":
            return self._list_all_terms(parameters)
        else:
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": [t["name"] for t in self.get_tool_definitions()]
            }

    def _search_glossary(self, parameters: Dict) -> Dict:
        """Search for glossary terms by name or definition"""
        term_query = parameters.get("term", "").strip()

        if not term_query:
            return {
                "error": "Term parameter is required",
                "results": []
            }

        # Search in term name and definition (case-insensitive)
        terms = GlossaryTerm.objects.filter(
            Q(term__icontains=term_query) | Q(definition__icontains=term_query)
        ).order_by('term')[:10]  # Limit to top 10 results

        if not terms.exists():
            return {
                "query": term_query,
                "results": [],
                "message": f"No glossary terms found matching '{term_query}'"
            }

        results = []
        for term in terms:
            term_data = {
                "term": term.term,
                "definition": term.definition,
                "category": term.get_category_display(),
                "category_code": term.category
            }

            # Add keywords if available
            if term.keywords:
                term_data["keywords"] = term.keywords

            # Add related links if available
            if term.related_links:
                term_data["related_links"] = term.related_links

            results.append(term_data)

        return {
            "query": term_query,
            "count": len(results),
            "results": results
        }

    def _get_by_category(self, parameters: Dict) -> Dict:
        """Get glossary terms by category"""
        category = parameters.get("category")
        limit = parameters.get("limit", 20)

        if not category:
            return {
                "error": "Category parameter is required",
                "valid_categories": ["reporting", "geology", "finance", "regulatory", "operations", "general"]
            }

        # Validate category
        valid_categories = ["reporting", "geology", "finance", "regulatory", "operations", "general"]
        if category not in valid_categories:
            return {
                "error": f"Invalid category: {category}",
                "valid_categories": valid_categories
            }

        terms = GlossaryTerm.objects.filter(category=category).order_by('term')[:limit]

        if not terms.exists():
            return {
                "category": category,
                "results": [],
                "message": f"No terms found in category '{category}'"
            }

        results = []
        for term in terms:
            results.append({
                "term": term.term,
                "definition": term.definition,
                "keywords": term.keywords if term.keywords else None
            })

        return {
            "category": category,
            "count": len(results),
            "results": results
        }

    def _list_all_terms(self, parameters: Dict) -> Dict:
        """List all glossary terms with optional definitions"""
        include_definitions = parameters.get("include_definitions", False)

        terms = GlossaryTerm.objects.all().order_by('term')

        if not terms.exists():
            return {
                "count": 0,
                "terms": [],
                "message": "Glossary is empty"
            }

        if include_definitions:
            results = []
            for term in terms:
                results.append({
                    "term": term.term,
                    "definition": term.definition,
                    "category": term.get_category_display()
                })

            return {
                "count": len(results),
                "terms": results
            }
        else:
            # Just return term names grouped by category
            categories = {}
            for term in terms:
                cat = term.get_category_display()
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(term.term)

            return {
                "count": terms.count(),
                "categories": categories,
                "message": f"Total {terms.count()} terms across {len(categories)} categories"
            }
