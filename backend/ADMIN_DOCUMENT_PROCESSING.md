# Admin Document Processing Guide

This guide shows you how to use the admin interface to process mining documents including NI 43-101 reports, news releases, presentations, fact sheets, and financial statements.

## Features

✅ **Single URL Processing** - Add one document at a time
✅ **Batch URL Processing** - Add multiple URLs in one go
✅ **5 Document Types Supported** - NI 43-101, PEA, News Releases, Presentations, Financial Statements, Fact Sheets
✅ **Auto-detection** - Company and project names detected from documents
✅ **Progress Tracking** - Real-time status updates
✅ **RAG Integration** - Automatic chunking and embedding for semantic search
✅ **Queue Management** - Process multiple documents sequentially
✅ **Chatbot Integration** - All processed documents queryable via Claude chatbot

## Quick Start

### 1. Access the Admin Interface

1. Start your Django server:
   ```bash
   cd backend
   python manage.py runserver
   ```

2. Go to: http://localhost:8000/admin/

3. Login with your admin credentials

4. Navigate to: **Core** → **Document processing jobs**

### 2. Add Documents

#### Option A: Single URL

1. Click **"Add document processing job"**
2. Paste the URL
3. Select document type:
   - **NI 43-101 Technical Report** - Full technical reports with resource estimates
   - **Preliminary Economic Assessment (PEA)** - Economic studies
   - **News Release** - Company news and press releases
   - **Presentation** - Corporate presentations and investor decks
   - **Financial Statement** - Annual reports, quarterly financials
   - **Fact Sheet** - Company fact sheets and summaries
4. (Optional) Enter company/project name
5. Click **"Save"**

#### Option B: Batch URLs (Recommended!)

1. Click **"Batch Add"** button at the top
2. Paste multiple URLs, one per line:
   ```
   https://www.1911gold.com/_resources/reports/2024-43-101-True-North-Gold-Project.pdf
   https://www.1911gold.com/news/2024-Q3-results.pdf
   https://www.1911gold.com/presentations/2024-11-Corporate.pdf
   ```
3. Select document type (applies to all URLs in batch)
4. (Optional) Enter company/project name (same for all)
5. Click **"Add Jobs to Queue"**

### 3. Process the Queue

1. From the job list page, click **"Process Queue"**
2. Review the pending jobs
3. Click **"Start Processing Queue"**
4. Processing runs in the background - you can close the page
5. Refresh the job list to see status updates

### 4. Monitor Progress

The job list shows:
- **Status** (Pending/Processing/Completed/Failed)
- **URL** being processed
- **Duration** for each job
- **Results** (resources and chunks created)

Status badge colors:
- 🟢 **Green** = Completed
- 🔵 **Blue** = Processing
- ⚪ **Gray** = Pending
- 🔴 **Red** = Failed

## Processing Times

| Document Size | Typical Time |
|--------------|--------------|
| Small (< 50 pages) | 15-30 minutes |
| Medium (50-150 pages) | 30-60 minutes |
| Large (150-300 pages) | 60-90 minutes |

**Note:** Docling extraction is the longest step (30-75 minutes typically)

## What Gets Stored

### For NI 43-101 Reports and PEA Documents:

1. **Structured Data:**
   - Company and Project records
   - Resource estimates (M&I, Inferred)
   - Economic studies (NPV, IRR, Capex, Opex)
   - Document metadata

2. **RAG System:**
   - 200-300 text chunks (512 tokens each)
   - Vector embeddings for semantic search
   - Stored in ChromaDB for fast retrieval

3. **Full searchability** via chatbot:
   - "What are the metallurgical recoveries?"
   - "Tell me about the drilling results"
   - "What infrastructure exists?"

### For General Documents (News, Presentations, Financial Statements, Fact Sheets):

1. **Document Record:**
   - Company linkage
   - Document metadata
   - Full text extraction via Docling

2. **RAG System:**
   - Text chunks (512 tokens each)
   - Vector embeddings for semantic search
   - Available for chatbot queries

3. **Example queries:**
   - "What did the latest news release say about drilling?"
   - "Summarize the Q3 financial results"
   - "What are the key points from the investor presentation?"
   - "What projects does the company have according to their fact sheet?"

## Example Batch Jobs

### Example 1: NI 43-101 Reports

