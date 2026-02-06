"""
Hybrid Document Processor MCP Server (Docling + Claude)
Combines Docling's structure extraction with Claude's intelligent interpretation
for maximum accuracy in NI 43-101 report processing.

Now enhanced with Recursive Language Model (RLM) support for processing
documents that exceed context windows (100+ pages).

Based on: "Recursive Language Models" (Zhang, Kraska, Khattab - arXiv:2512.24601)
"""

import logging
import requests

logger = logging.getLogger(__name__)
import anthropic
from typing import Dict, List, Any, Tuple
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import tempfile
import json
import re
from urllib.parse import urlparse

from docling.document_converter import DocumentConverter
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem

from .base import BaseMCPServer
from .rlm_processor import RLMProcessor, DecompositionStrategy
from django.conf import settings
from core.models import Company, Project, Document, ResourceEstimate, EconomicStudy
from core.security_utils import check_url_safety as is_safe_url
from django.db.models import Q


class HybridDocumentProcessor(BaseMCPServer):
    """
    Hybrid MCP Server combining Docling (structure) + Claude (intelligence).

    Pipeline:
    1. Docling extracts tables, text, and structure from PDF
    2. Claude interprets the extracted data with context
    3. Results stored in database with full traceability

    Enhanced with RLM (Recursive Language Model) support for long documents:
    - Documents under 50 pages: Standard single-pass processing
    - Documents over 50 pages: RLM recursive decomposition and aggregation
    """

    # Page threshold for using RLM processing
    RLM_PAGE_THRESHOLD = 50

    def __init__(self, company_id: int = None, user=None):
        super().__init__(company_id, user)
        self.claude_client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.doc_converter = DocumentConverter()
        self.rlm_processor = RLMProcessor()

    def _register_tools(self):
        """Register all document processing tools"""

        # Tool 1: Process NI 43-101 with hybrid approach
        self.register_tool(
            name="document_process_ni43101_hybrid",
            description=(
                "Process NI 43-101 technical report using hybrid Docling+Claude approach. "
                "Docling extracts tables and structure, Claude interprets the data. "
                "Automatically stores: resource estimates, economic studies, project details. "
                "Provides highest accuracy for complex mining reports."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "document_url": {
                        "type": "string",
                        "description": "URL to the PDF document"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Company name or ticker symbol"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Project name (optional)"
                    }
                },
                "required": ["document_url", "company_name"]
            },
            handler=self._process_ni43101_hybrid
        )

        # Tool 2: Extract resource tables with Docling
        self.register_tool(
            name="document_extract_resource_tables",
            description=(
                "Extract resource estimate tables from technical reports using Docling. "
                "Returns structured table data with tonnage, grade, and metal content. "
                "More accurate than text-based extraction for complex tables."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "document_url": {
                        "type": "string",
                        "description": "URL to the PDF document"
                    }
                },
                "required": ["document_url"]
            },
            handler=self._extract_resource_tables
        )

        # Tool 3: Extract economic data with hybrid approach
        self.register_tool(
            name="document_extract_economics_hybrid",
            description=(
                "Extract economic study data (NPV, IRR, capex, opex) using Docling+Claude. "
                "Docling finds tables, Claude interprets financial metrics. "
                "Handles PEA, PFS, and FS reports."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "document_url": {
                        "type": "string",
                        "description": "URL to the PDF document"
                    }
                },
                "required": ["document_url"]
            },
            handler=self._extract_economics_hybrid
        )

        # Tool 4: Smart document summary with structure awareness
        self.register_tool(
            name="document_summarize_structured",
            description=(
                "Generate intelligent summary using document structure. "
                "Docling identifies sections, Claude summarizes content. "
                "Returns executive summary, key findings, and recommendations."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "document_url": {
                        "type": "string",
                        "description": "URL to the PDF document"
                    },
                    "focus": {
                        "type": "string",
                        "description": "Focus area: all, resources, economics, geology",
                        "default": "all"
                    }
                },
                "required": ["document_url"]
            },
            handler=self._summarize_structured
        )

        # Tool 5: List documents (same as before)
        self.register_tool(
            name="document_list_documents",
            description=(
                "List all uploaded documents for a company or project. "
                "Filter by document type (NI 43-101, presentations, etc.)"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name or ticker (optional)"
                    },
                    "document_type": {
                        "type": "string",
                        "description": "Document type filter"
                    }
                },
                "required": []
            },
            handler=self._list_documents
        )

        # Tool 6: Process with RLM (Recursive Language Model)
        self.register_tool(
            name="document_process_ni43101_rlm",
            description=(
                "Process NI 43-101 using Recursive Language Model (RLM) approach. "
                "Best for documents over 50 pages. Decomposes document into sections, "
                "processes each recursively, then aggregates with validation. "
                "Based on arXiv:2512.24601 research paper."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "document_url": {
                        "type": "string",
                        "description": "URL to the PDF document"
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Company name or ticker symbol"
                    },
                    "project_name": {
                        "type": "string",
                        "description": "Project name (optional)"
                    },
                    "decomposition_strategy": {
                        "type": "string",
                        "description": "Strategy: hybrid (default), section, page, semantic",
                        "default": "hybrid"
                    },
                    "validate": {
                        "type": "boolean",
                        "description": "Run validation pass (default: true)",
                        "default": True
                    }
                },
                "required": ["document_url", "company_name"]
            },
            handler=self._process_ni43101_rlm
        )

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    def _download_pdf(self, url: str) -> Path:
        """Download PDF to temporary file with retry logic and proper headers"""
        import time

        # Use realistic browser headers to avoid 403 blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,application/octet-stream,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': '/'.join(url.split('/')[:3]) + '/',  # Set referer to domain root
        }

        max_retries = 3
        last_error = None

        # Validate URL is safe (prevent SSRF)
        if not is_safe_url(url):
            raise Exception(f"URL validation failed - potentially unsafe: {url}")

        for attempt in range(max_retries):
            try:
                # Use allow_redirects=False to manually validate redirects
                response = requests.get(url, headers=headers, timeout=60, allow_redirects=False)

                # Handle redirects manually to validate each destination
                redirect_count = 0
                while response.is_redirect and redirect_count < 5:
                    redirect_url = response.headers.get('Location')
                    if redirect_url and not is_safe_url(redirect_url):
                        raise Exception(f"Redirect to unsafe URL blocked: {redirect_url}")
                    response = requests.get(redirect_url, headers=headers, timeout=60, allow_redirects=False)
                    redirect_count += 1

                response.raise_for_status()

                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.write(response.content)
                temp_file.close()

                return Path(temp_file.name)
            except requests.exceptions.HTTPError as e:
                last_error = e
                if e.response.status_code == 403:
                    # Exponential backoff for 403 errors
                    wait_time = 2 ** attempt
                    logger.warning(f"[PDF DOWNLOAD] 403 Forbidden, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                elif e.response.status_code == 404:
                    # Don't retry 404s
                    raise Exception(f"Failed to download PDF: {str(e)}")
                else:
                    # Other HTTP errors - retry with backoff
                    time.sleep(2 ** attempt)
                    continue
            except requests.exceptions.Timeout:
                last_error = Exception(f"Request timed out after 60s")
                time.sleep(2 ** attempt)
                continue
            except Exception as e:
                last_error = e
                time.sleep(2 ** attempt)
                continue

        raise Exception(f"Failed to download PDF after {max_retries} attempts: {str(last_error)}")

    def _process_with_docling(self, pdf_path: Path) -> Dict:
        """Extract structure and content using Docling"""
        try:
            # Convert document
            result = self.doc_converter.convert(pdf_path)
            doc = result.document

            # Extract tables
            tables = []
            for item, _ in doc.iterate_items():
                if isinstance(item, TableItem):
                    tables.append({
                        'caption': item.caption if hasattr(item, 'caption') else None,
                        'data': item.export_to_markdown() if hasattr(item, 'export_to_markdown') else str(item)
                    })

            # Extract full text with structure
            markdown_text = doc.export_to_markdown()

            return {
                'text': markdown_text,
                'tables': tables,
                'page_count': len(doc.pages) if hasattr(doc, 'pages') else 0
            }
        except Exception as e:
            raise Exception(f"Docling processing failed: {str(e)}")

    def _filter_resource_tables(self, tables: List[Dict]) -> List[Dict]:
        """Filter and prioritize tables that likely contain resource estimates"""
        resource_keywords = [
            'resource', 'reserve', 'mineral', 'estimate', 'tonnage', 'grade',
            'measured', 'indicated', 'inferred', 'proven', 'probable',
            'category', 'classification', 'cu', 'au', 'ag', 'oz', 'g/t',
            'mt', 'kt', 'metal', 'deposit', 'zone'
        ]

        # Score each table based on resource-related content
        scored_tables = []
        for i, table in enumerate(tables):
            score = 0
            table_text = (table.get('data', '') + ' ' + str(table.get('caption', ''))).lower()

            # Skip obvious non-resource tables
            if any(skip in table_text for skip in ['table of contents', 'list of tables', 'list of figures']):
                continue

            # Score based on keyword presence
            for keyword in resource_keywords:
                if keyword in table_text:
                    score += 1

            # Boost score for tables with numeric data patterns
            import re
            if re.search(r'\d+\.?\d*\s*(mt|kt|g/t|%|oz)', table_text):
                score += 3

            # Boost score for tables with category keywords
            if any(cat in table_text for cat in ['measured', 'indicated', 'inferred', 'proven', 'probable']):
                score += 5

            if score > 0:
                scored_tables.append({
                    'table': table,
                    'score': score,
                    'index': i
                })

        # Sort by score (highest first) and return top tables
        scored_tables.sort(key=lambda x: x['score'], reverse=True)

        # Return top 20 tables, or all if fewer
        top_tables = [item['table'] for item in scored_tables[:20]]

        # If we found fewer than 5 high-scoring tables, add some unscored tables for context
        if len(top_tables) < 5:
            remaining = [t for t in tables[:30] if t not in top_tables]
            top_tables.extend(remaining[:10])

        return top_tables

    def _ask_claude(self, prompt: str, context: str, max_tokens: int = 3000) -> str:
        """Ask Claude to interpret extracted data"""
        try:
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": f"{context}\n\n{prompt}"
                }]
            )
            return message.content[0].text
        except Exception as e:
            raise Exception(f"Claude analysis failed: {str(e)}")

    # =============================================================================
    # TOOL HANDLERS
    # =============================================================================

    def _process_ni43101_hybrid(self, document_url: str, company_name: str,
                                project_name: str = None) -> Dict:
        """Process NI 43-101 using Docling + Claude hybrid approach.

        Automatically uses RLM (Recursive Language Model) processing for
        documents over 50 pages to ensure comprehensive extraction.
        """
        try:
            # Find company
            company = Company.objects.filter(
                Q(name__icontains=company_name) | Q(ticker_symbol__iexact=company_name)
            ).first()

            if not company:
                return {"error": f"Company '{company_name}' not found"}

            # Step 1: Download PDF
            pdf_path = self._download_pdf(document_url)

            # Step 2: Extract with Docling
            docling_data = self._process_with_docling(pdf_path)

            # Check page count - use RLM for long documents
            page_count = docling_data.get('page_count', 0)
            if page_count > self.RLM_PAGE_THRESHOLD:
                logger.info(f"[HYBRID] Document has {page_count} pages (>{self.RLM_PAGE_THRESHOLD}), switching to RLM processing")
                pdf_path.unlink()
                return self._process_ni43101_rlm(
                    document_url=document_url,
                    company_name=company_name,
                    project_name=project_name,
                    decomposition_strategy="hybrid",
                    validate=True
                )

            # Clean up temp file
            pdf_path.unlink()

            # Step 3: Claude interprets the extracted data
            prompt = """Analyze this NI 43-101 technical report extracted by Docling.

The document has been pre-processed:
- Tables have been extracted and converted to markdown
- Text structure has been preserved
- Sections have been identified

Extract ALL key data in JSON format:

{
  "document_info": {
    "title": "...",
    "report_date": "YYYY-MM-DD",
    "authors": ["..."],
    "qualified_persons": ["..."]
  },
  "project_info": {
    "project_name": "...",
    "location": "...",
    "property_size_hectares": <number>,
    "ownership_percentage": <number>
  },
  "mineral_resources": [
    {
      "category": "Measured|Indicated|Inferred",
      "mineral_type": "gold|silver|copper|...",
      "tonnage_mt": <number>,
      "grade": <number>,
      "grade_unit": "g/t|%",
      "contained_metal": <number>,
      "contained_unit": "oz|tonnes"
    }
  ],
  "economic_study": {
    "study_type": "PEA|PFS|FS",
    "npv_usd_millions": <number>,
    "discount_rate": <number>,
    "irr_percent": <number>,
    "capex_initial_usd_millions": <number>,
    "opex_per_tonne": <number>,
    "payback_period_years": <number>,
    "mine_life_years": <number>
  },
  "key_findings": {
    "executive_summary": "...",
    "highlights": ["...", "..."],
    "recommendations": ["...", "..."]
  }
}

Return ONLY valid JSON. Use null for missing values."""

            # Filter tables to find resource-related ones
            filtered_tables = self._filter_resource_tables(docling_data['tables'])

            context = f"""DOCUMENT TEXT AND STRUCTURE:
{docling_data['text'][:15000]}

EXTRACTED TABLES ({len(docling_data['tables'])} total tables, showing {len(filtered_tables)} most relevant):
{json.dumps(filtered_tables, indent=2)[:50000]}
"""

            response_text = self._ask_claude(prompt, context, max_tokens=4000)

            # Parse JSON response - try direct parse first, then extract if needed
            try:
                # First, try to parse the entire response as JSON
                extracted_data = json.loads(response_text.strip())
            except json.JSONDecodeError:
                # Fall back to extracting JSON from response text
                try:
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        extracted_data = json.loads(response_text[json_start:json_end])
                    else:
                        raise json.JSONDecodeError("No JSON object found", response_text, 0)
                    # Validate extracted data has expected structure
                    if not isinstance(extracted_data, dict):
                        raise json.JSONDecodeError("Extracted data is not a dict", response_text, 0)
                except json.JSONDecodeError:
                    return {
                        "warning": "Could not parse structured data",
                        "raw_analysis": response_text[:1000],
                        "docling_stats": {
                            "tables_found": len(docling_data['tables']),
                            "pages": docling_data['page_count']
                        }
                    }

            # Store document
            doc_info = extracted_data.get('document_info', {})
            doc_date = datetime.now().date()
            if doc_info.get('report_date'):
                try:
                    doc_date = datetime.strptime(doc_info['report_date'], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    pass  # Use default date if parsing fails

            document = Document.objects.create(
                company=company,
                title=doc_info.get('title', 'NI 43-101 Technical Report'),
                document_type='ni43101',
                document_date=doc_date,
                file_url=document_url,
                description=f"Processed with Docling+Claude hybrid on {datetime.now().strftime('%Y-%m-%d')}"
            )

            # Store project
            project = None
            project_info = extracted_data.get('project_info', {})
            if project_info.get('project_name'):
                project, created = Project.objects.get_or_create(
                    company=company,
                    name=project_info['project_name'],
                    defaults={
                        'country': 'Unknown',  # Will be updated from location string if available
                        'project_stage': 'exploration',
                        'primary_commodity': 'gold'
                    }
                )
                document.project = project
                document.save()

            # Store resources
            resources_added = 0
            for res in extracted_data.get('mineral_resources', []):
                if res.get('tonnage_mt') and res.get('grade'):
                    try:
                        # Map mineral type to specific grade field
                        mineral_type = res.get('mineral_type', 'gold').lower()
                        grade_value = Decimal(str(res['grade']))

                        # Prepare grade fields based on mineral type
                        grade_fields = {}
                        if mineral_type in ['gold', 'au']:
                            if res.get('grade_unit') == 'g/t':
                                grade_fields['gold_grade_gpt'] = grade_value
                            if res.get('contained_metal'):
                                grade_fields['gold_ounces'] = Decimal(str(res['contained_metal']))
                        elif mineral_type in ['silver', 'ag']:
                            if res.get('grade_unit') == 'g/t':
                                grade_fields['silver_grade_gpt'] = grade_value
                            if res.get('contained_metal'):
                                grade_fields['silver_ounces'] = Decimal(str(res['contained_metal']))
                        elif mineral_type in ['copper', 'cu']:
                            if res.get('grade_unit') == '%':
                                grade_fields['copper_grade_pct'] = grade_value

                        ResourceEstimate.objects.create(
                            project=project or Project.objects.filter(company=company).first(),
                            category=res.get('category', 'inferred').lower(),
                            standard='ni43101',
                            tonnes=Decimal(str(res['tonnage_mt'])) * Decimal('1000000'),  # Convert Mt to tonnes
                            report_date=doc_date,
                            effective_date=doc_date,
                            **grade_fields
                        )
                        resources_added += 1
                    except Exception as e:
                        logger.error(f"Error storing resource: {str(e)}")

            # Store economic study
            econ_data = extracted_data.get('economic_study', {})
            econ_stored = False
            if econ_data.get('npv_usd_millions'):
                try:
                    EconomicStudy.objects.create(
                        project=project or Project.objects.filter(company=company).first(),
                        study_type=econ_data.get('study_type', 'pea').lower(),
                        study_date=doc_date,
                        npv_usd=Decimal(str(econ_data['npv_usd_millions'])) * Decimal('1000000'),
                        discount_rate=Decimal(str(econ_data.get('discount_rate', 5))),
                        irr=Decimal(str(econ_data.get('irr_percent', 0))) if econ_data.get('irr_percent') else None,
                        capex_initial=Decimal(str(econ_data.get('capex_initial_usd_millions', 0))) * Decimal('1000000'),
                        payback_period_years=Decimal(str(econ_data.get('payback_period_years', 0))) if econ_data.get('payback_period_years') else None,
                        mine_life_years=int(econ_data.get('mine_life_years', 0)) if econ_data.get('mine_life_years') else None
                    )
                    econ_stored = True
                except Exception as e:
                    logger.error(f"Error storing economics: {str(e)}")

            # Store full document text for RAG/semantic search
            chunks_stored = 0
            try:
                from .rag_utils import RAGManager
                rag_manager = RAGManager()
                full_text = docling_data['text']  # Full extracted text from Docling
                chunks_stored = rag_manager.store_document_chunks(document, full_text)
                logger.info(f"Stored {chunks_stored} chunks for semantic search")
            except Exception as e:
                logger.error(f"Error storing document chunks for RAG: {str(e)}")

            return {
                "success": True,
                "method": "Docling + Claude Hybrid",
                "document_id": document.id,
                "company": company.name,
                "project": project.name if project else None,
                "processing_stats": {
                    "tables_extracted": len(docling_data['tables']),
                    "pages_processed": docling_data['page_count'],
                    "resources_stored": resources_added,
                    "economic_study_stored": econ_stored,
                    "document_chunks_stored": chunks_stored
                },
                "extracted_data": {
                    "document_info": doc_info,
                    "project_info": project_info,
                    "key_findings": extracted_data.get('key_findings', {})
                },
                "message": "NI 43-101 processed successfully with hybrid approach"
            }

        except Exception as e:
            return {"error": f"Hybrid processing failed: {str(e)}"}
        finally:
            # Cleanup temp file if it still exists
            if 'pdf_path' in locals() and pdf_path.exists():
                pdf_path.unlink()

    def _extract_resource_tables(self, document_url: str) -> Dict:
        """Extract resource tables using Docling"""
        try:
            pdf_path = self._download_pdf(document_url)
            docling_data = self._process_with_docling(pdf_path)
            pdf_path.unlink()

            # Filter tables that look like resource estimates
            resource_tables = []
            for table in docling_data['tables']:
                table_text = str(table.get('data', '')).lower()
                if any(keyword in table_text for keyword in ['resource', 'tonnage', 'grade', 'ounces', 'measured', 'indicated', 'inferred']):
                    resource_tables.append(table)

            # Have Claude interpret the tables
            if resource_tables:
                prompt = """Extract mineral resource data from these tables.

Return JSON array:
[
  {
    "category": "Measured|Indicated|Inferred",
    "mineral_type": "gold|silver|copper|...",
    "tonnage_mt": <number>,
    "grade": <number>,
    "grade_unit": "g/t|%",
    "contained_metal": <number>,
    "contained_unit": "oz|tonnes"
  }
]"""

                context = f"RESOURCE TABLES:\n{json.dumps(resource_tables, indent=2)}"
                response = self._ask_claude(prompt, context, max_tokens=2000)

                try:
                    json_start = response.find('[')
                    json_end = response.rfind(']') + 1
                    resources = json.loads(response[json_start:json_end])
                except (json.JSONDecodeError, ValueError, TypeError):
                    resources = []

                return {
                    "success": True,
                    "tables_found": len(resource_tables),
                    "resources": resources,
                    "source": document_url
                }
            else:
                return {
                    "success": False,
                    "message": "No resource tables found",
                    "tables_scanned": len(docling_data['tables'])
                }

        except Exception as e:
            return {"error": f"Table extraction failed: {str(e)}"}

    def _extract_economics_hybrid(self, document_url: str) -> Dict:
        """Extract economic data using hybrid approach"""
        try:
            pdf_path = self._download_pdf(document_url)
            docling_data = self._process_with_docling(pdf_path)
            pdf_path.unlink()

            # Find economics-related tables
            econ_tables = []
            for table in docling_data['tables']:
                table_text = str(table.get('data', '')).lower()
                if any(keyword in table_text for keyword in ['npv', 'irr', 'capex', 'opex', 'cash flow', 'payback']):
                    econ_tables.append(table)

            prompt = """Extract economic study data.

Return JSON:
{
  "study_type": "PEA|PFS|FS",
  "base_case": {
    "npv_usd_millions": <number>,
    "discount_rate": <number>,
    "irr_percent": <number>
  },
  "capital_costs": {
    "initial_capex_usd_millions": <number>,
    "sustaining_capex_usd_millions": <number>
  },
  "operating_costs": {
    "opex_per_tonne": <number>
  },
  "production": {
    "mine_life_years": <number>,
    "annual_production": <number>
  }
}"""

            context = f"TEXT:\n{docling_data['text'][:10000]}\n\nTABLES:\n{json.dumps(econ_tables[:3], indent=2)}"
            response = self._ask_claude(prompt, context, max_tokens=2000)

            try:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                economics = json.loads(response[json_start:json_end])
            except (json.JSONDecodeError, ValueError, TypeError):
                economics = {}

            return {
                "success": True,
                "economics": economics,
                "tables_analyzed": len(econ_tables),
                "source": document_url
            }

        except Exception as e:
            return {"error": f"Economics extraction failed: {str(e)}"}

    def _summarize_structured(self, document_url: str, focus: str = "all") -> Dict:
        """Generate summary using document structure"""
        try:
            pdf_path = self._download_pdf(document_url)
            docling_data = self._process_with_docling(pdf_path)
            pdf_path.unlink()

            prompt = f"""Provide a comprehensive summary of this mining technical report.

Focus: {focus}

Structure:
**EXECUTIVE SUMMARY** (2-3 paragraphs)

**KEY HIGHLIGHTS** (5-7 bullet points)

**PROJECT DETAILS**
- Location and ownership
- Development stage

**MINERAL RESOURCES** (if present)

**ECONOMICS** (if present)

**RECOMMENDATIONS**"""

            context = f"DOCUMENT:\n{docling_data['text'][:20000]}"
            summary = self._ask_claude(prompt, context, max_tokens=3000)

            return {
                "success": True,
                "summary": summary,
                "document_stats": {
                    "pages": docling_data['page_count'],
                    "tables": len(docling_data['tables'])
                },
                "source": document_url,
                "focus": focus
            }

        except Exception as e:
            return {"error": f"Summarization failed: {str(e)}"}

    def _list_documents(self, company_name: str = None, document_type: str = None) -> Dict:
        """List uploaded documents"""
        try:
            queryset = Document.objects.all()

            if company_name:
                queryset = queryset.filter(
                    Q(company__name__icontains=company_name) |
                    Q(company__ticker_symbol__iexact=company_name)
                )

            if document_type:
                queryset = queryset.filter(document_type=document_type)

            documents = queryset.select_related('company', 'project').order_by('-document_date')

            return {
                "total_count": documents.count(),
                "documents": [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "company": doc.company.name,
                        "project": doc.project.name if doc.project else None,
                        "type": doc.document_type,
                        "date": doc.document_date.isoformat(),
                        "url": doc.file_url,
                        "description": doc.description
                    }
                    for doc in documents[:50]
                ]
            }

        except Exception as e:
            return {"error": str(e)}

    def _process_ni43101_rlm(
        self,
        document_url: str,
        company_name: str,
        project_name: str = None,
        decomposition_strategy: str = "hybrid",
        validate: bool = True
    ) -> Dict:
        """
        Process NI 43-101 using Recursive Language Model (RLM) approach.

        This method implements the RLM framework from arXiv:2512.24601:
        1. Decompose document into logical chunks
        2. Recursively process each chunk
        3. Aggregate results with conflict resolution
        4. Validate extracted data

        Best for documents over 50 pages where standard processing may miss information.
        """
        try:
            # Find company
            company = Company.objects.filter(
                Q(name__icontains=company_name) | Q(ticker_symbol__iexact=company_name)
            ).first()

            if not company:
                return {"error": f"Company '{company_name}' not found"}

            # Step 1: Download PDF
            pdf_path = self._download_pdf(document_url)

            # Step 2: Extract with Docling
            docling_data = self._process_with_docling(pdf_path)

            # Clean up temp file
            pdf_path.unlink()

            page_count = docling_data.get('page_count', 0)
            logger.info(f"[RLM] Document has {page_count} pages, {len(docling_data['tables'])} tables")

            # Step 3: Process with RLM
            strategy_map = {
                "hybrid": DecompositionStrategy.HYBRID,
                "section": DecompositionStrategy.SECTION_BASED,
                "page": DecompositionStrategy.PAGE_BASED,
                "semantic": DecompositionStrategy.SEMANTIC
            }
            strategy = strategy_map.get(decomposition_strategy, DecompositionStrategy.HYBRID)

            rlm_result = self.rlm_processor.process_document(
                document_text=docling_data['text'],
                tables=docling_data['tables'],
                strategy=strategy,
                validate=validate
            )

            # Convert to dictionary
            extracted_data = self.rlm_processor.to_dict(rlm_result)

            # Step 4: Store in database
            doc_info = extracted_data.get('document_info', {})
            doc_date = datetime.now().date()
            if doc_info.get('report_date'):
                try:
                    doc_date = datetime.strptime(doc_info['report_date'], "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    pass  # Use default date if parsing fails

            document = Document.objects.create(
                company=company,
                title=doc_info.get('title', 'NI 43-101 Technical Report'),
                document_type='ni43101',
                document_date=doc_date,
                file_url=document_url,
                description=f"Processed with RLM ({strategy.value}) on {datetime.now().strftime('%Y-%m-%d')}"
            )

            # Store project
            project = None
            project_info = extracted_data.get('project_info', {})
            if project_info.get('project_name') or project_name:
                proj_name = project_info.get('project_name') or project_name
                project, created = Project.objects.get_or_create(
                    company=company,
                    name=proj_name,
                    defaults={
                        'country': project_info.get('country', 'Unknown'),
                        'project_stage': project_info.get('stage', 'exploration'),
                        'primary_commodity': 'gold'
                    }
                )
                document.project = project
                document.save()

            # Store resources
            resources_added = 0
            for res in extracted_data.get('mineral_resources', []):
                if res.get('tonnage_mt') and res.get('grade'):
                    try:
                        mineral_type = res.get('mineral_type', 'gold').lower()
                        grade_value = Decimal(str(res['grade']))

                        grade_fields = {}
                        if mineral_type in ['gold', 'au']:
                            if res.get('grade_unit') == 'g/t':
                                grade_fields['gold_grade_gpt'] = grade_value
                            if res.get('contained_metal'):
                                grade_fields['gold_ounces'] = Decimal(str(res['contained_metal']))
                        elif mineral_type in ['silver', 'ag']:
                            if res.get('grade_unit') == 'g/t':
                                grade_fields['silver_grade_gpt'] = grade_value
                            if res.get('contained_metal'):
                                grade_fields['silver_ounces'] = Decimal(str(res['contained_metal']))
                        elif mineral_type in ['copper', 'cu']:
                            if res.get('grade_unit') == '%':
                                grade_fields['copper_grade_pct'] = grade_value

                        # Determine category
                        category = res.get('category', 'inferred').lower()
                        if res.get('is_reserve'):
                            category = 'proven' if 'proven' in category else 'probable'

                        ResourceEstimate.objects.create(
                            project=project or Project.objects.filter(company=company).first(),
                            category=category,
                            standard='ni43101',
                            tonnes=Decimal(str(res['tonnage_mt'])) * Decimal('1000000'),
                            report_date=doc_date,
                            effective_date=doc_date,
                            **grade_fields
                        )
                        resources_added += 1
                    except Exception as e:
                        logger.error(f"[RLM] Error storing resource: {str(e)}")

            # Store economic study
            econ_data = extracted_data.get('economic_study', {})
            econ_stored = False
            npv_value = econ_data.get('npv_usd_millions') or econ_data.get('npv_millions')
            if npv_value:
                try:
                    EconomicStudy.objects.create(
                        project=project or Project.objects.filter(company=company).first(),
                        study_type=econ_data.get('study_type', 'pea').lower(),
                        study_date=doc_date,
                        npv_usd=Decimal(str(npv_value)) * Decimal('1000000'),
                        discount_rate=Decimal(str(econ_data.get('discount_rate_percent') or econ_data.get('discount_rate', 5))),
                        irr=Decimal(str(econ_data.get('irr_percent', 0))) if econ_data.get('irr_percent') else None,
                        capex_initial=Decimal(str(econ_data.get('capex_initial_usd_millions', 0))) * Decimal('1000000') if econ_data.get('capex_initial_usd_millions') else None,
                        payback_period_years=Decimal(str(econ_data.get('payback_period_years', 0))) if econ_data.get('payback_period_years') else None,
                        mine_life_years=int(econ_data.get('mine_life_years', 0)) if econ_data.get('mine_life_years') else None
                    )
                    econ_stored = True
                except Exception as e:
                    logger.error(f"[RLM] Error storing economics: {str(e)}")

            # Store document chunks for RAG
            chunks_stored = 0
            try:
                from .rag_utils import RAGManager
                rag_manager = RAGManager()
                full_text = docling_data['text']
                chunks_stored = rag_manager.store_document_chunks(document, full_text)
                logger.info(f"[RLM] Stored {chunks_stored} chunks for semantic search")
            except Exception as e:
                logger.error(f"[RLM] Error storing document chunks for RAG: {str(e)}")

            # Get processing metadata
            proc_meta = extracted_data.get('processing_metadata', {})

            return {
                "success": True,
                "method": f"RLM ({strategy.value} decomposition)",
                "document_id": document.id,
                "company": company.name,
                "project": project.name if project else None,
                "rlm_stats": {
                    "chunks_processed": proc_meta.get('chunks_processed', 0),
                    "successful_extractions": proc_meta.get('successful_extractions', 0),
                    "processing_time_seconds": proc_meta.get('processing_time_seconds', 0),
                    "validation_passed": proc_meta.get('validation_passed'),
                    "decomposition_strategy": strategy.value
                },
                "processing_stats": {
                    "pages_processed": page_count,
                    "tables_extracted": len(docling_data['tables']),
                    "resources_stored": resources_added,
                    "economic_study_stored": econ_stored,
                    "document_chunks_stored": chunks_stored
                },
                "extracted_data": {
                    "document_info": doc_info,
                    "project_info": project_info,
                    "key_findings": extracted_data.get('key_findings', {}),
                    "resources_summary": f"{len(extracted_data.get('mineral_resources', []))} resource categories found"
                },
                "message": f"NI 43-101 processed successfully with RLM ({strategy.value})"
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": f"RLM processing failed: {str(e)}"}
        finally:
            if 'pdf_path' in locals() and pdf_path.exists():
                pdf_path.unlink()
