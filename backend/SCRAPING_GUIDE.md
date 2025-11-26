# News Scraping Guide - Manual & Automatic

Complete guide for scraping company news releases both manually and automatically.

## 🎯 Two Ways to Scrape

### 1. **Manual Scraping** - When You Need It Now
- Scrape specific company immediately
- Try different settings (months, depth)
- Scrape any URL on demand
- Perfect for testing or one-off scrapes

### 2. **Automatic Scraping** - Set It and Forget It
- Runs daily at 2 AM automatically
- Scrapes all companies
- Zero manual work
- Perfect for keeping database up-to-date

---

## 📱 Manual Scraping (Interactive)

### Quick Start:

```cmd
cd c:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend
python manual_scrape.py
```

### What You'll See:

```
================================================================================
MANUAL NEWS SCRAPER
================================================================================

Found 2 companies:

1. 1911 Gold Corporation - https://www.1911gold.com
2. Aston Bay Holdings Ltd. - https://www.astonbayholdings.com

Options:
  Enter number (1-2) to scrape specific company
  Enter 'all' to scrape all companies
  Enter 'url' to scrape any URL manually
  Enter 'q' to quit

Your choice: _
```

### Usage Examples:

#### Example 1: Scrape Specific Company

```
Your choice: 1
How many months back? (default 6): 3
Crawl depth? (default 2): 2

Settings: 3 months back, depth 2

Scraping 1911 Gold Corporation...
Found 5 news releases
✓ Created: 2
⊘ Skipped: 3
```

#### Example 2: Scrape All Companies

```
Your choice: all
How many months back? (default 6): 6
Crawl depth? (default 2): 2

Scraping all 2 companies...
[Scrapes each company]
Total created: 10
```

#### Example 3: Scrape Any URL

```
Your choice: url
Enter website URL: https://newcompany.com
Enter company name (must match database): New Company Inc

Found 8 news releases
✓ Created: 8
```

### Parameters Explained:

- **Months back**: How far to look back for news (1-12 recommended)
  - `1` = Last month only (fast)
  - `6` = Last 6 months (default)
  - `12` = Last year (comprehensive)

- **Crawl depth**: How deep to search the website (1-3 recommended)
  - `1` = Homepage only (fastest)
  - `2` = Homepage + one level deep (default, good balance)
  - `3` = Deeper search (slower but more thorough)

---

## 🤖 Automatic Scraping (Scheduled)

### Setup Windows Task Scheduler:

#### Step 1: Test the Batch File

First make sure it works:

```cmd
cd c:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend
crawl_all_companies.bat
```

You should see the crawler run and scrape all companies.

#### Step 2: Open Task Scheduler

1. Press `Windows Key + R`
2. Type: `taskschd.msc`
3. Press Enter

#### Step 3: Create New Task

1. In the right panel, click **"Create Basic Task..."**

2. **Name and Description**:
   - Name: `Crawl Company News Releases`
   - Description: `Automatically scrapes mining company websites for latest news releases`
   - Click "Next"

3. **Trigger (When)**:
   - Select: **Daily**
   - Click "Next"
   - Start date: Today
   - Start time: `2:00:00 AM` (or your preferred time)
   - Recur every: `1` days
   - Click "Next"

4. **Action (What)**:
   - Select: **Start a program**
   - Click "Next"
   - Program/script: Browse to:
     ```
     c:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend\crawl_all_companies.bat
     ```
   - Start in (optional):
     ```
     c:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend
     ```
   - Click "Next"

5. **Summary**:
   - Review settings
   - ✓ Check "Open the Properties dialog when I click Finish"
   - Click "Finish"

6. **Properties Dialog** (Opens automatically):
   - Go to **"General"** tab:
     - ✓ Check "Run whether user is logged on or not"
     - ✓ Check "Run with highest privileges" (if needed)

   - Go to **"Settings"** tab:
     - ✓ Check "Stop the task if it runs longer than: 1 hour"
     - ✓ Check "If the task fails, restart every: 10 minutes"
     - Set "Attempt to restart up to: 3 times"

   - Click "OK"

7. **Enter Windows Password** when prompted

#### Step 4: Test the Schedule

1. In Task Scheduler, find your task in the list
2. Right-click → **"Run"**
3. Check "Last Run Result" column (should say "Success")
4. Verify news releases were added to database

