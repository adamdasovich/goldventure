# Financing Detection System

Automatic detection and flagging of news releases containing financing-related keywords for superuser review.

## Overview

The financing detection system automatically scans all incoming news releases for financing-related keywords and flags them for superuser review. Superusers can then confirm if the news represents actual financing and create Financing records directly from the flagged news.

## Features

✅ **Automatic Keyword Detection** - Scans news release titles for 11+ financing keywords
✅ **Superuser Review Queue** - Dedicated interface for reviewing flagged news
✅ **One-Click Financing Creation** - Create Financing records directly from flagged news
✅ **False Positive Dismissal** - Dismiss non-financing news with notes
✅ **Audit Trail** - Tracks who reviewed, when, and links to created financing records
✅ **Status Tracking** - Three states: Pending, Confirmed Financing, False Positive

## How It Works

### 1. Automatic Detection

When news releases are scraped (via `scrape_company_news_task`), the system checks titles for these keywords:

- private placement
- financing
- funding round
- capital raise
- bought deal
- equity financing
- debt financing
- flow-through
- warrant
- subscription
- offering

If any keywords are detected, a `NewsReleaseFlag` record is automatically created with:
- Link to the news release
- List of detected keywords
- Status: 'pending'
- Timestamp of detection

**Location:** [backend/core/tasks.py:315-347](backend/core/tasks.py)

### 2. Superuser Review

Superusers access the review interface at `/admin/news-flags`

**Features:**
- Filter by status (Pending, Reviewed Financing, Reviewed False Positive)
- View company name, news title, release date
- See detected keywords
- Link to original news release
- Review actions: Create Financing or Dismiss

**Location:** [frontend/app/admin/news-flags/page.tsx](frontend/app/admin/news-flags/page.tsx)

### 3. Financing Creation

When superuser confirms financing:

1. Click "Create Financing" on flagged news
2. Fill in financing details:
   - Financing Type (Private Placement, Bought Deal, etc.)
   - Status (Announced, Closing, Closed, Cancelled)
   - Amount Raised (USD)
   - Price Per Share
   - Shares Issued
   - Warrant Details (if applicable)
   - Lead Agent/Broker
   - Use of Proceeds
   - Notes
3. Submit to create Financing record
4. Flag is automatically marked as 'reviewed_financing'
5. Financing record is linked to the news release
6. Audit trail is created

### 4. False Positive Dismissal

If news doesn't represent actual financing:

1. Click "Dismiss" on flagged news
2. Optionally add notes explaining why (e.g., "Mentions warrant exercises in context of unrelated announcement")
3. Submit to mark as 'reviewed_false_positive'
4. Flag removed from pending queue

## Database Schema

### NewsReleaseFlag Model

```python
class NewsReleaseFlag(models.Model):
    # Relationships
    news_release = OneToOneField(NewsRelease)  # The flagged news
    reviewed_by = ForeignKey(User, null=True)  # Reviewer
    created_financing = ForeignKey(Financing, null=True)  # Linked financing if confirmed

    # Detection metadata
    flagged_at = DateTimeField(auto_now_add=True)
    detected_keywords = JSONField(default=list)  # List of matched keywords

    # Review workflow
    status = CharField(choices=['pending', 'reviewed_financing', 'reviewed_false_positive'])
    reviewed_at = DateTimeField(null=True)
    review_notes = TextField(blank=True)

    # Methods
    def mark_as_financing(reviewer, financing_record, notes)
    def dismiss_as_false_positive(reviewer, notes)
```

**Location:** [backend/core/models.py:4479-4569](backend/core/models.py)

## API Endpoints

### List Flagged News Releases

```bash
GET /api/news-flags/?status=pending
Authorization: Bearer {token}
```

**Query Parameters:**
- `status` - Filter by status (pending, reviewed_financing, reviewed_false_positive)

**Response:**
```json
[
  {
    "id": 1,
    "company_name": "1911 Gold Corporation",
    "company_id": 5,
    "news_release_id": 123,
    "news_title": "1911 Gold Announces $5M Private Placement",
    "news_url": "https://www.1911gold.com/news/2024-01-financing.pdf",
    "news_date": "2024-01-15",
    "detected_keywords": ["private placement", "financing"],
    "status": "pending",
    "flagged_at": "2024-01-16T02:30:00Z",
    "reviewed_by": null,
    "reviewed_at": null,
    "created_financing_id": null,
    "review_notes": ""
  }
]
```

