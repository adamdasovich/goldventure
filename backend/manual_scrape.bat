@echo off
REM Manual News Scraper - Interactive
REM Double-click this file to manually scrape company news

echo ================================================================================
echo MANUAL NEWS SCRAPER
echo ================================================================================
echo.

REM Change to backend directory
cd /d "c:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend"

REM Run the interactive scraper
python manual_scrape.py

echo.
echo Press any key to exit...
pause > nul
