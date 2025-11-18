# Admin Document Processing Guide

This guide shows you how to use the new admin interface to easily process NI 43-101 reports and other documents.

## Features

✅ **Single URL Processing** - Add one document at a time
✅ **Batch URL Processing** - Add multiple URLs in one go
✅ **Auto-detection** - Company and project names detected from documents
✅ **Progress Tracking** - Real-time status updates
✅ **RAG Integration** - Automatic chunking and embedding for semantic search
✅ **Queue Management** - Process multiple documents sequentially

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
3. Select document type (usually "NI 43-101 Technical Report")
4. (Optional) Enter company/project name
5. Click **"Save"**

#### Option B: Batch URLs (Recommended!)

1. Click **"Batch Add"** button at the top
2. Paste multiple URLs, one per line:
   ```
   https://www.1911gold.com/_resources/reports/2024-43-101-True-North-Gold-Project.pdf
   https://www.astonbayholdings.com/...
   https://anothercompany.com/...
   ```
3. Select document type
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

For each processed NI 43-101 report:

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

## Example Batch Job

Here's an example of processing multiple reports:

```
# Create list of URLs
URLs:
https://www.1911gold.com/_resources/reports/2024-43-101-True-North-Gold-Project.pdf
https://www.astonbayholdings.com/assets/docs/Storm-Copper-NI43-101-2023.pdf
https://example.com/another-report.pdf

# Settings
Document Type: NI 43-101 Technical Report
Company Name: (leave blank for auto-detection)
Project Name: (leave blank for auto-detection)

# Result
→ 3 jobs created
→ Processing takes ~90-180 minutes total (sequential)
→ All documents searchable via chatbot when complete
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

## Support

Questions? Issues? Contact support or check the logs at:
- Django logs: `backend/logs/`
- Processing errors: Check job error_message field
