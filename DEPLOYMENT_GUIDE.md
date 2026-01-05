# Deployment Guide for juniorminingintelligence.com

This guide will walk you through deploying the GoldVenture platform to production.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Domain & DNS Configuration](#domain--dns-configuration)
4. [SSL Certificate Setup](#ssl-certificate-setup)
5. [Backend Deployment](#backend-deployment)
6. [Frontend Deployment](#frontend-deployment)
7. [Database Migration](#database-migration)
8. [WebSocket Server Setup](#websocket-server-setup)
9. [Production Checklist](#production-checklist)

---

## Prerequisites

### Required Services
- [ ] VPS/Cloud Server (DigitalOcean, AWS, Linode, etc.)
  - Recommended: 2 CPU cores, 4GB RAM, 50GB SSD
  - Ubuntu 22.04 LTS recommended
- [ ] Domain: juniorminingintelligence.com (purchased ✓)
- [ ] PostgreSQL database (can be on same server or managed service)
- [ ] Redis server (for WebSocket/caching)

### Required Software on Server
- Docker & Docker Compose (recommended)
- OR: Python 3.12+, Node.js 18+, Nginx, PostgreSQL, Redis

---

## Server Setup

### Option 1: Using Docker (Recommended)

1. **Install Docker & Docker Compose**
```bash
# On Ubuntu 22.04
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo apt-get install docker-compose-plugin
```

2. **Clone your repository**
```bash
git clone <your-repo-url> /var/www/goldventure
cd /var/www/goldventure
```

### Option 2: Manual Setup

1. **Install Python & Node.js**
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip nodejs npm nginx postgresql postgresql-contrib redis-server
```

2. **Clone repository**
```bash
git clone <your-repo-url> /var/www/goldventure
cd /var/www/goldventure
```

---

## Domain & DNS Configuration

### Step 1: Point Domain to Server

In your domain registrar (where you bought juniorminingintelligence.com):

**Add these DNS records:**

| Type  | Name | Value                  | TTL  |
|-------|------|------------------------|------|
| A     | @    | YOUR_SERVER_IP         | 3600 |
| A     | www  | YOUR_SERVER_IP         | 3600 |
| CNAME | api  | juniorminingintelligence.com | 3600 |

**Example:**
```
A     @    147.182.123.45
A     www  147.182.123.45
CNAME api  juniorminingintelligence.com
```

### Step 2: Wait for DNS Propagation
- DNS changes can take 1-48 hours
- Check status: `dig juniorminingintelligence.com`

---

## SSL Certificate Setup

### Using Certbot (Let's Encrypt - Free SSL)

1. **Install Certbot**
```bash
sudo apt install certbot python3-certbot-nginx
```

2. **Obtain SSL Certificate**
```bash
sudo certbot --nginx -d juniorminingintelligence.com -d www.juniorminingintelligence.com -d api.juniorminingintelligence.com
```

3. **Auto-renewal** (Certbot sets this up automatically)
```bash
sudo certbot renew --dry-run
```

---

## Backend Deployment

### Step 1: Environment Variables

Create `/var/www/goldventure/backend/.env.production`:

```bash
# Django Settings
SECRET_KEY=your-super-secret-key-here-change-this
DEBUG=False
ALLOWED_HOSTS=juniorminingintelligence.com,www.juniorminingintelligence.com,api.juniorminingintelligence.com

# Database
DATABASE_URL=postgresql://dbuser:dbpassword@localhost:5432/goldventure_prod

# CORS
CORS_ALLOWED_ORIGINS=https://juniorminingintelligence.com,https://www.juniorminingintelligence.com

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (for production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (for media files - optional)
USE_S3=False
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Step 2: Update Django Settings

The `settings.py` will be updated to use environment variables (see below).

### Step 3: Install Dependencies

```bash
cd /var/www/goldventure/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### Step 4: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 5: Run Migrations

```bash
python manage.py migrate
```

### Step 6: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 7: Setup Gunicorn Service

Create `/etc/systemd/system/goldventure-backend.service`:

```ini
[Unit]
Description=GoldVenture Django Backend
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/goldventure/backend
Environment="PATH=/var/www/goldventure/backend/venv/bin"
ExecStart=/var/www/goldventure/backend/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable goldventure-backend
sudo systemctl start goldventure-backend
sudo systemctl status goldventure-backend
```

---

## Frontend Deployment

### Step 1: Environment Variables

Create `/var/www/goldventure/frontend/.env.production`:

```bash
NEXT_PUBLIC_API_URL=https://api.juniorminingintelligence.com
NEXT_PUBLIC_WS_URL=wss://api.juniorminingintelligence.com
```

### Step 2: Update API URLs in Code

The frontend will be updated to use environment variables (see below).

### Step 3: Build Frontend

```bash
cd /var/www/goldventure/frontend
npm install
npm run build
```

### Step 4: Setup PM2 (Process Manager)

```bash
npm install -g pm2
pm2 start npm --name "goldventure-frontend" -- start
pm2 save
pm2 startup
```

---

## WebSocket Server Setup

### Setup Daphne Service

Create `/etc/systemd/system/goldventure-websocket.service`:

```ini
[Unit]
Description=GoldVenture WebSocket Server (Daphne)
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/goldventure/backend
Environment="PATH=/var/www/goldventure/backend/venv/bin"
ExecStart=/var/www/goldventure/backend/venv/bin/daphne \
    -b 127.0.0.1 \
    -p 8002 \
    config.asgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable goldventure-websocket
sudo systemctl start goldventure-websocket
sudo systemctl status goldventure-websocket
```

---

## Nginx Configuration

Create `/etc/nginx/sites-available/goldventure`:

```nginx
# Frontend - Main Site
server {
    listen 80;
    listen [::]:80;
    server_name juniorminingintelligence.com www.juniorminingintelligence.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name juniorminingintelligence.com www.juniorminingintelligence.com;

    # SSL certificates (Certbot will add these)
    ssl_certificate /etc/letsencrypt/live/juniorminingintelligence.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/juniorminingintelligence.com/privkey.pem;

    # Frontend - Next.js
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend API
server {
    listen 80;
    listen [::]:80;
    server_name api.juniorminingintelligence.com;

    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.juniorminingintelligence.com;

    ssl_certificate /etc/letsencrypt/live/juniorminingintelligence.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/juniorminingintelligence.com/privkey.pem;

    # Django Backend
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /var/www/goldventure/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/goldventure/backend/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/goldventure /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Database Migration

### Step 1: Backup Current Database

```bash
# On development machine
pg_dump goldventure > goldventure_backup.sql
```

### Step 2: Transfer to Production

```bash
scp goldventure_backup.sql user@your-server:/tmp/
```

### Step 3: Import to Production

```bash
# On production server
sudo -u postgres psql
CREATE DATABASE goldventure_prod;
CREATE USER dbuser WITH PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE goldventure_prod TO dbuser;
\q

psql -U dbuser goldventure_prod < /tmp/goldventure_backup.sql
```

---

## Production Checklist

### Security
- [ ] Change Django SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable HTTPS (SSL certificate installed)
- [ ] Set secure cookie flags
- [ ] Configure firewall (UFW)
- [ ] Set up fail2ban
- [ ] Regular security updates

### Performance
- [ ] Enable Django caching (Redis)
- [ ] Configure static file caching
- [ ] Set up CDN (optional - Cloudflare)
- [ ] Database indexing optimized
- [ ] Gzip compression enabled

### Monitoring
- [ ] Set up error logging (Sentry)
- [ ] Configure uptime monitoring
- [ ] Set up server monitoring (CPU, memory, disk)
- [ ] Database backups automated

### Functionality
- [ ] Test user registration
- [ ] Test user login
- [ ] Test event creation
- [ ] Test live streaming
- [ ] Test Q&A and reactions
- [ ] Test WebSocket connections
- [ ] Test email sending

---

## Deployment Commands Reference

### Update Backend
```bash
cd /var/www/goldventure/backend
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart goldventure-backend
sudo systemctl restart goldventure-websocket
```

### Update Frontend
```bash
cd /var/www/goldventure/frontend
git pull
npm install
npm run build
pm2 restart goldventure-frontend
```

### View Logs
```bash
# Backend
sudo journalctl -u goldventure-backend -f

# WebSocket
sudo journalctl -u goldventure-websocket -f

# Frontend
pm2 logs goldventure-frontend

# Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

---

## Next Steps After Deployment

1. **Test thoroughly** - Go through all features
2. **Set up monitoring** - Sentry, Uptime Robot, etc.
3. **Configure backups** - Database, media files
4. **Update branding** - Update any "GoldVenture" references to your preferred name
5. **Set up analytics** - Google Analytics, etc.
6. **Create documentation** - User guides, API docs

---

## Support & Troubleshooting

### Common Issues

**500 Error:**
- Check logs: `sudo journalctl -u goldventure-backend -f`
- Verify environment variables
- Check database connection

**WebSocket not connecting:**
- Verify Daphne is running: `sudo systemctl status goldventure-websocket`
- Check nginx WebSocket configuration
- Verify wss:// URL in frontend

**Static files not loading:**
- Run `python manage.py collectstatic`
- Check nginx static file location
- Verify permissions: `sudo chown -R www-data:www-data /var/www/goldventure`

---

## Contact

For deployment support, refer to Django and Next.js documentation:
- Django: https://docs.djangoproject.com/en/5.0/howto/deployment/
- Next.js: https://nextjs.org/docs/deployment
