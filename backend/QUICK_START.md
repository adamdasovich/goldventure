# Quick Start - News Scraping

## 🚀 Manual Scraping (Do It Now)

**Just double-click this file:**
```
manual_scrape.bat
```

Or run from command line:
```cmd
cd backend
python manual_scrape.py
```

Then follow the prompts:
1. Choose company number or 'all'
2. Enter months back (default: 6)
3. Enter depth (default: 2)
4. Done! View results in admin

---

## 🤖 Automatic Scraping (Set & Forget)

### Quick Setup (5 minutes):

1. **Test the batch file:**
   ```cmd
   cd backend
   crawl_all_companies.bat
   ```
   (Should see it scrape companies)

2. **Open Task Scheduler:**
   - Press `Win + R`
   - Type: `taskschd.msc`
   - Press Enter

3. **Create Task:**
   - Click "Create Basic Task"
   - Name: `Crawl Company News`
   - Trigger: Daily at 2:00 AM
   - Action: Start program → Browse to `crawl_all_companies.bat`
   - Check "Run whether user is logged on"
   - Done!

4. **Test it:**
   - Right-click task → "Run"
   - Check database for new news releases

---

## 📍 View Results

**Admin Interface:**
- http://localhost:8000/admin/core/newsrelease/

**Current Count:**
```bash
python manage.py shell -c "from core.models import NewsRelease; print(f'{NewsRelease.objects.count()} news releases')"
```

---

## 📚 Full Documentation

- [SCRAPING_GUIDE.md](SCRAPING_GUIDE.md) - Complete manual & auto guide
- [AUTOMATED_NEWS_CRAWLING.md](AUTOMATED_NEWS_CRAWLING.md) - Scheduling details
- [NEWS_RELEASE_CRAWLER.md](NEWS_RELEASE_CRAWLER.md) - Technical documentation

---

## ✅ You're Ready!

**Manual scraping**: Double-click `manual_scrape.bat`

**Automatic scraping**: Already running at 2 AM daily (after setup)

**View news**: Admin interface → News releases
