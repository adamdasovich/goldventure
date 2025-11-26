# Automated News Crawling - Scheduled Task Setup

Complete guide for automatically crawling company news releases on a schedule.

## 🎯 What This Does

Automatically runs daily/weekly to:
1. **Crawl** all company websites in your database
2. **Discover** new news releases from the last month
3. **Store** them in the NewsRelease database table
4. **Skip** duplicates (already in database)

## ✅ Django Management Command

You now have a powerful management command: `crawl_news`

### Usage Examples:

```bash
# Crawl all companies (last 6 months)
python manage.py crawl_news --all

# Crawl specific company
python manage.py crawl_news --company "1911 Gold"

# Crawl all companies (last 1 month only - recommended for daily runs)
python manage.py crawl_news --all --months 1

# Crawl with deeper search
python manage.py crawl_news --all --depth 3

# Crawl all, last 12 months, depth 3
python manage.py crawl_news --all --months 12 --depth 3
```

### Command Options:

- `--all` - Crawl all companies in database with websites
- `--company "Name"` - Crawl specific company (partial name match)
- `--months N` - Number of months to look back (default: 6)
- `--depth N` - Max crawl depth (default: 2)

## 🔄 Option 1: Windows Task Scheduler (Recommended for Windows)

### Step 1: Test the Batch File

First, make sure the batch file works:

```cmd
cd c:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend
crawl_all_companies.bat
```

### Step 2: Open Task Scheduler

1. Press `Win + R`
2. Type `taskschd.msc` and press Enter
3. Click "Create Basic Task..." in the right panel

### Step 3: Create the Task

1. **Name**: "Crawl Company News Releases"
2. **Description**: "Automatically crawls mining company websites for latest news releases"
3. **Trigger**: Daily at 2:00 AM (or your preferred time)
4. **Action**: Start a program
   - **Program/script**: `c:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend\crawl_all_companies.bat`
   - **Start in**: `c:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend`

5. **Settings**:
   - ✓ Run whether user is logged on or not
   - ✓ Run with highest privileges (if needed)
   - ✓ Stop the task if it runs longer than 1 hour

### Step 4: Test the Schedule

Right-click the task → "Run" to test it immediately.

### Recommended Schedule:

- **Daily at 2:00 AM** - For active companies releasing frequent news
- **Weekly on Monday at 6:00 AM** - For less active companies
- **First of month at 3:00 AM** - For monthly updates

## 🔄 Option 2: Cron Job (Linux/Mac)

### Edit crontab:

```bash
crontab -e
```

### Add entry:

```bash
# Run daily at 2:00 AM
0 2 * * * cd /path/to/backend && python manage.py crawl_news --all --months 1

# Run weekly on Monday at 6:00 AM
0 6 * * 1 cd /path/to/backend && python manage.py crawl_news --all --months 1

# Run first of month at 3:00 AM
0 3 1 * * cd /path/to/backend && python manage.py crawl_news --all --months 6
```

### Cron Syntax Reminder:

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── day of week (0-7, Sun=0 or 7)
│ │ │ └───── month (1-12)
│ │ └─────── day of month (1-31)
│ └───────── hour (0-23)
└─────────── minute (0-59)
```

## 🔄 Option 3: Django Q / Celery (Advanced)

For more advanced scheduling with Django:

### Install Django Q:

```bash
pip install django-q
```

### Add to settings.py:

```python
INSTALLED_APPS = [
    ...
    'django_q',
]

Q_CLUSTER = {
    'name': 'GoldVenture',
    'workers': 4,
    'timeout': 3600,
    'retry': 3600,
    'queue_limit': 50,
    'bulk': 10,
    'orm': 'default',
}
```

### Create schedule in Django:

```python
from django_q.tasks import schedule
from django_q.models import Schedule

# Schedule daily crawl
schedule('core.tasks.crawl_all_news',
         schedule_type=Schedule.DAILY,
         next_run='02:00')
```

## 📊 What Gets Crawled

### When you run `--all`:

1. Finds all companies with `website` field populated
2. For each company:
   - Crawls their website
   - Discovers news releases
   - Extracts dates from filenames
   - Stores new releases in database
   - Skips duplicates

### Example Output:

```
================================================================================
Company: 1911 Gold Corporation
Website: https://www.1911gold.com
================================================================================
Crawling website...
Found 4 news releases

Preview (latest 3):
  1. [2025-11-11] nr-20251111.pdf
  2. [2025-11-10] nr-20251110.pdf
  3. [2025-11-06] nr-20251106.pdf

Storing in database...
✓ Created: 2
⊘ Skipped: 2

