"""
Recursive Language Model (RLM) Processor for NI 43-101 Reports

Based on "Recursive Language Models" (Zhang, Kraska, Khattab - arXiv:2512.24601)

Key concept: Enable LLMs to process documents up to 100x longer than context windows
by having the model programmatically:
1. Examine the input
2. Decompose it into manageable chunks
3. Recursively call itself on snippets
4. Aggregate results

This implementation applies RLMs to NI 43-101 technical mining reports, which are
typically 100-300+ pages and contain complex tables, geological data, and financial projections.
"""

import json
import anthropic
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import re

from django.conf import settings


class DecompositionStrategy(Enum):
    """Strategies for decomposing documents into processable chunks"""
    SECTION_BASED = "section"      # Split by document sections (TOC-aware)
    PAGE_BASED = "page"            # Split by page ranges
    SEMANTIC = "semantic"          # Split by semantic boundaries
    HYBRID = "hybrid"              # Combination of strategies


@dataclass
class DocumentChunk:
    """A chunk of document content for recursive processing"""
    content: str
    chunk_id: str
    chunk_type: str  # e.g., "section", "table", "summary"
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0
    page_range: Optional[tuple] = None
    section_title: Optional[str] = None


@dataclass
class ExtractionResult:
    """Result from processing a chunk"""
    chunk_id: str
    data: Dict[str, Any]
    confidence: float = 1.0
    source_pages: Optional[List[int]] = None
    raw_response: Optional[str] = None


@dataclass
class AggregatedResult:
    """Final aggregated result from all chunks"""
    document_info: Dict[str, Any] = field(default_factory=dict)
    project_info: Dict[str, Any] = field(default_factory=dict)
    mineral_resources: List[Dict[str, Any]] = field(default_factory=list)
    economic_study: Dict[str, Any] = field(default_factory=dict)
    key_findings: Dict[str, Any] = field(default_factory=dict)
    processing_metadata: Dict[str, Any] = field(default_factory=dict)


