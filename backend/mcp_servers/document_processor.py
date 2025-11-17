"""
Document Processor MCP Server
Processes NI 43-101 technical reports and other mining documents using Claude's PDF vision
Automatically extracts resource estimates, economics, and project details
"""

import requests
import base64
import anthropic
from typing import Dict, List, Any
from datetime import datetime
from decimal import Decimal
from .base import BaseMCPServer
from django.conf import settings
from core.models import Company, Project, Document, ResourceEstimate, EconomicStudy
from django.db.models import Q


class DocumentProcessorServer(BaseMCPServer):
    """
    MCP Server for processing mining technical reports with Claude.
    Extracts structured data from PDFs and stores in database.
    """

    def __init__(self, company_id: int = None, user=None):
        super().__init__(company_id, user)
        self.claude_client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )

    def _register_tools(self):
        """Register all document processing tools"""

        # Tool 1: Process NI 43-101 report from URL
        self.register_tool(
            name="document_process_ni43101",
            description=(
                "Process a NI 43-101 technical report PDF and extract all key data. "
                "Automatically extracts: resource estimates, mineral reserves, economic studies, "
                "project details, metallurgy, infrastructure, and recommendations. "
                "Data is stored in the database and linked to the company/project. "
                "Use this when you have a URL to a NI 43-101 report."
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
                        "description": "Project name (optional)",
                        "default": None
                    },
                    "document_date": {
                        "type": "string",
                        "description": "Document date in YYYY-MM-DD format (optional)"
                    }
                },
                "required": ["document_url", "company_name"]
            },
            handler=self._process_ni43101
        )

        # Tool 2: Extract resource estimates from document
        self.register_tool(
            name="document_extract_resources",
            description=(
                "Extract mineral resource estimates from a technical report PDF. "
                "Returns detailed resource tables with tonnage, grade, and contained metal. "
                "Supports M&I (Measured & Indicated) and Inferred categories."
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
            handler=self._extract_resources
        )

        # Tool 3: Extract economic study data
        self.register_tool(
            name="document_extract_economics",
            description=(
                "Extract economic study data from PEA, PFS, or FS reports. "
                "Returns NPV, IRR, capex, opex, payback period, production rates, "
                "and other key economic metrics."
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
            handler=self._extract_economics
        )

        # Tool 4: List uploaded documents
        self.register_tool(
            name="document_list_documents",
            description=(
                "List all uploaded documents for a company or project. "
                "Filter by document type (NI 43-101, presentations, financials, etc.)"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Company name or ticker symbol (optional)"
                    },
                    "document_type": {
                        "type": "string",
                        "description": "Filter by type: ni43101, presentation, financial_stmt, etc."
                    }
                },
                "required": []
            },
            handler=self._list_documents
        )

        # Tool 5: Summarize document content
        self.register_tool(
            name="document_summarize",
            description=(
                "Generate a comprehensive summary of any mining document. "
                "Returns executive summary, key highlights, and main findings. "
                "Works with any PDF document type."
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
                        "description": "Specific focus area: resources, economics, geology, metallurgy, all",
                        "default": "all"
                    }
                },
                "required": ["document_url"]
            },
            handler=self._summarize_document
        )

    # =============================================================================
    # HELPER METHODS
    # =============================================================================

    def _fetch_pdf_as_base64(self, url: str) -> str:
        """Fetch PDF from URL and convert to base64"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return base64.standard_b64encode(response.content).decode('utf-8')
        except Exception as e:
            raise Exception(f"Failed to fetch PDF: {str(e)}")

    def _analyze_pdf_with_claude(self, pdf_base64: str, prompt: str, max_tokens: int = 4000) -> str:
        """Send PDF to Claude for analysis"""
        try:
            message = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )
            return message.content[0].text
        except Exception as e:
            raise Exception(f"Claude PDF analysis failed: {str(e)}")

    # =============================================================================
    # TOOL HANDLERS
    # =============================================================================

    def _process_ni43101(self, document_url: str, company_name: str,
                        project_name: str = None, document_date: str = None) -> Dict:
        """Process complete NI 43-101 report and extract all data"""
        try:
            # Find company
            company = Company.objects.filter(
                Q(name__icontains=company_name) | Q(ticker_symbol__iexact=company_name)
            ).first()

            if not company:
                return {"error": f"Company '{company_name}' not found"}

            # Fetch PDF
            try:
                pdf_base64 = self._fetch_pdf_as_base64(document_url)
            except Exception as e:
                return {"error": str(e)}

            # Comprehensive extraction prompt
            prompt = """Analyze this NI 43-101 technical report and extract ALL key data in JSON format.

