# Deployment Reference

## Server Information

| Property | Value |
|----------|-------|
| **Provider** | DigitalOcean |
| **IP Address** | 137.184.168.166 |
| **SSH Access** | `ssh root@137.184.168.166` |
| **Project Path** | `/var/www/goldventure` |
| **Virtual Env** | `/var/www/goldventure/backend/venv` |
| **Live URL** | https://juniorminingintelligence.com |

**IMPORTANT:** The server path is `/var/www/goldventure`, NOT `/var/www/goldventure-platform`.

---

## Directory Structure (Server)

```
/var/www/goldventure/
├── backend/
│   ├── venv/                  # Python virtual environment
│   ├── config/                # Django settings
│   ├── core/                  # Main application
│   ├── mcp_servers/           # Scrapers
│   └── manage.py
├── frontend/                  # Next.js app (built)
└── staticfiles/               # Collected static files
```

---

## Services

### Gunicorn (Django)
- **Service:** `systemctl status gunicorn`
- **Config:** `/etc/systemd/system/gunicorn.service`
- **Restart:** `systemctl restart gunicorn`

### Nginx
- **Service:** `systemctl status nginx`
- **Config:** `/etc/nginx/sites-available/goldventure`
- **Restart:** `systemctl restart nginx`

### Celery Worker
- **Log:** `/var/log/celery-worker.log`
- **PID:** `/var/run/celery-worker.pid`
- **Check:** `ps aux | grep 'celery.*worker'`

### Celery Beat (Scheduler)
- **Log:** `/var/log/celery-beat.log`
- **PID:** `/var/run/celery-beat.pid`
- **Check:** `ps aux | grep 'celery.*beat'`

### Redis (Message Broker)
- **Check:** `redis-cli ping`
- **Service:** `systemctl status redis`

### PostgreSQL
- **Database:** `goldventure`
- **User:** `goldventure`
- **Check:** `systemctl status postgresql`

---

## Deployment Steps

### 1. SSH into Server
```bash
ssh root@137.184.168.166
cd /var/www/goldventure/backend
source venv/bin/activate
```

### 2. Pull Latest Code
```bash
git pull origin main
```

### 3. Install Dependencies (if changed)
```bash
pip install -r requirements.txt
```

### 4. Run Migrations (if needed)
```bash
python manage.py migrate
```

### 5. Collect Static Files (if changed)
```bash
python manage.py collectstatic --noinput
```

### 6. Restart Services
```bash
# Restart Django
systemctl restart gunicorn

# Restart Celery (BOTH are required)
pkill -f 'celery -A config'
rm -f /var/run/celery-beat.pid /var/run/celery-worker.pid

celery -A config beat --detach \
  --logfile=/var/log/celery-beat.log \
  --pidfile=/var/run/celery-beat.pid

celery -A config worker --detach --concurrency=2 \
  --logfile=/var/log/celery-worker.log \
  --pidfile=/var/run/celery-worker.pid
```

### 7. Verify Services
```bash
# Check all services are running
ps aux | grep gunicorn | grep -v grep
ps aux | grep celery | grep -v grep
redis-cli ping
```

---

## Celery Management

### Check Status
```bash
# Check if processes are running
ps aux | grep celery | grep -v grep

# Check active tasks
celery -A config inspect active

# Check queued tasks
celery -A config inspect reserved

# View recent logs
tail -50 /var/log/celery-worker.log
tail -50 /var/log/celery-beat.log
```

### Full Restart
```bash
# Kill existing processes
pkill -f 'celery -A config'

# Wait a moment
sleep 2

# Remove stale PID files
rm -f /var/run/celery-beat.pid /var/run/celery-worker.pid

# Start beat (scheduler)
cd /var/www/goldventure/backend && source venv/bin/activate
celery -A config beat --detach \
  --logfile=/var/log/celery-beat.log \
  --pidfile=/var/run/celery-beat.pid

# Start worker
celery -A config worker --detach --concurrency=2 \
  --logfile=/var/log/celery-worker.log \
  --pidfile=/var/run/celery-worker.pid

# Verify
ps aux | grep celery | grep -v grep
```

### Purge Task Queue
```bash
celery -A config purge -f
```

### Trigger Task Manually
```bash
cd /var/www/goldventure/backend && source venv/bin/activate
DJANGO_SETTINGS_MODULE=config.settings python -c "
from core.tasks import scrape_all_companies_news_task
result = scrape_all_companies_news_task.delay()
print(f'Task ID: {result.id}')
"
```

---

## Log Locations

| Log | Path |
|-----|------|
| Celery Worker | `/var/log/celery-worker.log` |
| Celery Beat | `/var/log/celery-beat.log` |
| Gunicorn | `journalctl -u gunicorn` |
| Nginx Access | `/var/log/nginx/access.log` |
| Nginx Error | `/var/log/nginx/error.log` |
| Django | Check gunicorn logs |

---

## Common Issues

### Celery Worker Died
**Symptoms:** Tasks not running, stale data
**Solution:**
```bash
# Check if running
ps aux | grep 'celery.*worker'

# If not, restart both beat and worker
pkill -f 'celery -A config'
# ... (see Full Restart above)
```

### Out of Memory
**Symptoms:** Worker killed, OOM in dmesg
**Check:**
```bash
free -h
dmesg | grep -i kill
```
**Solution:** Reduce concurrency to 1:
```bash
celery -A config worker --detach --concurrency=1 ...
```

### Database Connection Errors
**Check:**
```bash
systemctl status postgresql
sudo -u postgres psql -c "SELECT 1"
```

### Nginx 502 Bad Gateway
**Cause:** Gunicorn not running
**Solution:**
```bash
systemctl restart gunicorn
systemctl status gunicorn
```

---

## Environment Variables

Key environment variables are in `/var/www/goldventure/backend/.env`:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret key |
| `DATABASE_URL` | PostgreSQL connection |
| `REDIS_URL` | Redis connection (Celery broker) |
| `ANTHROPIC_API_KEY` | Claude API access |
| `ALPHA_VANTAGE_API_KEY` | Stock price API |
| `EMAIL_HOST_PASSWORD` | SMTP password |

---

## API Authentication

**Admin Token:** `ADMIN_API_TOKEN_ROTATED`

```bash
curl -H "Authorization: Token ADMIN_API_TOKEN_ROTATED" \
  https://juniorminingintelligence.com/api/companies/
```

---

## Backup

### Database Backup
```bash
sudo -u postgres pg_dump goldventure > /tmp/goldventure_backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
sudo -u postgres psql goldventure < backup_file.sql
```

---

## Frontend Deployment

The Next.js frontend is built and served by Nginx:

```bash
cd /var/www/goldventure/frontend
npm install
npm run build
# Nginx serves from .next/
```
