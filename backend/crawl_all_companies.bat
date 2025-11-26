@echo off
REM Automated News Crawler - Runs daily to fetch latest news releases
REM This batch file is designed to be run by Windows Task Scheduler

echo ================================================================================
echo AUTOMATED NEWS CRAWLER
echo ================================================================================
echo Started at: %DATE% %TIME%
echo.

REM Change to backend directory
cd /d "c:\Users\adamd\Desktop\Nvidia\goldventure-platform\backend"

REM Activate virtual environment (if you have one)
REM call venv\Scripts\activate.bat

REM Run the crawler for all companies
python manage.py crawl_news --all --months 1

echo.
echo ================================================================================
echo CRAWLER FINISHED
echo ================================================================================
echo Completed at: %DATE% %TIME%
echo.

REM Optional: Log output to file
REM Add >> crawler_log.txt to the python command above to append to log file