Extract the following sections:

1. DOCUMENT INFO:
   - title
   - report_date
   - authors
   - qualified_persons

2. PROJECT INFO:
   - project_name
   - location (country, province/state)
   - property_size_hectares
   - ownership_percentage

3. MINERAL RESOURCES (all categories):
   - category (Measured, Indicated, Inferred)
   - mineral_type (gold, silver, copper, etc.)
   - tonnage_mt (million tonnes)
   - grade (g/t for precious, % for base)
   - contained_metal (oz or tonnes)

4. MINERAL RESERVES (if available):
   - category (Proven, Probable)
   - mineral_type
   - tonnage_mt
   - grade
   - contained_metal

5. ECONOMIC STUDY (PEA/PFS/FS):
   - study_type
   - npv_usd_millions (at discount rate)
   - discount_rate
   - irr_percent
   - capex_initial_usd_millions
   - capex_sustaining_usd_millions
   - opex_per_tonne
   - payback_period_years
   - mine_life_years
   - annual_production (gold_oz, silver_oz, copper_tonnes, etc.)

6. KEY FINDINGS:
   - executive_summary (2-3 paragraphs)
   - main_highlights (bullet points)
   - recommendations

Return ONLY valid JSON. Use null for missing values. Be precise with numbers."""

            # Analyze with Claude
            response_text = self._analyze_pdf_with_claude(pdf_base64, prompt, max_tokens=4000)

            # Parse JSON response
            import json
            try:
                # Try to extract JSON from response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    extracted_data = json.loads(response_text[json_start:json_end])
                else:
                    extracted_data = json.loads(response_text)
            except json.JSONDecodeError:
                return {
                    "warning": "Could not parse structured data",
                    "raw_analysis": response_text[:1000]
                }

            # Store document record
            doc_date = datetime.strptime(document_date, "%Y-%m-%d").date() if document_date else datetime.now().date()

            doc_info = extracted_data.get('DOCUMENT_INFO', {})
            document = Document.objects.create(
                company=company,
                title=doc_info.get('title', 'NI 43-101 Technical Report'),
                document_type='ni43101',
                document_date=doc_date,
                file_url=document_url,
                description=f"Processed by Claude AI on {datetime.now().strftime('%Y-%m-%d')}"
            )

            # Store project if provided
            project = None
            project_info = extracted_data.get('PROJECT_INFO', {})
            if project_info.get('project_name'):
                project, created = Project.objects.get_or_create(
                    company=company,
                    name=project_info['project_name'],
                    defaults={
                        'location': f"{project_info.get('location', 'Unknown')}",
                        'project_stage': 'exploration',
                        'commodity_primary': 'gold'
                    }
                )
                document.project = project
                document.save()

            # Store resource estimates
            resources_added = 0
            for res in extracted_data.get('MINERAL_RESOURCES', []):
                if res.get('tonnage_mt') and res.get('grade'):
                    ResourceEstimate.objects.create(
                        project=project or Project.objects.filter(company=company).first(),
                        estimate_date=doc_date,
                        resource_category=res.get('category', 'inferred').lower(),
                        mineral_type=res.get('mineral_type', 'gold'),
                        tonnage_mt=Decimal(str(res['tonnage_mt'])),
                        grade_gpt=Decimal(str(res['grade'])) if 'gold' in res.get('mineral_type', '').lower() else None,
                        grade_percent=Decimal(str(res['grade'])) if 'copper' in res.get('mineral_type', '').lower() else None,
                        contained_metal_oz=int(res.get('contained_metal', 0)) if res.get('contained_metal') else None
                    )
                    resources_added += 1

            # Store economic study
            econ_data = extracted_data.get('ECONOMIC_STUDY', {})
            if econ_data.get('npv_usd_millions'):
                EconomicStudy.objects.create(
                    project=project or Project.objects.filter(company=company).first(),
                    study_type=econ_data.get('study_type', 'pea'),
                    study_date=doc_date,
                    npv_usd=Decimal(str(econ_data['npv_usd_millions'])) * Decimal('1000000'),
                    discount_rate=Decimal(str(econ_data.get('discount_rate', 5))),
                    irr=Decimal(str(econ_data.get('irr_percent', 0))) if econ_data.get('irr_percent') else None,
                    capex_initial=Decimal(str(econ_data.get('capex_initial_usd_millions', 0))) * Decimal('1000000'),
                    payback_period_years=Decimal(str(econ_data.get('payback_period_years', 0))) if econ_data.get('payback_period_years') else None,
                    mine_life_years=int(econ_data.get('mine_life_years', 0)) if econ_data.get('mine_life_years') else None
                )

            return {
                "success": True,
                "document_id": document.id,
                "company": company.name,
                "project": project.name if project else None,
                "extracted_data": {
                    "resources_added": resources_added,
                    "economic_study": "stored" if econ_data.get('npv_usd_millions') else "not found",
                    "document_info": doc_info,
                    "project_info": project_info,
                    "key_findings": extracted_data.get('KEY_FINDINGS', {})
                },
                "message": "NI 43-101 report processed and data stored successfully"
            }

        except Exception as e:
            return {"error": f"Processing failed: {str(e)}"}

    def _extract_resources(self, document_url: str) -> Dict:
        """Extract only resource estimates from document"""
        try:
            pdf_base64 = self._fetch_pdf_as_base64(document_url)

            prompt = """Extract ALL mineral resource estimates from this technical report.