================================================================================
CRAWL COMPLETE
================================================================================
Companies crawled: 2
Total created: 15
Total skipped: 3
```

## 📝 Logging (Optional)

### Enable logging to file:

Modify the batch file:

```batch
python manage.py crawl_news --all --months 1 >> crawler_log.txt 2>&1
```

This will append all output to `crawler_log.txt`.

### View logs:

```cmd
type crawler_log.txt
```

### Log rotation (to prevent huge files):

Create a PowerShell script:

```powershell
# crawler_with_log_rotation.ps1
$logFile = "crawler_log.txt"
$maxSize = 10MB

# Rotate log if > 10MB
if ((Get-Item $logFile -ErrorAction SilentlyContinue).Length -gt $maxSize) {
    Move-Item $logFile "$logFile.old" -Force
}

# Run crawler
python manage.py crawl_news --all --months 1 >> $logFile 2>&1
```

## 🔔 Email Notifications (Optional)

### Get notified when crawler finds new releases:

Modify `crawl_news.py` to send email summary:

```python
from django.core.mail import send_mail

# After crawling
if total_created > 0:
    send_mail(
        subject=f'News Crawler: {total_created} New Releases Found',
        message=f'Crawled {len(companies)} companies.\nFound {total_created} new news releases.',
        from_email='noreply@yoursite.com',
        recipient_list=['your@email.com'],
    )
```

## ⚙️ Configuration Recommendations

### For Production:

1. **Frequency**: Daily at 2-3 AM
2. **Months**: 1 month (to catch latest releases)
3. **Depth**: 2 (default, good balance)

```bash
python manage.py crawl_news --all --months 1 --depth 2
```

### For Initial Setup:

1. **Frequency**: One-time
2. **Months**: 12 (get historical data)
3. **Depth**: 3 (deeper search)

```bash
python manage.py crawl_news --all --months 12 --depth 3
```

### For Testing:

1. **Frequency**: Manual
2. **Months**: 1
3. **Company**: Specific company

```bash
python manage.py crawl_news --company "1911" --months 1
```

## 📈 Performance

| Companies | Frequency | Typical Time | New Releases |
|-----------|-----------|--------------|--------------|
| 1         | Daily     | 30-60 sec    | 0-2          |
| 5         | Daily     | 2-5 min      | 0-10         |
| 10        | Weekly    | 5-15 min     | 5-30         |
| 20        | Weekly    | 10-30 min    | 10-60        |

## 🐛 Troubleshooting

### Task doesn't run

**Check**:
1. Task Scheduler → View running tasks
2. Check "Last Run Result" column
3. View task history (Actions → Enable All Tasks History)

**Common issues**:
- Wrong path in batch file
- Python not in PATH
- Database not accessible
- Company has no website

### No news releases found

**Possible reasons**:
- Company hasn't published news recently
- News releases not in PDF format
- Date range too narrow (increase `--months`)
- Crawler can't access website (firewall/VPN)

**Try**:
```bash
# Increase depth and months
python manage.py crawl_news --company "CompanyName" --months 12 --depth 3
```

### Crawler runs but nothing stored

**Check**:
1. Company name matches exactly in database
2. Website URL is correct in database
3. Company actually has news releases in PDF format

## 📚 Database Schema

News releases are stored in the `NewsRelease` table:

```python
NewsRelease.objects.filter(
    company__name="1911 Gold Corporation",
    release_date__gte=date(2025, 1, 1)
).order_by('-release_date')
```

### View recent news via Django shell:

```python
python manage.py shell

from core.models import NewsRelease
from datetime import date, timedelta

# Get news from last 30 days
cutoff = date.today() - timedelta(days=30)
recent = NewsRelease.objects.filter(
    release_date__gte=cutoff
).order_by('-release_date')

for nr in recent:
    print(f"[{nr.release_date}] {nr.company.name}: {nr.title}")
```

## 🎉 Summary

You now have **automated news crawling** that:

✅ Runs on a schedule (daily/weekly)
✅ Crawls all company websites automatically
✅ Discovers and stores new releases
✅ Skips duplicates
✅ Requires zero manual intervention

### Before Automation:
1. Manually visit company website
2. Look for news section
3. Check for new releases
4. Copy URLs
5. Manually add to database
6. Repeat for each company
7. Do this daily/weekly

### After Automation:
1. **Nothing!** It runs automatically
2. Check admin interface to see new releases

**Saves:** 99% of manual effort!

---

## Quick Start (Windows):

1. Test the command:
   ```cmd
   cd c:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend
   python manage.py crawl_news --all --months 1
   ```

2. Test the batch file:
   ```cmd
   crawl_all_companies.bat
   ```

3. Set up Task Scheduler:
   - Open Task Scheduler
   - Create task
   - Set trigger (Daily 2 AM)
   - Set action (run batch file)
   - Save and test

4. Done! Crawler runs automatically every day.

**Questions? Issues?**
- Check Task Scheduler history
- View crawler logs
- Test manually first
