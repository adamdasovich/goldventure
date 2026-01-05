# Email Notification System

Automatic email alerts for critical system events: NI 43-101 report discoveries and financing flag detections.

## Overview

The system automatically sends email notifications to `adamdasovich@gmail.com` for two key events:
1. **NI 43-101 Report Discovery** - When a new NI 43-101 technical report is successfully processed
2. **Financing Flag Detection** - When a news release is flagged for potential financing announcement

## Configuration

### Email Settings

Located in `backend/config/settings.py`:

```python
# Email backend - SMTP configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'Junior Mining Intelligence <noreply@juniorminingintelligence.com>'

# Notification Recipients
ADMIN_EMAIL = 'adamdasovich@gmail.com'
NI43101_NOTIFICATION_EMAIL = 'adamdasovich@gmail.com'
FINANCING_NOTIFICATION_EMAIL = 'adamdasovich@gmail.com'
```

### Environment Variables

Add these to your `.env` file for production:

```bash
EMAIL_HOST_USER=your-smtp-username@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password

# Optional: Override notification recipients
NI43101_NOTIFICATION_EMAIL=adamdasovich@gmail.com
FINANCING_NOTIFICATION_EMAIL=adamdasovich@gmail.com
```

**Gmail Setup:**
1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App-Specific Password at https://myaccount.google.com/apppasswords
3. Use the app password as `EMAIL_HOST_PASSWORD`

## Notification Types

### 1. NI 43-101 Report Discovery

**Trigger:** When a new NI 43-101 technical report is successfully processed

**Location:** `backend/core/tasks.py` - `process_single_job()` function

**Email Content:**
- Company name and ticker
- Document title
- Document date
- Document URL
- Processing confirmation message

**Example Subject:** `🔔 New NI 43-101 Report Discovered: 1911 Gold Corporation`

**Timing:** Sent immediately after successful document processing (typically 30-90 minutes after discovery)

### 2. Financing Flag Detection

**Trigger:** When a news release is automatically flagged for potential financing

**Location:** `backend/core/tasks.py` - `scrape_company_news_task()` function

**Email Content:**
- Company name and ticker
- News release title
- Release date
- News release URL
- Detected financing keywords
- Link to admin review interface

**Example Subject:** `🚩 Financing Alert: Emerald Peak Resources - News Release Flagged`

**Timing:** Sent immediately when financing keywords are detected in a new news release

**Keywords Detected:**
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

## Email Templates

### NI 43-101 Discovery Email

```
Subject: 🔔 New NI 43-101 Report Discovered: [Company Name]

New NI 43-101 Report Discovered

Company: [Company Name]
Ticker: [Ticker Symbol]
Document Title: [Report Title]
Document Date: [Date]
URL: [Document URL]

This NI 43-101 report was automatically discovered and will be processed for
resource estimates, economic data, and added to the RAG system for chatbot queries.

---
Junior Mining Intelligence Platform
Automated Document Discovery System
```

### Financing Flag Email

```
Subject: 🚩 Financing Alert: [Company Name] - News Release Flagged

🚩 Potential Financing Detected

Company: [Company Name]
Ticker: [Ticker Symbol]
News Title: [News Release Title]
Release Date: [Release Date]
URL: [News Release URL]

Detected Keywords: [keyword1], [keyword2], [keyword3]

⚡ Action Required:
Review this news release at: https://juniorminingintelligence.com/admin/news-flags

This news release was automatically flagged by the financing detection system
based on keywords in the title. Please review and confirm if this represents
an actual financing announcement.

---
Junior Mining Intelligence Platform
Automated Financing Detection System
```

## Notification Workflow

### NI 43-101 Report Discovery Flow

```
1. Weekly Celery Beat runs auto-discovery (Monday 2 AM)
   ↓
2. System crawls 10 company websites
   ↓
3. Discovers NI 43-101 report
   ↓
4. Creates DocumentProcessingJob
   ↓
5. Processes document (30-90 minutes)
   ↓
6. Successfully completes processing
   ↓
7. 📧 Email sent to adamdasovich@gmail.com
   ↓
8. Document available in database & RAG system
```

### Financing Flag Detection Flow

```
1. Weekly Celery Beat runs auto-discovery (Monday 2 AM)
   ↓
2. System scrapes news releases
   ↓
3. Detects financing keywords in news title
   ↓
4. Creates NewsReleaseFlag record
   ↓
5. 📧 Email sent immediately to adamdasovich@gmail.com
   ↓
6. Admin reviews flag at /admin/news-flags
   ↓
7. Admin creates Financing record or dismisses
```

## Notification Functions

### send_ni43101_discovery_notification()

**Location:** `backend/core/notifications.py`

**Usage:**
```python
from core.notifications import send_ni43101_discovery_notification

# After successful NI 43-101 processing
document = Document.objects.get(id=document_id)
if document.company:
    send_ni43101_discovery_notification(document, document.company)
```

**Parameters:**
- `document`: Document instance (NI 43-101 report)
- `company`: Company instance

### send_financing_flag_notification()

**Location:** `backend/core/notifications.py`

**Usage:**
```python
from core.notifications import send_financing_flag_notification

# After creating NewsReleaseFlag
flag = NewsReleaseFlag.objects.create(...)
send_financing_flag_notification(flag, company, news_release)
```

**Parameters:**
- `flag`: NewsReleaseFlag instance
- `company`: Company instance
- `news_release`: NewsRelease instance

## Testing

### Test NI 43-101 Notification