```
# URLs
https://www.1911gold.com/_resources/reports/2024-43-101-True-North-Gold-Project.pdf
https://www.astonbayholdings.com/assets/docs/Storm-Copper-NI43-101-2023.pdf

# Settings
Document Type: NI 43-101 Technical Report
Company Name: (leave blank for auto-detection)

# Result
→ 2 jobs created
→ Processing: ~60-120 minutes (extracts resources + RAG)
→ Structured data stored + chatbot searchable
```

### Example 2: Mixed Document Types

```
# URLs (news releases, presentations, financials)
https://www.1911gold.com/news/2024-11-drilling-results.pdf
https://www.1911gold.com/presentations/2024-11-corporate.pdf
https://www.1911gold.com/financials/2024-Q3-results.pdf

# Settings
Company Name: 1911 Gold Corporation

# Result
→ 3 jobs created (select type for each)
→ Processing: ~15-30 minutes each (Docling + RAG)
→ All documents queryable via chatbot
```

### Example 3: Complete Company Document Set

```
# Comprehensive document processing for a new company
1 NI 43-101 report (technical data)
3 News releases (recent updates)
1 Corporate presentation (overview)
1 Annual report (financials)
1 Fact sheet (summary)

# Result
→ 7 jobs total
→ Total processing: ~120-180 minutes
→ Complete company knowledge base for chatbot
```

## Troubleshooting

### Job Failed?

1. Check the error message in the job details
2. Common issues:
   - **Invalid URL**: Check the PDF URL is accessible
   - **Timeout**: Document too large - contact support
   - **Parse Error**: Document format not supported

### Processing Stuck?

1. Check server logs for errors
2. Refresh the page to see if status updated
3. If truly stuck, you can manually set status back to 'pending' and retry

## Next Steps: Web Crawling with Crawl4AI

Coming soon! Automatic discovery and processing of documents from company websites.

**Planned Features:**
- Auto-discover all NI 43-101 reports on a company website
- Schedule regular crawls for new documents
- Filter by document type and date
- Batch process discovered documents

**Example:**
```python
# Future capability
crawler.discover_documents(
    url="https://www.1911gold.com",
    document_types=["ni43101", "presentation"],
    max_depth=3
)
# → Finds 15 documents
# → Adds to processing queue
# → Processes automatically
```

## API Access (Advanced)

You can also process documents via API:

```python
import requests

# Create job
response = requests.post(
    'http://localhost:8000/api/documents/process/',
    json={
        'url': 'https://example.com/report.pdf',
        'document_type': 'ni43101',
        'company_name': '1911 Gold'  # optional
    },
    headers={'Authorization': 'Token YOUR_API_TOKEN'}
)

job_id = response.json()['id']

# Check status
status = requests.get(f'http://localhost:8000/api/documents/jobs/{job_id}/')
print(status.json())
```

## Document Type Processing Details

### NI 43-101 Technical Reports & PEA
**Processing Method:** Hybrid (Docling + Claude API)
**Processing Time:** 30-90 minutes
**Extracts:**
- Resource estimates (tonnage, grade, metal content)
- Economic data (NPV, IRR, Capex, Opex)
- Metallurgical data
- Infrastructure details
**Storage:** Structured database + RAG vectors

### News Releases
**Processing Method:** Docling text extraction
**Processing Time:** 5-15 minutes
**Extracts:**
- Full text content
- Tables and figures
**Storage:** Document record + RAG vectors
**Use Cases:**
- Drilling results announcements
- Resource estimate updates
- Corporate updates
- Partnership announcements

### Corporate Presentations
**Processing Method:** Docling text extraction
**Processing Time:** 10-20 minutes
**Extracts:**
- Slide text content
- Tables and charts
**Storage:** Document record + RAG vectors
**Use Cases:**
- Investor presentations
- Project overviews
- Company snapshots

### Financial Statements
**Processing Method:** Docling text extraction
**Processing Time:** 15-30 minutes
**Extracts:**
- Full financial report text
- Financial tables
**Storage:** Document record + RAG vectors
**Use Cases:**
- Annual reports
- Quarterly financials
- MD&A sections

### Fact Sheets
**Processing Method:** Docling text extraction
**Processing Time:** 5-10 minutes
**Extracts:**
- Summary information
- Key metrics
**Storage:** Document record + RAG vectors
**Use Cases:**
- Company fact sheets
- Project summaries
- Quick reference documents

## Support

Questions? Issues? Contact support or check the logs at:
- Django logs: `backend/logs/`
- Processing errors: Check job error_message field