class RLMProcessor:
    """
    Recursive Language Model processor for long documents.

    Implements the RLM framework to process NI 43-101 reports that exceed
    context windows by:
    1. Decomposing the document into logical chunks
    2. Recursively processing each chunk with specialized prompts
    3. Aggregating results with conflict resolution
    4. Performing validation passes on aggregated data
    """

    # NI 43-101 section patterns for intelligent decomposition
    NI43101_SECTIONS = [
        (r"(?:1\.?\s*)?(?:summary|executive\s+summary)", "executive_summary"),
        (r"(?:2\.?\s*)?introduction", "introduction"),
        (r"(?:3\.?\s*)?reliance\s+on\s+other\s+experts", "reliance"),
        (r"(?:4\.?\s*)?property\s+description\s+(?:and|&)\s+location", "property"),
        (r"(?:5\.?\s*)?accessibility.*infrastructure", "accessibility"),
        (r"(?:6\.?\s*)?history", "history"),
        (r"(?:7\.?\s*)?geological\s+setting", "geology"),
        (r"(?:8\.?\s*)?deposit\s+types?", "deposit_type"),
        (r"(?:9\.?\s*)?mineralization", "mineralization"),
        (r"(?:10\.?\s*)?exploration", "exploration"),
        (r"(?:11\.?\s*)?drilling", "drilling"),
        (r"(?:12\.?\s*)?sample\s+preparation", "sampling"),
        (r"(?:13\.?\s*)?data\s+verification", "data_verification"),
        (r"(?:14\.?\s*)?mineral\s+(?:processing|treatment)", "mineral_processing"),
        (r"(?:15\.?\s*)?mineral\s+resource\s+estimate", "mineral_resources"),
        (r"(?:16\.?\s*)?mineral\s+reserve\s+estimate", "mineral_reserves"),
        (r"(?:17\.?\s*)?mining\s+methods?", "mining_methods"),
        (r"(?:18\.?\s*)?recovery\s+methods?", "recovery_methods"),
        (r"(?:19\.?\s*)?project\s+infrastructure", "infrastructure"),
        (r"(?:20\.?\s*)?market\s+studies?", "market"),
        (r"(?:21\.?\s*)?environmental", "environmental"),
        (r"(?:22\.?\s*)?capital\s+(?:and|&)\s+operating\s+costs?", "costs"),
        (r"(?:23\.?\s*)?economic\s+analysis", "economics"),
        (r"(?:24\.?\s*)?adjacent\s+properties", "adjacent"),
        (r"(?:25\.?\s*)?other\s+relevant\s+data", "other"),
        (r"(?:26\.?\s*)?interpretation\s+(?:and|&)\s+conclusions?", "conclusions"),
        (r"(?:27\.?\s*)?recommendations?", "recommendations"),
    ]

    # Maximum tokens per chunk (leaving room for prompts)
    MAX_CHUNK_TOKENS = 80000  # ~60k for content, rest for prompt/response

    # Token estimation ratio (chars to tokens)
    CHARS_PER_TOKEN = 4

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = model
        self.processing_log: List[Dict] = []

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text"""
        return len(text) // self.CHARS_PER_TOKEN

    def _log(self, message: str, level: str = "info", data: Dict = None):
        """Log processing steps for debugging and monitoring"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "data": data or {}
        }
        self.processing_log.append(entry)
        print(f"[RLM-{level.upper()}] {message}")

    # =========================================================================
    # PHASE 1: Document Decomposition
    # =========================================================================

    def decompose_document(
        self,
        document_text: str,
        tables: List[Dict],
        strategy: DecompositionStrategy = DecompositionStrategy.HYBRID
    ) -> List[DocumentChunk]:
        """
        Decompose a document into processable chunks.

        The RLM framework requires intelligent decomposition that:
        - Respects document structure (sections, tables)
        - Keeps related content together
        - Fits within context windows
        """
        self._log(f"Decomposing document with strategy: {strategy.value}")

        if strategy == DecompositionStrategy.SECTION_BASED:
            return self._decompose_by_sections(document_text, tables)
        elif strategy == DecompositionStrategy.PAGE_BASED:
            return self._decompose_by_pages(document_text, tables)
        elif strategy == DecompositionStrategy.SEMANTIC:
            return self._decompose_semantic(document_text, tables)
        else:  # HYBRID
            return self._decompose_hybrid(document_text, tables)

    def _decompose_by_sections(
        self,
        document_text: str,
        tables: List[Dict]
    ) -> List[DocumentChunk]:
        """Decompose by NI 43-101 standard sections"""
        chunks = []

        # Find section boundaries
        section_positions = []
        text_lower = document_text.lower()

        for pattern, section_name in self.NI43101_SECTIONS:
            for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                section_positions.append({
                    "start": match.start(),
                    "name": section_name,
                    "title": match.group(0)
                })

        # Sort by position
        section_positions.sort(key=lambda x: x["start"])

        # Extract content for each section
        for i, section in enumerate(section_positions):
            start = section["start"]
            end = section_positions[i + 1]["start"] if i + 1 < len(section_positions) else len(document_text)

            content = document_text[start:end]
            token_est = self._estimate_tokens(content)

            # If section is too large, split it further
            if token_est > self.MAX_CHUNK_TOKENS:
                sub_chunks = self._split_large_section(content, section["name"])
                chunks.extend(sub_chunks)
            else:
                chunks.append(DocumentChunk(
                    content=content,
                    chunk_id=f"section_{section['name']}",
                    chunk_type="section",
                    section_title=section["title"],
                    token_count=token_est,
                    metadata={"section_name": section["name"]}
                ))

        # Add tables as separate chunks for focused extraction
        table_chunk = self._create_table_chunk(tables)
        if table_chunk:
            chunks.append(table_chunk)

        self._log(f"Created {len(chunks)} section-based chunks")
        return chunks

    def _decompose_by_pages(
        self,
        document_text: str,
        tables: List[Dict],
        pages_per_chunk: int = 20
    ) -> List[DocumentChunk]:
        """Decompose by page ranges (uses page markers if available)"""
        chunks = []

        # Split by common page markers
        page_pattern = r'\n(?:Page\s+\d+|\d+\s*\n{2,}|\[Page\s+\d+\])'
        pages = re.split(page_pattern, document_text)

        # Group pages into chunks
        current_content = ""
        current_start_page = 1
        chunk_count = 0

        for i, page_content in enumerate(pages):
            if self._estimate_tokens(current_content + page_content) > self.MAX_CHUNK_TOKENS:
                if current_content:
                    chunks.append(DocumentChunk(
                        content=current_content,
                        chunk_id=f"pages_{current_start_page}_{i}",
                        chunk_type="page_range",
                        page_range=(current_start_page, i),
                        token_count=self._estimate_tokens(current_content)
                    ))
                    chunk_count += 1
                current_content = page_content
                current_start_page = i + 1
            else:
                current_content += page_content

        # Add remaining content
        if current_content:
            chunks.append(DocumentChunk(
                content=current_content,
                chunk_id=f"pages_{current_start_page}_end",
                chunk_type="page_range",
                page_range=(current_start_page, len(pages)),
                token_count=self._estimate_tokens(current_content)
            ))

        # Add tables
        table_chunk = self._create_table_chunk(tables)
        if table_chunk:
            chunks.append(table_chunk)

        self._log(f"Created {len(chunks)} page-based chunks")
        return chunks

    def _decompose_semantic(
        self,
        document_text: str,
        tables: List[Dict]
    ) -> List[DocumentChunk]:
        """Use Claude to identify semantic boundaries"""
        # For very long documents, first use page-based chunking
        # then ask Claude to identify key content within each chunk

        # Initial coarse chunking
        coarse_chunks = self._decompose_by_pages(document_text, [], pages_per_chunk=30)

        semantic_chunks = []
        for chunk in coarse_chunks:
            # Ask Claude to identify what type of content this contains
            classification = self._classify_chunk_content(chunk.content)
            chunk.metadata["content_types"] = classification
            semantic_chunks.append(chunk)

        # Add tables
        table_chunk = self._create_table_chunk(tables)
        if table_chunk:
            semantic_chunks.append(table_chunk)

        return semantic_chunks

    def _decompose_hybrid(
        self,
        document_text: str,
        tables: List[Dict]
    ) -> List[DocumentChunk]:
        """
        Hybrid decomposition combining section and page-based approaches.
        Best for NI 43-101 reports where structure varies.
        """
        chunks = []

        # First, try section-based decomposition
        section_chunks = self._decompose_by_sections(document_text, [])

        # If we found good section boundaries, use them
        if len(section_chunks) >= 5:
            chunks = section_chunks
        else:
            # Fall back to page-based with semantic classification
            chunks = self._decompose_semantic(document_text, [])

        # Always extract tables separately for focused analysis
        table_chunk = self._create_table_chunk(tables)
        if table_chunk:
            chunks.append(table_chunk)

        # Create a "key data" chunk with likely resource/economics sections
        key_data_chunk = self._extract_key_data_chunk(document_text)
        if key_data_chunk:
            chunks.insert(0, key_data_chunk)  # Process first

        self._log(f"Created {len(chunks)} hybrid chunks")
        return chunks

    def _split_large_section(self, content: str, section_name: str) -> List[DocumentChunk]:
        """Split a section that exceeds token limits"""
        chunks = []
        max_chars = self.MAX_CHUNK_TOKENS * self.CHARS_PER_TOKEN

        # Split at paragraph boundaries
        paragraphs = content.split('\n\n')
        current_chunk = ""
        chunk_idx = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) > max_chars:
                if current_chunk:
                    chunks.append(DocumentChunk(
                        content=current_chunk,
                        chunk_id=f"section_{section_name}_part{chunk_idx}",
                        chunk_type="section_part",
                        section_title=section_name,
                        token_count=self._estimate_tokens(current_chunk),
                        metadata={"section_name": section_name, "part": chunk_idx}
                    ))
                    chunk_idx += 1
                current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk:
            chunks.append(DocumentChunk(
                content=current_chunk,
                chunk_id=f"section_{section_name}_part{chunk_idx}",
                chunk_type="section_part",
                section_title=section_name,
                token_count=self._estimate_tokens(current_chunk),
                metadata={"section_name": section_name, "part": chunk_idx}
            ))

        return chunks

    def _create_table_chunk(self, tables: List[Dict]) -> Optional[DocumentChunk]:
        """Create a dedicated chunk for table analysis"""
        if not tables:
            return None

        # Filter to resource-related tables
        resource_keywords = [
            'resource', 'reserve', 'tonnage', 'grade', 'measured',
            'indicated', 'inferred', 'npv', 'irr', 'capex', 'economic'
        ]

        relevant_tables = []
        for table in tables:
            table_text = str(table.get('data', '')).lower()
            if any(kw in table_text for kw in resource_keywords):
                relevant_tables.append(table)

        if not relevant_tables:
            relevant_tables = tables[:10]  # Take first 10 if no keyword matches

        table_content = json.dumps(relevant_tables, indent=2)

        return DocumentChunk(
            content=table_content,
            chunk_id="tables_focused",
            chunk_type="tables",
            token_count=self._estimate_tokens(table_content),
            metadata={"table_count": len(relevant_tables)}
        )

    def _extract_key_data_chunk(self, document_text: str) -> Optional[DocumentChunk]:
        """Extract a focused chunk with likely key data (resources, economics)"""
        # Look for resource estimate and economic analysis sections
        key_patterns = [
            r'mineral\s+resource\s+estimate.*?(?=\n(?:\d+\.|\#|\*{3}|mineral\s+reserve))',
            r'economic\s+analysis.*?(?=\n(?:\d+\.|\#|\*{3}|adjacent))',
            r'summary.*?(?=\n(?:\d+\.|\#|\*{3}|introduction))',
        ]

        key_content = ""
        for pattern in key_patterns:
            matches = re.findall(pattern, document_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if len(match) > 500:  # Only include substantial matches
                    key_content += f"\n\n---\n\n{match[:20000]}"  # Limit each section

        if len(key_content) > 1000:
            return DocumentChunk(
                content=key_content[:100000],
                chunk_id="key_data_extract",
                chunk_type="key_data",
                token_count=self._estimate_tokens(key_content[:100000]),
                metadata={"extraction_type": "key_sections"}
            )

        return None

    def _classify_chunk_content(self, content: str) -> List[str]:
        """Quick classification of chunk content types"""
        content_lower = content.lower()
        types = []

        if any(kw in content_lower for kw in ['resource estimate', 'tonnage', 'grade g/t']):
            types.append("resources")
        if any(kw in content_lower for kw in ['npv', 'irr', 'capex', 'economic']):
            types.append("economics")
        if any(kw in content_lower for kw in ['geology', 'mineralization', 'deposit']):
            types.append("geology")
        if any(kw in content_lower for kw in ['drilling', 'assay', 'sample']):
            types.append("exploration")
        if any(kw in content_lower for kw in ['recommendation', 'conclusion']):
            types.append("conclusions")

        return types if types else ["general"]

    # =========================================================================
    # PHASE 2: Recursive Processing
    # =========================================================================

    def process_chunk(
        self,
        chunk: DocumentChunk,
        extraction_focus: Optional[str] = None
    ) -> ExtractionResult:
        """
        Process a single chunk using Claude.

        The RLM framework calls the model on each chunk with a specialized prompt
        that instructs it to extract specific information based on chunk type.
        """
        self._log(f"Processing chunk: {chunk.chunk_id} (type: {chunk.chunk_type})")

        # Select prompt based on chunk type
        if chunk.chunk_type == "tables":
            prompt = self._get_table_extraction_prompt()
        elif chunk.chunk_type == "key_data":
            prompt = self._get_comprehensive_extraction_prompt()
        elif extraction_focus:
            prompt = self._get_focused_extraction_prompt(extraction_focus)
        else:
            prompt = self._get_section_extraction_prompt(chunk)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": f"{prompt}\n\nCONTENT TO ANALYZE:\n{chunk.content}"
                }]
            )

            response_text = response.content[0].text

            # Parse JSON from response
            extracted_data = self._parse_json_response(response_text)

            return ExtractionResult(
                chunk_id=chunk.chunk_id,
                data=extracted_data,
                confidence=self._estimate_confidence(extracted_data),
                raw_response=response_text
            )

        except Exception as e:
            self._log(f"Error processing chunk {chunk.chunk_id}: {str(e)}", "error")
            return ExtractionResult(
                chunk_id=chunk.chunk_id,
                data={"error": str(e)},
                confidence=0.0
            )

    def _get_comprehensive_extraction_prompt(self) -> str:
        """Prompt for extracting all key data from a chunk"""
        return """Analyze this section of an NI 43-101 mining technical report.

Extract ALL available information into this JSON structure:

{
  "document_info": {
    "title": "string or null",
    "report_date": "YYYY-MM-DD or null",
    "authors": ["list of authors"],
    "qualified_persons": ["list of QPs with credentials"]
  },
  "project_info": {
    "project_name": "string or null",
    "location": "string description",
    "country": "string",
    "province_state": "string or null",
    "property_size_hectares": "number or null",
    "ownership_percentage": "number or null",
    "stage": "exploration|development|production or null"
  },
  "mineral_resources": [
    {
      "category": "measured|indicated|inferred",
      "mineral_type": "gold|silver|copper|zinc|etc",
      "tonnage_mt": "number (million tonnes)",
      "grade": "number",
      "grade_unit": "g/t|%|oz/t",
      "contained_metal": "number or null",
      "contained_unit": "oz|tonnes|lbs",
      "cutoff_grade": "number or null",
      "zone_name": "string or null"
    }
  ],
  "mineral_reserves": [
    {
      "category": "proven|probable",
      "mineral_type": "string",
      "tonnage_mt": "number",
      "grade": "number",
      "grade_unit": "string",
      "contained_metal": "number or null"
    }
  ],
  "economic_study": {
    "study_type": "PEA|PFS|FS|null",
    "npv_usd_millions": "number or null",
    "discount_rate_percent": "number or null",
    "irr_percent": "number or null",
    "capex_initial_usd_millions": "number or null",
    "capex_sustaining_usd_millions": "number or null",
    "opex_per_tonne_usd": "number or null",
    "payback_period_years": "number or null",
    "mine_life_years": "number or null",
    "gold_price_assumption": "number or null",
    "annual_production_oz": "number or null"
  },
  "key_findings": {
    "highlights": ["list of key points"],
    "risks": ["identified risks"],
    "recommendations": ["QP recommendations"]
  },
  "data_quality": {
    "has_resource_estimate": true/false,
    "has_economic_study": true/false,
    "confidence_notes": "string describing data quality"
  }
}

IMPORTANT:
- Extract ONLY what is explicitly stated in the text
- Use null for missing values, do not guess
- For resources, extract ALL categories found (measured, indicated, inferred)
- For grades, note the unit (g/t for gold, % for base metals)
- Return ONLY valid JSON, no explanatory text"""

    def _get_table_extraction_prompt(self) -> str:
        """Specialized prompt for table data extraction"""
        return """These are extracted tables from an NI 43-101 mining report.

Focus on extracting STRUCTURED DATA from resource and economic tables.

Return JSON:
{
  "mineral_resources": [
    {
      "category": "measured|indicated|inferred",
      "mineral_type": "gold|silver|copper|etc",
      "tonnage_mt": <number>,
      "grade": <number>,
      "grade_unit": "g/t|%",
      "contained_metal": <number or null>,
      "contained_unit": "oz|tonnes",
      "zone_name": "string or null"
    }
  ],
  "mineral_reserves": [
    {
      "category": "proven|probable",
      "tonnage_mt": <number>,
      "grade": <number>,
      "contained_metal": <number or null>
    }
  ],
  "economic_metrics": {
    "npv_usd_millions": <number or null>,
    "discount_rate": <number or null>,
    "irr_percent": <number or null>,
    "capex_millions": <number or null>,
    "opex_per_tonne": <number or null>,
    "mine_life_years": <number or null>
  },
  "table_notes": "any important caveats or assumptions from the tables"
}

IMPORTANT:
- Look for resource estimate tables with tonnage, grade, and contained metal
- Look for economic summary tables with NPV, IRR, costs
- Distinguish between Measured, Indicated, and Inferred categories
- Note the difference between Resources (M+I+Inf) and Reserves (P+Prob)
- Return ONLY valid JSON"""

    def _get_section_extraction_prompt(self, chunk: DocumentChunk) -> str:
        """Generate prompt based on section type"""
        section_name = chunk.metadata.get("section_name", "general")

        prompts = {
            "executive_summary": """Extract key summary information:
{
  "project_overview": "brief description",
  "key_highlights": ["list of main points"],
  "resource_summary": "brief resource description if mentioned",
  "economic_summary": "brief economics if mentioned",
  "recommendations": ["key recommendations"]
}""",
            "mineral_resources": """Extract detailed resource estimates:
{
  "mineral_resources": [
    {"category": "measured|indicated|inferred", "tonnage_mt": <num>, "grade": <num>, "grade_unit": "g/t|%", "mineral_type": "gold|etc", "contained_metal": <num>, "cutoff_grade": <num>}
  ],
  "effective_date": "YYYY-MM-DD",
  "qualified_person": "name and credentials",
  "methodology": "estimation method used",
  "assumptions": ["key assumptions"]
}""",
            "economics": """Extract economic analysis data:
{
  "study_type": "PEA|PFS|FS",
  "base_case": {"npv_millions": <num>, "discount_rate": <num>, "irr_percent": <num>},
  "capital_costs": {"initial_capex_millions": <num>, "sustaining_capex_millions": <num>},
  "operating_costs": {"total_opex_per_tonne": <num>, "mining_cost": <num>, "processing_cost": <num>},
  "production": {"mine_life_years": <num>, "annual_production": <num>, "production_unit": "oz|tonnes"},
  "price_assumptions": {"gold_usd_oz": <num>, "silver_usd_oz": <num>},
  "sensitivity": "notes on sensitivity analysis"
}""",
            "property": """Extract property/location information:
{
  "project_name": "string",
  "location": {"country": "string", "province": "string", "coordinates": "string or null"},
  "property_size": {"value": <num>, "unit": "hectares|acres"},
  "ownership": {"percentage": <num>, "structure": "description"},
  "tenure": "description of claims/permits"
}""",
            "geology": """Extract geological information:
{
  "deposit_type": "string",
  "host_rocks": ["list of rock types"],
  "mineralization_style": "description",
  "structural_controls": "description",
  "alteration": "description if present",
  "key_minerals": ["list of minerals"]
}""",
            "recommendations": """Extract recommendations:
{
  "recommendations": [
    {"priority": "high|medium|low", "description": "recommendation text", "estimated_cost": <num or null>}
  ],
  "next_steps": ["ordered list of suggested activities"],
  "budget_estimate": <total budget if mentioned>
}"""
        }

        base_prompt = prompts.get(section_name, """Extract relevant information from this section:
{
  "section_type": "identified section type",
  "key_data": {},
  "notable_points": ["list of important information"],
  "figures_tables_referenced": ["any referenced figures or tables"]
}""")

        return f"""Analyze this {section_name} section from an NI 43-101 report.

{base_prompt}

Return ONLY valid JSON. Use null for missing values."""

    def _get_focused_extraction_prompt(self, focus: str) -> str:
        """Get prompt for specific extraction focus"""
        if focus == "resources":
            return self._get_section_extraction_prompt(
                DocumentChunk("", "", "", metadata={"section_name": "mineral_resources"})
            )
        elif focus == "economics":
            return self._get_section_extraction_prompt(
                DocumentChunk("", "", "", metadata={"section_name": "economics"})
            )
        else:
            return self._get_comprehensive_extraction_prompt()

    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from Claude's response"""
        try:
            # Find JSON boundaries
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)

            # Try parsing entire response
            return json.loads(response)

        except json.JSONDecodeError:
            # Return raw response if JSON parsing fails
            return {"raw_response": response, "parse_error": True}

    def _estimate_confidence(self, data: Dict) -> float:
        """Estimate confidence in extracted data"""
        if data.get("parse_error"):
            return 0.3
        if data.get("error"):
            return 0.0

        # Higher confidence if we found key data
        confidence = 0.5

        if data.get("mineral_resources"):
            confidence += 0.2
        if data.get("economic_study") or data.get("economic_metrics"):
            confidence += 0.2
        if data.get("project_info") or data.get("project_name"):
            confidence += 0.1

        return min(confidence, 1.0)

    # =========================================================================
    # PHASE 3: Result Aggregation
    # =========================================================================

    def aggregate_results(
        self,
        results: List[ExtractionResult]
    ) -> AggregatedResult:
        """
        Aggregate extraction results from all chunks.

        The RLM framework requires intelligent aggregation that:
        - Combines data from multiple chunks
        - Resolves conflicts between extractions
        - Deduplicates resources
        - Validates consistency
        """
        self._log(f"Aggregating results from {len(results)} chunks")

        aggregated = AggregatedResult()

        # Collect all extracted data
        all_resources = []
        all_reserves = []
        all_economics = []
        all_doc_info = []
        all_project_info = []
        all_findings = []

        for result in results:
            if result.confidence < 0.3:
                continue  # Skip low-confidence results

            data = result.data

            # Collect resources
            if data.get("mineral_resources"):
                for res in data["mineral_resources"]:
                    res["_source_chunk"] = result.chunk_id
                    res["_confidence"] = result.confidence
                    all_resources.append(res)

            # Collect reserves
            if data.get("mineral_reserves"):
                for res in data["mineral_reserves"]:
                    res["_source_chunk"] = result.chunk_id
                    all_reserves.append(res)

            # Collect economics
            econ = data.get("economic_study") or data.get("economic_metrics")
            if econ:
                econ["_source_chunk"] = result.chunk_id
                econ["_confidence"] = result.confidence
                all_economics.append(econ)

            # Collect document info
            if data.get("document_info"):
                all_doc_info.append(data["document_info"])

            # Collect project info
            if data.get("project_info"):
                all_project_info.append(data["project_info"])

            # Collect findings
            if data.get("key_findings"):
                all_findings.append(data["key_findings"])

        # Aggregate each category
        aggregated.mineral_resources = self._deduplicate_resources(all_resources)
        aggregated.economic_study = self._merge_economics(all_economics)
        aggregated.document_info = self._merge_document_info(all_doc_info)
        aggregated.project_info = self._merge_project_info(all_project_info)
        aggregated.key_findings = self._merge_findings(all_findings)

        # Add reserves to resources if found
        if all_reserves:
            deduped_reserves = self._deduplicate_resources(all_reserves)
            for reserve in deduped_reserves:
                reserve["is_reserve"] = True
            aggregated.mineral_resources.extend(deduped_reserves)

        # Processing metadata
        aggregated.processing_metadata = {
            "chunks_processed": len(results),
            "successful_extractions": len([r for r in results if r.confidence > 0.3]),
            "resources_found": len(aggregated.mineral_resources),
            "has_economics": bool(aggregated.economic_study)
        }

        return aggregated

    def _deduplicate_resources(self, resources: List[Dict]) -> List[Dict]:
        """Remove duplicate resource entries"""
        if not resources:
            return []

        # Group by category and mineral type
        seen = {}
        for res in resources:
            key = (
                res.get("category", "").lower(),
                res.get("mineral_type", "").lower(),
                res.get("zone_name", "")
            )

            if key not in seen:
                seen[key] = res
            else:
                # Keep the one with higher confidence or more complete data
                existing = seen[key]
                if res.get("_confidence", 0) > existing.get("_confidence", 0):
                    seen[key] = res
                elif res.get("contained_metal") and not existing.get("contained_metal"):
                    seen[key] = res

        # Clean up internal fields
        result = []
        for res in seen.values():
            clean_res = {k: v for k, v in res.items() if not k.startswith("_")}
            result.append(clean_res)

        return result

    def _merge_economics(self, economics: List[Dict]) -> Dict:
        """Merge economic data from multiple extractions"""
        if not economics:
            return {}

        # Prefer the most complete extraction
        best = max(economics, key=lambda e: sum(1 for v in e.values() if v is not None))

        # Clean up internal fields
        return {k: v for k, v in best.items() if not k.startswith("_")}

    def _merge_document_info(self, doc_infos: List[Dict]) -> Dict:
        """Merge document info from multiple sources"""
        if not doc_infos:
            return {}

        merged = {}
        for info in doc_infos:
            for key, value in info.items():
                if value and (key not in merged or not merged[key]):
                    merged[key] = value

        return merged

    def _merge_project_info(self, project_infos: List[Dict]) -> Dict:
        """Merge project info from multiple sources"""
        if not project_infos:
            return {}

        merged = {}
        for info in project_infos:
            for key, value in info.items():
                if value and (key not in merged or not merged[key]):
                    merged[key] = value

        return merged

    def _merge_findings(self, findings: List[Dict]) -> Dict:
        """Merge key findings from multiple sections"""
        merged = {
            "highlights": [],
            "risks": [],
            "recommendations": []
        }

        seen_highlights = set()
        seen_recommendations = set()

        for finding in findings:
            for h in finding.get("highlights", []):
                if h and h not in seen_highlights:
                    merged["highlights"].append(h)
                    seen_highlights.add(h)

            for r in finding.get("risks", []):
                if r:
                    merged["risks"].append(r)

            for rec in finding.get("recommendations", []):
                rec_text = rec if isinstance(rec, str) else rec.get("description", "")
                if rec_text and rec_text not in seen_recommendations:
                    merged["recommendations"].append(rec)
                    seen_recommendations.add(rec_text)

        return merged

    # =========================================================================
    # PHASE 4: Validation Pass
    # =========================================================================

    def validate_and_refine(
        self,
        aggregated: AggregatedResult,
        original_chunks: List[DocumentChunk]
    ) -> AggregatedResult:
        """
        Final validation pass using Claude to verify extracted data.

        This is the RLM "refinement" step where the model reviews
        its own extractions for consistency and completeness.
        """
        self._log("Running validation pass")

        # Create a summary for validation
        summary = {
            "document": aggregated.document_info,
            "project": aggregated.project_info,
            "resources": aggregated.mineral_resources,
            "economics": aggregated.economic_study,
            "findings": aggregated.key_findings
        }

        # Get key data chunk for cross-reference
        key_chunk = next(
            (c for c in original_chunks if c.chunk_type == "key_data"),
            original_chunks[0] if original_chunks else None
        )

        if not key_chunk:
            return aggregated

        validation_prompt = f"""Review this extracted data from an NI 43-101 report for accuracy.

EXTRACTED DATA:
{json.dumps(summary, indent=2, default=str)}

ORIGINAL DOCUMENT EXCERPT:
{key_chunk.content[:30000]}

Check for:
1. Are the resource tonnages and grades reasonable for the deposit type?
2. Do the economics (NPV, IRR) align with what's stated?
3. Are there any obvious extraction errors?
4. Is anything important missing?

Return JSON with corrections:
{{
  "corrections": [
    {{"field": "path.to.field", "current": "value", "corrected": "new value", "reason": "why"}}
  ],
  "missing_data": ["list of important missing items"],
  "validation_passed": true/false,
  "notes": "any important observations"
}}

If everything looks correct, return {{"corrections": [], "validation_passed": true}}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": validation_prompt}]
            )

            validation_result = self._parse_json_response(response.content[0].text)

            # Apply corrections if any
            if validation_result.get("corrections"):
                aggregated = self._apply_corrections(aggregated, validation_result["corrections"])

            aggregated.processing_metadata["validation_passed"] = validation_result.get("validation_passed", True)
            aggregated.processing_metadata["validation_notes"] = validation_result.get("notes", "")

        except Exception as e:
            self._log(f"Validation pass failed: {str(e)}", "warning")
            aggregated.processing_metadata["validation_passed"] = None

        return aggregated

    def _apply_corrections(
        self,
        aggregated: AggregatedResult,
        corrections: List[Dict]
    ) -> AggregatedResult:
        """Apply validation corrections to aggregated result"""
        for correction in corrections:
            field_path = correction.get("field", "").split(".")
            corrected_value = correction.get("corrected")

            if not field_path or corrected_value is None:
                continue

            try:
                # Navigate to the field and update it
                obj = aggregated
                for part in field_path[:-1]:
                    if hasattr(obj, part):
                        obj = getattr(obj, part)
                    elif isinstance(obj, dict):
                        obj = obj.get(part, {})
                    elif isinstance(obj, list) and part.isdigit():
                        obj = obj[int(part)]

                final_key = field_path[-1]
                if hasattr(obj, final_key):
                    setattr(obj, final_key, corrected_value)
                elif isinstance(obj, dict):
                    obj[final_key] = corrected_value

                self._log(f"Applied correction: {correction['field']} -> {corrected_value}")

            except Exception as e:
                self._log(f"Failed to apply correction: {str(e)}", "warning")

        return aggregated

    # =========================================================================
    # Main Processing Pipeline
    # =========================================================================

    def process_document(
        self,
        document_text: str,
        tables: List[Dict],
        strategy: DecompositionStrategy = DecompositionStrategy.HYBRID,
        validate: bool = True
    ) -> AggregatedResult:
        """
        Main RLM processing pipeline for NI 43-101 documents.

        Implements the full Recursive Language Model framework:
        1. Decompose document into chunks
        2. Recursively process each chunk
        3. Aggregate results
        4. Validate and refine

        Args:
            document_text: Full document text (from Docling)
            tables: Extracted tables (from Docling)
            strategy: Decomposition strategy to use
            validate: Whether to run validation pass

        Returns:
            AggregatedResult with all extracted data
        """
        self._log("Starting RLM document processing")
        start_time = datetime.now()

        # Phase 1: Decompose
        chunks = self.decompose_document(document_text, tables, strategy)
        self._log(f"Document decomposed into {len(chunks)} chunks")

        # Phase 2: Recursive Processing
        results = []
        for i, chunk in enumerate(chunks):
            self._log(f"Processing chunk {i+1}/{len(chunks)}: {chunk.chunk_id}")
            result = self.process_chunk(chunk)
            results.append(result)

        # Phase 3: Aggregate
        aggregated = self.aggregate_results(results)

        # Phase 4: Validate (optional)
        if validate:
            aggregated = self.validate_and_refine(aggregated, chunks)

        # Add timing metadata
        elapsed = (datetime.now() - start_time).total_seconds()
        aggregated.processing_metadata["processing_time_seconds"] = elapsed
        aggregated.processing_metadata["strategy"] = strategy.value

        self._log(f"RLM processing complete in {elapsed:.1f}s")

        return aggregated

    def to_dict(self, result: AggregatedResult) -> Dict:
        """Convert AggregatedResult to dictionary for JSON serialization"""
        return {
            "document_info": result.document_info,
            "project_info": result.project_info,
            "mineral_resources": result.mineral_resources,
            "economic_study": result.economic_study,
            "key_findings": result.key_findings,
            "processing_metadata": result.processing_metadata
        }