### Create Financing from Flag

```bash
POST /api/news-flags/{id}/create-financing/
Authorization: Bearer {token}
Content-Type: application/json

{
  "financing_type": "private_placement",
  "status": "announced",
  "announced_date": "2024-01-15",
  "amount_raised_usd": "5000000.00",
  "price_per_share": "0.50",
  "shares_issued": 10000000,
  "has_warrants": true,
  "warrant_strike_price": "0.65",
  "use_of_proceeds": "Exploration and working capital",
  "lead_agent": "Canaccord Genuity",
  "notes": "Full exercise of over-allotment option",
  "review_notes": "Confirmed financing from news release"
}
```

**Response:**
```json
{
  "message": "Financing created successfully",
  "financing_id": 42,
  "flag_id": 1
}
```

### Dismiss Flag as False Positive

```bash
POST /api/news-flags/{id}/dismiss/
Authorization: Bearer {token}
Content-Type: application/json

{
  "notes": "Mention of warrants in context of existing financing only"
}
```

**Response:**
```json
{
  "message": "Flag dismissed successfully",
  "flag_id": 1
}
```

## Admin Interface

### Access

Navigate to: **http://localhost:3000/admin/news-flags**

**Requirements:**
- Must be authenticated
- Must be superuser (`user.is_superuser = True`)

### Interface Features

**Status Tabs:**
- Pending - News awaiting review
- Reviewed Financing - Confirmed financings with linked records
- Reviewed False Positive - Dismissed flags

**For Each Flagged News:**
- Company name
- News title
- Release date and flagged date
- Detected keywords (highlighted)
- Link to original news release
- Actions (if pending):
  - "Create Financing" - Opens financing form
  - "Dismiss" - Opens dismissal modal

**Financing Creation Form:**
- All financing fields pre-populated where possible
- Announced date defaults to news release date
- Press release URL automatically linked
- Review notes tracked

**Dismissal Modal:**
- Optional notes field
- Confirmation required
- Tracks reviewer and timestamp

## Example Workflow

### Scenario: Private Placement Announcement

1. **Automatic Detection** (2:00 AM Monday via Celery)
   ```
   News scraped: "Emerald Peak Announces $3.5M Private Placement"
   Keywords detected: ['private placement', 'financing']
   → NewsReleaseFlag created (status='pending')
   ```

2. **Superuser Review** (9:00 AM Monday)
   - Superuser logs into /admin/news-flags
   - Sees 1 pending flag for Emerald Peak
   - Clicks "Create Financing"

3. **Financing Creation**
   - Form pre-filled with news date
   - Superuser fills in:
     - Amount: $3,500,000
     - Price: $0.42
     - Shares: 8,333,333
     - Warrants: Yes, strike $0.55
     - Lead Agent: Red Cloud Securities
   - Submits form

