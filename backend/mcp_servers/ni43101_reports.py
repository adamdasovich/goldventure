"""
NI 43-101 Reports MCP Server
=============================

Gives the AI assistant direct access to NI 43-101 technical mining reports that
are already stored in the platform's two databases, removing the previous
limitation of only being able to process reports supplied as direct URLs.

Three tools are exposed:

1. ``reports_vector_search``    - Semantic search over the ChromaDB vector store
                                  (the ``document_chunks`` collection).
2. ``reports_search_technical`` - Structured search over the PostgreSQL
                                  ``documents`` table (Django ORM, parameterized).
3. ``reports_get_content``      - Fetch the full content or an accessible URL for
                                  a specific report given its document identifier.

Design notes
------------
* Tool 2 deliberately uses a *structured*, parameterized search interface (Django
  ORM) rather than a raw-SQL passthrough. Executing LLM-generated SQL would be a
  SQL-injection / data-exfiltration risk and would break the platform's
  parameterized-query security posture (see CLAUDE.md "Security Summary").
* All three tools respect the ``Document.is_public`` flag: non-staff users only
  ever see public documents. Staff / superusers see everything.
* Tools 1 and 2 return ``document_id`` values that can be fed straight into
  Tool 3 (``reports_get_content``).
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional

from core.models import Document, DocumentChunk
from .base import BaseMCPServer
from .rag_utils import RAGManager

logger = logging.getLogger(__name__)

# Document types that count as "technical reports" for the structured search.
TECHNICAL_REPORT_TYPES = ['ni43101', 'mda', 'annual_report', 'financial_stmt']

# How many characters of reconstructed text to return by default in Tool 3.
DEFAULT_MAX_CONTENT_CHARS = 50_000


class NI43101ReportsServer(BaseMCPServer):
    """MCP server exposing database-access tools for stored NI 43-101 reports."""

    def __init__(self, company_id: int = None, user=None):
        super().__init__(company_id=company_id, user=user)
        # RAGManager is relatively heavy (ChromaDB client + embedding fn); only
        # instantiate it when a vector search is actually requested.
        self._rag_manager: Optional[RAGManager] = None

    def _register_tools(self):
        """Required by BaseMCPServer. Tools are returned via get_tool_definitions()."""
        pass

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @property
    def rag_manager(self) -> RAGManager:
        """Lazily fetch the RAG manager so non-vector tools stay lightweight."""
        if self._rag_manager is None:
            from .rag_utils import get_rag_manager
            self._rag_manager = get_rag_manager()
        return self._rag_manager

    @property
    def _is_staff(self) -> bool:
        """True when the requesting user may see non-public documents."""
        return bool(self.user and (self.user.is_staff or self.user.is_superuser))

    def _visible_documents(self):
        """Base Document queryset filtered by the requesting user's access level."""
        qs = Document.objects.all()
        if not self._is_staff:
            qs = qs.filter(is_public=True)
        return qs

    @staticmethod
    def _parse_date(value: str, field_name: str) -> Optional[date]:
        """Parse a YYYY-MM-DD string, raising a ValueError with a clear message."""
        if not value:
            return None
        try:
            return datetime.strptime(value.strip(), '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"{field_name} must be in YYYY-MM-DD format, got '{value}'")

    @staticmethod
    def _detect_format(url: str) -> str:
        """Infer a document format from a URL's file extension."""
        if not url:
            return 'unknown'
        lowered = url.split('?')[0].lower()
        if lowered.endswith('.pdf'):
            return 'pdf'
        if lowered.endswith(('.htm', '.html')):
            return 'html'
        if lowered.endswith(('.txt', '.text')):
            return 'text'
        if lowered.endswith(('.doc', '.docx')):
            return 'word'
        return 'unknown'

    @staticmethod
    def _relevance_score(result: Dict) -> Optional[float]:
        """
        Extract a single relevance score from a hybrid-search result.

        search_documents() may attach a cross-encoder 'rerank_score', a fused
        'rrf_score', or a raw vector 'distance' depending on the pipeline stage.
        """
        if result.get('rerank_score') is not None:
            return round(float(result['rerank_score']), 4)
        if result.get('distance') is not None:
            return round(1.0 - float(result['distance']), 4)
        if result.get('rrf_score') is not None:
            return round(float(result['rrf_score']), 4)
        return None

    def _document_summary(self, doc: Document) -> Dict:
        """Standard metadata block for a Document (shared by Tools 2 and 3)."""
        return {
            "document_id": doc.id,
            "title": doc.title,
            "document_type": doc.get_document_type_display(),
            "document_type_code": doc.document_type,
            "document_date": doc.document_date.isoformat() if doc.document_date else None,
            "company": doc.company.name if doc.company_id else None,
            "company_id": doc.company_id,
            "project": doc.project.name if doc.project_id else None,
            "primary_commodity": (
                doc.project.primary_commodity if doc.project_id else None
            ),
            "file_url": doc.file_url,
            "file_format": self._detect_format(doc.file_url),
            "file_size_mb": float(doc.file_size_mb) if doc.file_size_mb else None,
            "is_public": doc.is_public,
        }

    # ------------------------------------------------------------------ #
    # Tool definitions
    # ------------------------------------------------------------------ #

    def get_tool_definitions(self) -> List[Dict]:
        """Return Claude tool schemas for all three report-access tools."""
        return [
            {
                "name": "reports_vector_search",
                "description": (
                    "Semantic (vector) search over stored NI 43-101 technical "
                    "reports in the ChromaDB vector database. Use this when the "
                    "user asks a conceptual question about report contents -- "
                    "resource estimates, drill results, metallurgy, geology, "
                    "mining methods -- and you want the most relevant passages "
                    "ranked by relevance. Returns ranked text chunks with a "
                    "relevance score and full source metadata (title, date, "
                    "company, report type, document_id). The document_id can be "
                    "passed to reports_get_content to retrieve the whole report."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Natural-language search query. Mining "
                                "terminology and company names are supported."
                            ),
                        },
                        "company_name": {
                            "type": "string",
                            "description": (
                                "Optional. Restrict results to one company "
                                "(e.g. 'Aston Bay', '1911 Gold')."
                            ),
                        },
                        "document_type": {
                            "type": "string",
                            "description": (
                                "Optional report-type filter. One of: ni43101, "
                                "presentation, financial_stmt, mda, annual_report, "
                                "factsheet, map, other."
                            ),
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Optional. Earliest report date, YYYY-MM-DD.",
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Optional. Latest report date, YYYY-MM-DD.",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Number of ranked chunks to return (default 5, max 20).",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "reports_search_technical",
                "description": (
                    "Structured search over the PostgreSQL 'documents' table for "
                    "company-specific technical reports. Use this when the user "
                    "wants to find or list reports by company, project, date, "
                    "commodity, or report type -- rather than search their text. "
                    "Supports exact and partial (case-insensitive) text matching. "
                    "Returns document identifiers plus metadata; pass a "
                    "document_id to reports_get_content to fetch the report."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "Optional. Company name to match.",
                        },
                        "project_name": {
                            "type": "string",
                            "description": "Optional. Project name to match.",
                        },
                        "commodity": {
                            "type": "string",
                            "description": (
                                "Optional. Primary commodity of the report's "
                                "project (e.g. 'gold', 'silver', 'copper')."
                            ),
                        },
                        "document_type": {
                            "type": "string",
                            "description": (
                                "Optional. Report type code (e.g. 'ni43101'). "
                                "If omitted, all technical report types are "
                                "searched (NI 43-101, MD&A, annual report, "
                                "financial statements)."
                            ),
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Optional. Earliest report date, YYYY-MM-DD.",
                        },
                        "date_to": {
                            "type": "string",
                            "description": "Optional. Latest report date, YYYY-MM-DD.",
                        },
                        "exact_match": {
                            "type": "boolean",
                            "description": (
                                "If true, company/project names must match "
                                "exactly (case-insensitive). If false (default), "
                                "partial substring matching is used."
                            ),
                            "default": False,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results to return (default 20, max 100).",
                            "default": 20,
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "reports_get_content",
                "description": (
                    "Fetch the actual content of a stored report given its "
                    "document_id (obtained from reports_vector_search or "
                    "reports_search_technical). If the report has been processed "
                    "into the vector database, returns its reconstructed full "
                    "text. If not yet processed, returns an accessible file URL "
                    "and detected format (PDF/HTML/text) that can be passed to "
                    "the document processing tools. Always returns report "
                    "metadata. Handles missing/inaccessible documents gracefully."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "integer",
                            "description": (
                                "The numeric document identifier returned by "
                                "reports_vector_search or reports_search_technical."
                            ),
                        },
                        "include_full_text": {
                            "type": "boolean",
                            "description": (
                                "If true (default), return the reconstructed "
                                "full report text when available. If false, "
                                "return only metadata and the file URL."
                            ),
                            "default": True,
                        },
                        "max_chars": {
                            "type": "integer",
                            "description": (
                                "Maximum characters of report text to return "
                                f"(default {DEFAULT_MAX_CONTENT_CHARS}). Text is "
                                "truncated past this limit."
                            ),
                            "default": DEFAULT_MAX_CONTENT_CHARS,
                        },
                    },
                    "required": ["document_id"],
                },
            },
        ]

    # ------------------------------------------------------------------ #
    # Tool routing
    # ------------------------------------------------------------------ #

    def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Route a tool call to its handler (called by ClaudeClient)."""
        try:
            if tool_name == "reports_vector_search":
                return self._vector_search(parameters)
            if tool_name == "reports_search_technical":
                return self._search_technical(parameters)
            if tool_name == "reports_get_content":
                return self._get_content(parameters)
            return {"error": f"Unknown tool: {tool_name}"}
        except ValueError as e:
            # Predictable input errors (bad dates, etc.) - surface cleanly.
            return {"error": str(e)}
        except Exception as e:
            logger.error("NI43101ReportsServer.%s failed: %s", tool_name, e, exc_info=True)
            return {"error": f"Tool '{tool_name}' failed: {e}"}

    # Alias for any caller that uses handle_tool_call (DocumentSearchServer style).
    handle_tool_call = execute_tool

    # ------------------------------------------------------------------ #
    # Tool 1: Vector database query
    # ------------------------------------------------------------------ #

    def _vector_search(self, params: Dict) -> Dict:
        """Semantic search over the ChromaDB document_chunks collection."""
        query = (params.get("query") or "").strip()
        if not query:
            return {"error": "query is required"}

        company_name = params.get("company_name")
        document_type = params.get("document_type")
        date_from = self._parse_date(params.get("date_from"), "date_from")
        date_to = self._parse_date(params.get("date_to"), "date_to")
        max_results = max(1, min(int(params.get("max_results", 5)), 20))

        # Over-fetch so post-filtering still leaves enough — but only when a
        # type/date filter is actually set. search_documents already fetches 4x
        # internally, so this multiplier compounds straight into the MMR and
        # cross-encoder candidate counts: a blanket ×4 here made one tool call
        # cost ~30s warm (measured 2026-09-04); ×2 covers access-control drops.
        has_post_filter = bool(document_type or date_from or date_to)
        fetch_n = max_results * (4 if has_post_filter else 2)
        raw_results = self.rag_manager.search_documents(
            query=query,
            n_results=fetch_n,
            filter_company=company_name,
        )

        if not raw_results:
            return {
                "found": False,
                "query": query,
                "message": f"No NI 43-101 report content found for: {query}",
                "results": [],
            }

        # Resolve access control + extra metadata in one batched DB query.
        doc_ids = {
            r.get("metadata", {}).get("document_id")
            for r in raw_results
            if r.get("metadata", {}).get("document_id")
        }
        docs_by_id = {
            d.id: d
            for d in self._visible_documents().filter(id__in=doc_ids).select_related(
                "company", "project"
            )
        }

        formatted: List[Dict] = []
        for result in raw_results:
            meta = result.get("metadata", {}) or {}
            doc = docs_by_id.get(meta.get("document_id"))
            if doc is None:
                # Either not visible to this user, or chunk's document was removed.
                continue

            # Post-filter by report type.
            if document_type and doc.document_type != document_type:
                continue

            # Post-filter by date range.
            if doc.document_date:
                if date_from and doc.document_date < date_from:
                    continue
                if date_to and doc.document_date > date_to:
                    continue

            formatted.append({
                "rank": len(formatted) + 1,
                "relevance_score": self._relevance_score(result),
                "text": result.get("text", ""),
                "source": {
                    "document_id": doc.id,
                    "document_title": doc.title,
                    "document_date": (
                        doc.document_date.isoformat() if doc.document_date else None
                    ),
                    "company": doc.company.name if doc.company_id else None,
                    "document_type": doc.get_document_type_display(),
                    "report_status": "processed",  # vector hits exist only for processed reports
                },
            })
            if len(formatted) >= max_results:
                break

        return {
            "found": bool(formatted),
            "query": query,
            "filters_applied": {
                "company_name": company_name,
                "document_type": document_type,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
            },
            "total_results": len(formatted),
            "results": formatted,
            "hint": (
                "Pass any source.document_id to reports_get_content to retrieve "
                "the full report."
            ),
        }

    # ------------------------------------------------------------------ #
    # Tool 2: PostgreSQL structured report search
    # ------------------------------------------------------------------ #

    def _search_technical(self, params: Dict) -> Dict:
        """Structured Django-ORM search over the documents table."""
        company_name = params.get("company_name")
        project_name = params.get("project_name")
        commodity = params.get("commodity")
        document_type = params.get("document_type")
        date_from = self._parse_date(params.get("date_from"), "date_from")
        date_to = self._parse_date(params.get("date_to"), "date_to")
        exact_match = bool(params.get("exact_match", False))
        limit = max(1, min(int(params.get("limit", 20)), 100))

        qs = self._visible_documents().select_related("company", "project")

        # Report type: explicit type, else default to the technical-report set.
        if document_type:
            qs = qs.filter(document_type=document_type)
        else:
            qs = qs.filter(document_type__in=TECHNICAL_REPORT_TYPES)

        # Company / project name matching (exact or partial, parameterized ORM).
        if company_name:
            lookup = "company__name__iexact" if exact_match else "company__name__icontains"
            qs = qs.filter(**{lookup: company_name.strip()})
        if project_name:
            lookup = "project__name__iexact" if exact_match else "project__name__icontains"
            qs = qs.filter(**{lookup: project_name.strip()})

        if commodity:
            qs = qs.filter(project__primary_commodity__iexact=commodity.strip())

        if date_from:
            qs = qs.filter(document_date__gte=date_from)
        if date_to:
            qs = qs.filter(document_date__lte=date_to)

        total = qs.count()
        documents = qs.order_by("-document_date")[:limit]

        # Which of these documents have been processed into the vector store?
        doc_ids = [d.id for d in documents]
        processed_ids = set(
            DocumentChunk.objects.filter(document_id__in=doc_ids)
            .values_list("document_id", flat=True)
            .distinct()
        )

        results: List[Dict] = []
        for doc in documents:
            summary = self._document_summary(doc)
            summary["report_status"] = (
                "processed" if doc.id in processed_ids else "not_processed"
            )
            results.append(summary)

        if not results:
            return {
                "found": False,
                "message": "No technical reports matched the given criteria.",
                "filters_applied": {
                    "company_name": company_name,
                    "project_name": project_name,
                    "commodity": commodity,
                    "document_type": document_type or TECHNICAL_REPORT_TYPES,
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                    "exact_match": exact_match,
                },
                "results": [],
            }

        return {
            "found": True,
            "total_matches": total,
            "returned": len(results),
            "results": results,
            "hint": (
                "Pass a document_id to reports_get_content to retrieve the "
                "report's content or URL. 'report_status' shows whether the "
                "report's text is already searchable in the vector database."
            ),
        }

    # ------------------------------------------------------------------ #
    # Tool 3: Document content retrieval
    # ------------------------------------------------------------------ #

    def _get_content(self, params: Dict) -> Dict:
        """Fetch report content (or an accessible URL) for a given document_id."""
        document_id = params.get("document_id")
        if document_id is None:
            return {"error": "document_id is required"}
        try:
            document_id = int(document_id)
        except (TypeError, ValueError):
            return {"error": f"document_id must be an integer, got '{document_id}'"}

        include_full_text = bool(params.get("include_full_text", True))
        max_chars = max(1_000, min(int(params.get("max_chars", DEFAULT_MAX_CONTENT_CHARS)),
                                   200_000))

        # Look up the document, distinguishing "missing" from "no access".
        doc = (
            Document.objects.select_related("company", "project")
            .filter(id=document_id)
            .first()
        )
        if doc is None:
            return {
                "found": False,
                "error": f"No document found with document_id={document_id}.",
            }
        if not doc.is_public and not self._is_staff:
            return {
                "found": False,
                "error": (
                    f"Document {document_id} is not publicly accessible and the "
                    "current user lacks permission to view it."
                ),
            }

        metadata = self._document_summary(doc)

        # Pull processed chunks (ordered) to reconstruct the report text.
        chunks = list(
            DocumentChunk.objects.filter(document=doc)
            .order_by("chunk_index")
            .values_list("text", flat=True)
        )

        if include_full_text and chunks:
            full_text = "\n".join(chunks)
            truncated = len(full_text) > max_chars
            return {
                "found": True,
                "content_type": "full_text",
                "metadata": metadata,
                "report_status": "processed",
                "chunk_count": len(chunks),
                "content": full_text[:max_chars],
                "truncated": truncated,
                "char_count": min(len(full_text), max_chars),
                "note": (
                    "Reconstructed from overlapping RAG chunks; minor text "
                    "overlap between sections is expected."
                    + (
                        " Output truncated -- increase max_chars to retrieve more."
                        if truncated else ""
                    )
                ),
            }

        # Not processed (or caller only wants the URL): return an accessible URL.
        if not doc.file_url:
            return {
                "found": True,
                "content_type": "unavailable",
                "metadata": metadata,
                "report_status": "not_processed",
                "error": (
                    "This report has not been processed into the vector "
                    "database and has no stored file URL, so its content "
                    "cannot be retrieved."
                ),
            }

        return {
            "found": True,
            "content_type": "url",
            "metadata": metadata,
            "report_status": "processed" if chunks else "not_processed",
            "file_url": doc.file_url,
            "file_format": metadata["file_format"],
            "note": (
                "Full text was not returned"
                + (" (include_full_text=false)." if not include_full_text
                   else " because this report has not been processed yet.")
                + " Use this URL with the document processing tools "
                "(e.g. document_process_ni43101_hybrid) to extract its content."
            ),
        }
