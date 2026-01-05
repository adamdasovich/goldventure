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

## Automatic Document Discovery and Processing

The system now supports automatic document discovery and processing! You can run this via command line or schedule it as a periodic task.

### Option 1: Management Command (One-Time Run)

Run the auto-discovery command to crawl company websites, discover documents, and process them automatically:

```bash
cd backend

# Process all companies with websites
python manage.py auto_process_documents --all

# Process specific company by ID
python manage.py auto_process_documents --company-id 123

# Process specific company by name
python manage.py auto_process_documents --company-name "1911 Gold"

# Only discover specific document types
python manage.py auto_process_documents --all --types ni43101,news_release

# Limit number of companies
python manage.py auto_process_documents --all --limit 10

# Dry run (discover but don't create jobs)
python manage.py auto_process_documents --all --dry-run

# Skip documents already in system
python manage.py auto_process_documents --all --skip-existing

# Auto-process after discovery
python manage.py auto_process_documents --all --auto-process
```

**What This Does:**
1. Crawls company website(s) using Crawl4AI
2. Discovers all documents (NI 43-101, news releases, presentations, etc.)
3. Creates DocumentProcessingJob records
4. Optionally auto-processes the queue
5. Shows detailed progress and summary

**Example Output:**
```
================================================================================
Processing: 1911 Gold Corporation
================================================================================
  ✓ Discovered 12 documents

  NI43101: 2 documents
    - 2024 NI 43-101 Technical Report - True North Gold Project...
    - 2023 Updated Resource Estimate - Apex Mine...

  NEWS_RELEASE: 5 documents
    - Q3 2024 Drilling Results - True North Project...
    - Resource Estimate Update - November 2024...
    ... and 3 more

  PRESENTATION: 3 documents
    - November 2024 Corporate Presentation...
    ... and 2 more

  ✓ Created 12 processing jobs

================================================================================
SUMMARY
================================================================================
Companies processed: 1
Documents discovered: 12
Jobs created: 12
```

### Option 2: Scheduled Periodic Task (Celery Beat)

Set up automatic daily/weekly document discovery using Celery Beat.

**1. Configure Celery Beat Schedule**

Edit `backend/goldventure/settings.py` and add:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'auto-discover-documents-weekly': {
        'task': 'core.tasks.auto_discover_and_process_documents_task',
        'schedule': crontab(day_of_week=1, hour=2, minute=0),  # Every Monday at 2 AM
        'kwargs': {
            'limit': 20,  # Process 20 companies per run
            'document_types': ['ni43101', 'news_release', 'presentation']  # Optional filter
        }
    },
}
```

**Schedule Options:**
```python
# Daily at 3 AM
'schedule': crontab(hour=3, minute=0)

# Every Monday at 2 AM
'schedule': crontab(day_of_week=1, hour=2, minute=0)

# Twice weekly (Monday and Thursday at 2 AM)
'schedule': crontab(day_of_week='1,4', hour=2, minute=0)

# Every day at midnight
'schedule': crontab(hour=0, minute=0)
```

**2. Start Celery Beat**

```bash
cd backend

# Start Celery worker (in one terminal)
celery -A goldventure worker --loglevel=info

# Start Celery Beat scheduler (in another terminal)
celery -A goldventure beat --loglevel=info
```

**3. Monitor Automatic Processing**

Check the Celery logs to see when automatic discovery runs:
```
[2024-01-15 02:00:00] Auto-discovery task: Processing 20 companies
[2024-01-15 02:05:23] Crawling 1911 Gold Corporation...
[2024-01-15 02:05:45]   Discovered 12 documents
[2024-01-15 02:05:46]   Created 8 new processing jobs
...
[2024-01-15 02:25:10] Auto-discovery completed: 20 companies, 156 documents discovered, 89 jobs created
```

### Option 3: Cron Job (Server Deployment)

For production deployment, you can use cron to run the management command:

```bash
# Edit crontab
crontab -e

# Add this line to run every Monday at 2 AM
0 2 * * 1 cd /var/www/goldventure/backend && source venv/bin/activate && python manage.py auto_process_documents --all --limit 20 --skip-existing --auto-process

# Or run daily at 3 AM
0 3 * * * cd /var/www/goldventure/backend && source venv/bin/activate && python manage.py auto_process_documents --all --limit 10 --skip-existing --auto-process
```

### Tips for Automatic Processing

**Best Practices:**
- Use `--skip-existing` to avoid reprocessing documents
- Use `--limit` to prevent overwhelming the system
- Filter `--types` to prioritize certain document types
- Schedule during off-peak hours (e.g., 2-4 AM)
- Monitor logs for errors

**Resource Considerations:**
- Each company crawl takes 30-60 seconds
- Document processing takes 5-90 minutes per document
- Limit concurrent processing to avoid overload
- Recommended: 10-20 companies per scheduled run

**Example Weekly Schedule:**
```bash
# Monday: Process NI 43-101 reports only
python manage.py auto_process_documents --all --types ni43101 --limit 10 --auto-process

# Wednesday: Process news releases and presentations
python manage.py auto_process_documents --all --types news_release,presentation --limit 20 --auto-process

# Friday: Process financial statements and fact sheets
python manage.py auto_process_documents --all --types financial_statement,fact_sheet --limit 20 --auto-process
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