4. **Result**
   - Financing record created (#47)
   - Flag marked as 'reviewed_financing'
   - Link: NewsReleaseFlag → Financing #47
   - Audit: Reviewed by admin@example.com on 2024-01-16

5. **Platform Impact**
   - Financing appears in company profile
   - Available via API: `/api/financings/47/`
   - Visible to investors
   - Included in financing analytics

## Celery Beat Schedule

The financing detection is part of the recommended schedule architecture:

```python
# config/settings.py

CELERY_BEAT_SCHEDULE = {
    'auto-discover-documents-weekly': {
        'task': 'core.tasks.auto_discover_and_process_documents_task',
        'schedule': crontab(day_of_week=1, hour=2, minute=0),  # Monday 2 AM
        'kwargs': {
            'limit': 10,
            'document_types': ['ni43101', 'news_release', 'presentation']
        }
    },
}
```

**Frequency:** Weekly (every Monday at 2 AM)
**Scope:** Processes 10 companies per week, includes news releases
**Detection:** Automatic financing keyword scanning during news scraping

## Monitoring

### Check for Pending Flags

```bash
# Via Django shell
python manage.py shell

from core.models import NewsReleaseFlag
pending_count = NewsReleaseFlag.objects.filter(status='pending').count()
print(f"Pending flags: {pending_count}")
```

### Review Detection Stats

```python
from core.models import NewsReleaseFlag

stats = {
    'total': NewsReleaseFlag.objects.count(),
    'pending': NewsReleaseFlag.objects.filter(status='pending').count(),
    'confirmed': NewsReleaseFlag.objects.filter(status='reviewed_financing').count(),
    'false_positives': NewsReleaseFlag.objects.filter(status='reviewed_false_positive').count()
}

print(stats)
# Output:
# {
#   'total': 45,
#   'pending': 3,
#   'confirmed': 38,
#   'false_positives': 4
# }
```

### Check Latest Flags

```python
latest = NewsReleaseFlag.objects.filter(status='pending').order_by('-flagged_at')[:5]
for flag in latest:
    print(f"{flag.news_release.company.name}: {flag.news_release.title}")
    print(f"  Keywords: {', '.join(flag.detected_keywords)}")
```

## Configuration

### Customize Detection Keywords

Edit the keyword list in [backend/core/tasks.py:316-328](backend/core/tasks.py):

```python
financing_keywords = [
    'private placement',
    'financing',
    'funding round',
    'capital raise',
    'bought deal',
    'equity financing',
    'debt financing',
    'flow-through',
    'warrant',
    'subscription',
    'offering',
    # Add more keywords here
]
```

### Adjust Auto-Processing Schedule

Edit [backend/config/settings.py:298-305](backend/config/settings.py):

```python
'auto-discover-documents-weekly': {
    'schedule': crontab(day_of_week=1, hour=2, minute=0),  # Change schedule
    'kwargs': {
        'limit': 10,  # Change company limit
        'document_types': ['news_release']  # Only process news if desired
    }
},
```

## Migration

Migration file: [backend/core/migrations/0031_add_news_release_flag_model.py](backend/core/migrations/0031_add_news_release_flag_model.py)

Run migration:
```bash
cd backend
python manage.py migrate
```

## Troubleshooting

### No Flags Being Created

**Possible causes:**
1. News scraping not running
2. No financing-related news in scraped releases
3. Keywords not matching news titles

**Debug:**
```python
# Check if news scraping is working
from core.models import NewsRelease
recent_news = NewsRelease.objects.order_by('-created_at')[:10]
for news in recent_news:
    print(f"{news.company.name}: {news.title}")

# Manually test keyword detection
title = "Company Announces $5M Private Placement"
keywords = ['private placement', 'financing']
detected = [kw for kw in keywords if kw in title.lower()]
print(f"Detected: {detected}")
```

### Flags Not Appearing in Admin

**Possible causes:**
1. User not superuser
2. Frontend API call failing
3. Backend not serving flags

**Debug:**
```bash
# Check user permissions
python manage.py shell
from core.models import User
user = User.objects.get(username='admin')
print(f"Is superuser: {user.is_superuser}")

# Test API endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/news-flags/?status=pending
```

### Financing Creation Failing

**Possible causes:**
1. Missing required fields
2. Invalid data format
3. Permission issues

**Debug:**
```python
# Check financing creation manually
from core.models import Financing, Company
from decimal import Decimal
from datetime import date

company = Company.objects.first()
financing = Financing.objects.create(
    company=company,
    financing_type='private_placement',
    status='announced',
    announced_date=date.today(),
    amount_raised_usd=Decimal('5000000.00')
)
print(f"Created: {financing.id}")
```

## Support

For issues or questions:
1. Check Django logs: `backend/logs/`
2. Check Celery logs for scraping issues
3. Review NewsReleaseFlag records in Django admin
4. Check browser console for frontend errors

## Related Documentation

- [ADMIN_DOCUMENT_PROCESSING.md](ADMIN_DOCUMENT_PROCESSING.md) - Document processing guide
- [backend/core/models.py](backend/core/models.py) - Model definitions
- [backend/core/tasks.py](backend/core/tasks.py) - Celery tasks
- [backend/core/views.py](backend/core/views.py) - API views