```python
# Django shell
python manage.py shell

from core.models import Document, Company
from core.notifications import send_ni43101_discovery_notification

# Get a test document
document = Document.objects.filter(document_type='ni43101').first()
if document and document.company:
    send_ni43101_discovery_notification(document, document.company)
```

### Test Financing Flag Notification

```python
# Django shell
python manage.py shell

from core.models import NewsReleaseFlag, NewsRelease, Company
from core.notifications import send_financing_flag_notification

# Get a test flag
flag = NewsReleaseFlag.objects.filter(status='pending').first()
if flag:
    send_financing_flag_notification(
        flag,
        flag.news_release.company,
        flag.news_release
    )
```

### Test Console Backend (Development)

For testing without sending real emails:

```python
# In settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

This will print emails to the console instead of sending them.

## Troubleshooting

### Emails Not Being Sent

**Check 1: Email Configuration**
```python
python manage.py shell

from django.conf import settings
print(f"Email Backend: {settings.EMAIL_BACKEND}")
print(f"Email Host: {settings.EMAIL_HOST}")
print(f"Email User: {settings.EMAIL_HOST_USER}")
print(f"NI43101 Recipient: {settings.NI43101_NOTIFICATION_EMAIL}")
print(f"Financing Recipient: {settings.FINANCING_NOTIFICATION_EMAIL}")
```

**Check 2: SMTP Connection**
```python
from django.core.mail import send_mail

send_mail(
    'Test Email',
    'This is a test email from Junior Mining Intelligence.',
    'noreply@juniorminingintelligence.com',
    ['adamdasovich@gmail.com'],
    fail_silently=False,
)
```

**Check 3: Gmail App Password**
- Ensure you're using an App-Specific Password, not your regular Gmail password
- Verify 2FA is enabled on your Gmail account
- Generate new app password if needed: https://myaccount.google.com/apppasswords

### Emails Going to Spam

**Solutions:**
1. Add `noreply@juniorminingintelligence.com` to your contacts
2. Mark first email as "Not Spam"
3. Create a Gmail filter to always inbox emails from the platform

**Gmail Filter:**
- From: noreply@juniorminingintelligence.com
- Action: Never send to Spam, Always mark as important

### Notification Not Triggered

**NI 43-101 Notifications:**
- Check if document processing completed successfully
- Verify `document_type == 'ni43101'`
- Check server logs for errors

**Financing Flag Notifications:**
- Verify news scraping is running
- Check if keywords match news title
- Ensure flag was newly created (not duplicate)

## Monitoring

### Check Sent Notifications

```python
# Check recent NI 43-101 discoveries
from core.models import Document
recent_ni43101 = Document.objects.filter(
    document_type='ni43101'
).order_by('-created_at')[:5]

for doc in recent_ni43101:
    print(f"{doc.company.name}: {doc.title} - {doc.created_at}")
```

```python
# Check recent financing flags
from core.models import NewsReleaseFlag
recent_flags = NewsReleaseFlag.objects.filter(
    status='pending'
).order_by('-flagged_at')[:5]

for flag in recent_flags:
    print(f"{flag.news_release.company.name}: {flag.news_release.title}")
    print(f"  Keywords: {', '.join(flag.detected_keywords)}")
    print(f"  Flagged: {flag.flagged_at}")
```

## Customization

### Change Notification Recipients

Edit `backend/config/settings.py`:

```python
# Send NI 43-101 notifications to different email
NI43101_NOTIFICATION_EMAIL = os.getenv('NI43101_NOTIFICATION_EMAIL', 'geologist@company.com')

# Send financing notifications to different email
FINANCING_NOTIFICATION_EMAIL = os.getenv('FINANCING_NOTIFICATION_EMAIL', 'cfo@company.com')
```

### Add Additional Notification Types

1. Create notification function in `backend/core/notifications.py`
2. Call function at appropriate trigger point
3. Add recipient setting in `settings.py`

Example:
```python
def send_resource_update_notification(resource, company):
    """Notify when resource estimate is updated"""
    subject = f'📊 Resource Update: {company.name}'
    # ... email content ...
    send_mail(subject, message, from_email, [settings.RESOURCE_NOTIFICATION_EMAIL])
```

### Customize Email Templates

Edit the HTML and plain text templates in `backend/core/notifications.py`:

- Modify styling (colors, fonts, layout)
- Add additional information fields
- Change branding or logos
- Adjust subject line format

## Production Deployment

### Email Service Providers

For production, consider using:

**SendGrid:**
```python
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
```

**AWS SES:**
```python
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'us-east-1'
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
```

**Mailgun:**
```python
EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
ANYMAIL = {
    "MAILGUN_API_KEY": os.getenv('MAILGUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": "mg.yourdomain.com",
}
```

### Best Practices

1. **Use Environment Variables** for all sensitive credentials
2. **Monitor Email Delivery** rates and bounces
3. **Set Up SPF/DKIM/DMARC** records for better deliverability
4. **Rate Limit** notifications to avoid overwhelming recipient
5. **Log All Notifications** for audit trail
6. **Test Before Deployment** using console backend

## Support

For issues with email notifications:
1. Check Django logs: `backend/logs/`
2. Verify email configuration in settings
3. Test SMTP connection manually
4. Check spam folder
5. Review Gmail app password setup

## Related Documentation

- [FINANCING_DETECTION.md](FINANCING_DETECTION.md) - Financing detection system
- [ADMIN_DOCUMENT_PROCESSING.md](ADMIN_DOCUMENT_PROCESSING.md) - Document processing
- Django Email Documentation: https://docs.djangoproject.com/en/stable/topics/email/