### What Happens Automatically:

Every day at 2 AM:
1. ✅ Task Scheduler wakes up the script
2. ✅ Crawls all companies with websites
3. ✅ Discovers news releases from last month
4. ✅ Stores new releases in database
5. ✅ Skips duplicates
6. ✅ Goes back to sleep

---

## 🎛️ Advanced Usage

### Change Automatic Scraping Settings:

Edit `crawl_all_companies.bat`:

```batch
REM Default (scrapes last 1 month)
python manage.py crawl_news --all --months 1

REM Scrape last 3 months
python manage.py crawl_news --all --months 3

REM Deeper crawl
python manage.py crawl_news --all --months 1 --depth 3
```

### Manual Django Command (Command Line):

```bash
# Scrape all companies
python manage.py crawl_news --all

# Scrape specific company
python manage.py crawl_news --company "1911 Gold"

# Custom settings
python manage.py crawl_news --company "1911" --months 12 --depth 3
```

---

## 📊 Where to View Results

### Django Admin:

1. Go to: http://localhost:8000/admin/
2. Navigate to: **Core → News releases**
3. See all scraped news releases sorted by date

### Django Shell:

```python
python manage.py shell

from core.models import NewsRelease
from datetime import date, timedelta

# Get recent news
recent = NewsRelease.objects.filter(
    release_date__gte=date.today() - timedelta(days=30)
).order_by('-release_date')

for nr in recent:
    print(f"[{nr.release_date}] {nr.company.name}: {nr.title}")
```

---

## 🔍 Troubleshooting

### Manual Scraping Issues:

**Problem**: "No companies found"
- **Solution**: Make sure companies have `website` field populated in database

**Problem**: "Company not found in database"
- **Solution**: Company name must match exactly. Check spelling in admin.

**Problem**: "No news releases found"
- **Solution**:
  - Try increasing months (e.g., 12)
  - Try increasing depth (e.g., 3)
  - Check if company actually publishes PDF news releases

### Automatic Scraping Issues:

**Problem**: Task doesn't run
- **Solution**:
  - Check Task Scheduler → Task history
  - Verify batch file path is correct
  - Make sure "Run whether user is logged on or not" is checked

**Problem**: Task runs but nothing happens
- **Solution**:
  - Run batch file manually to see errors
  - Check database for new entries
  - View Task Scheduler "Last Run Result"

**Problem**: "Access Denied" errors
- **Solution**:
  - Check "Run with highest privileges" in task properties
  - Verify Windows credentials are correct

---

## 📝 Recommended Schedules

### For Active Companies (Frequent News):
- **Frequency**: Daily at 2:00 AM
- **Settings**: `--months 1 --depth 2`
- **Why**: Catches news within 24 hours

### For Less Active Companies:
- **Frequency**: Weekly on Mondays at 6:00 AM
- **Settings**: `--months 1 --depth 2`
- **Why**: Reduces unnecessary crawling

### For Testing:
- **Frequency**: Manual only
- **Settings**: `--months 1 --depth 2`
- **Why**: Test before automating

---

## 🎯 Quick Reference

### Manual Scraping:
```cmd
python manual_scrape.py
```
- Choose company or URL
- Set months and depth
- View results immediately

### Automatic Scraping:
```cmd
crawl_all_companies.bat
```
- Runs via Task Scheduler
- Daily at 2:00 AM
- All companies automatically

### Django Command:
```cmd
python manage.py crawl_news --all --months 1
```
- More control
- Can filter by company
- Good for scripting

---

## ✅ Summary

| Method | When to Use | Command |
|--------|-------------|---------|
| **Manual Interactive** | Quick scrape, testing | `python manual_scrape.py` |
| **Manual Command** | Scripting, specific needs | `python manage.py crawl_news --company "X"` |
| **Automatic Scheduled** | Daily updates, hands-off | Task Scheduler runs batch file |

**Best Practice**:
- Use **manual** for immediate needs and testing
- Use **automatic** for daily maintenance
- Both can run simultaneously without conflicts

---

## 🎉 You're All Set!

Now you can:
- ✅ Manually scrape any company anytime
- ✅ Automatically scrape all companies daily
- ✅ View all news in admin interface
- ✅ Never manually check company websites again!