Return a JSON array with this structure:
[
  {
    "category": "Measured|Indicated|Inferred",
    "mineral_type": "gold|silver|copper|zinc|etc",
    "tonnage_mt": <number in million tonnes>,
    "grade": <number>,
    "grade_unit": "g/t|%",
    "contained_metal": <number>,
    "contained_unit": "oz|tonnes",
    "cutoff_grade": <number if specified>
  }
]

Be precise with numbers. Include all resource categories found."""

            response_text = self._analyze_pdf_with_claude(pdf_base64, prompt, max_tokens=2000)

            import json
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            resources = json.loads(response_text[json_start:json_end])

            return {
                "success": True,
                "resource_count": len(resources),
                "resources": resources,
                "source": document_url
            }

        except Exception as e:
            return {"error": f"Resource extraction failed: {str(e)}"}

    def _extract_economics(self, document_url: str) -> Dict:
        """Extract economic study data from document"""
        try:
            pdf_base64 = self._fetch_pdf_as_base64(document_url)

            prompt = """Extract economic study data from this mining report.

Return JSON with this structure:
{
  "study_type": "PEA|PFS|FS",
  "base_case": {
    "npv_usd_millions": <number>,
    "discount_rate": <number>,
    "irr_percent": <number>,
    "payback_years": <number>
  },
  "capital_costs": {
    "initial_capex_usd_millions": <number>,
    "sustaining_capex_usd_millions": <number>
  },
  "operating_costs": {
    "opex_per_tonne": <number>,
    "cash_cost_per_oz": <number if applicable>
  },
  "production": {
    "mine_life_years": <number>,
    "annual_production_gold_oz": <number if gold>,
    "annual_production_copper_tonnes": <number if copper>
  },
  "assumptions": {
    "gold_price_usd": <number>,
    "exchange_rate": <number if CAD>
  }
}

Use null for missing values. Be precise."""

            response_text = self._analyze_pdf_with_claude(pdf_base64, prompt, max_tokens=2000)

            import json
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            economics = json.loads(response_text[json_start:json_end])

            return {
                "success": True,
                "economics": economics,
                "source": document_url
            }

        except Exception as e:
            return {"error": f"Economics extraction failed: {str(e)}"}

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

    def _summarize_document(self, document_url: str, focus: str = "all") -> Dict:
        """Generate comprehensive summary of document"""
        try:
            pdf_base64 = self._fetch_pdf_as_base64(document_url)

            focus_prompts = {
                "resources": "Focus on mineral resource and reserve estimates",
                "economics": "Focus on economic analysis, NPV, IRR, costs, and production",
                "geology": "Focus on geology, mineralization, and exploration results",
                "metallurgy": "Focus on metallurgical testing and processing methods",
                "all": "Cover all key aspects comprehensively"
            }

            prompt = f"""Provide a comprehensive summary of this mining technical report.

{focus_prompts.get(focus, focus_prompts['all'])}.

Structure your summary as:

**EXECUTIVE SUMMARY** (2-3 paragraphs)

**KEY HIGHLIGHTS** (5-7 bullet points of most important findings)

**PROJECT DETAILS**
- Location and ownership
- Development stage
- Mineral types

**MINERAL RESOURCES** (if present)
- Summary of tonnage and grades
- Resource categories

**ECONOMICS** (if present)
- NPV and IRR
- Capital and operating costs
- Production targets

**RECOMMENDATIONS** (if present)
- Main recommendations from the report

Be concise but thorough. Focus on facts and numbers."""

            response_text = self._analyze_pdf_with_claude(pdf_base64, prompt, max_tokens=3000)

            return {
                "success": True,
                "summary": response_text,
                "source": document_url,
                "focus": focus
            }

        except Exception as e:
            return {"error": f"Summarization failed: {str(e)}"}
