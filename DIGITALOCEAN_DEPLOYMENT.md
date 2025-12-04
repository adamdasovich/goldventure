# DigitalOcean Deployment Guide
## juniorgoldminingintelligence.com

This guide will walk you through deploying your GoldVenture platform on DigitalOcean.

---

## Part 1: Create DigitalOcean Droplet (10 minutes)

### Step 1: Sign Up / Log In
1. Go to https://www.digitalocean.com
2. Sign up or log in
3. **New user?** You'll get $200 free credit for 60 days

### Step 2: Create Droplet
1. Click **"Create"** → **"Droplets"**
2. Choose configuration:

**Choose an image:**
- Select **Ubuntu 22.04 (LTS) x64**

**Choose Size:**
- **Recommended**: Basic Plan
- **CPU options**: Regular
- **Droplet Size**: $12/month (2 GB RAM / 1 CPU / 50 GB SSD / 2 TB transfer)
- Or **$18/month** (2 GB RAM / 2 CPUs) for better performance

**Choose a datacenter region:**
- Select closest to your target audience (e.g., New York, San Francisco, Toronto)

**Authentication:**
- Choose **SSH keys** (more secure) OR **Password**
- If SSH: Click "New SSH Key" and follow instructions
- If Password: You'll receive it via email

**Finalize Details:**
- Hostname: `goldventure-prod` or `juniorgoldmining`
- Tags: `production`, `web`
- Click **"Create Droplet"**

### Step 3: Note Your Server IP
- Wait 1-2 minutes for droplet to be created
- Copy the **IP Address** (e.g., 147.182.123.45)
- You'll need this for DNS and SSH

---

## Part 2: Configure DNS (5 minutes)

### Step 1: Add Domain to DigitalOcean (Optional but Recommended)
1. In DigitalOcean dashboard, go to **Networking** → **Domains**
2. Click **"Add Domain"**
3. Enter: `juniorgoldminingintelligence.com`
4. Select your droplet
5. Click **"Add Domain"**

### Step 2: Update Nameservers at Your Registrar
Go to where you purchased juniorgoldminingintelligence.com and update nameservers to:
```
ns1.digitalocean.com
ns2.digitalocean.com
ns3.digitalocean.com
```

**OR use A records** (if you want to keep current nameservers):

| Type  | Hostname | Value (Your Droplet IP) | TTL  |
|-------|----------|-------------------------|------|
| A     | @        | 147.182.123.45         | 3600 |
| A     | www      | 147.182.123.45         | 3600 |
| A     | api      | 147.182.123.45         | 3600 |

### Step 3: Create DNS Records in DigitalOcean
If using DigitalOcean DNS:
1. Go to **Networking** → **Domains** → **juniorgoldminingintelligence.com**
2. Add these records:

```
A     @    YOUR_DROPLET_IP   3600
A     www  YOUR_DROPLET_IP   3600
A     api  YOUR_DROPLET_IP   3600
```

**DNS Propagation:** Wait 1-48 hours (usually 1-2 hours)

---

## Part 3: Initial Server Setup (15 minutes)

### Step 1: Connect to Your Droplet
```bash
ssh root@YOUR_DROPLET_IP
# Enter password if you didn't use SSH keys
```

### Step 2: Update System
```bash
apt update && apt upgrade -y
```

### Step 3: Create Non-Root User (Security Best Practice)
```bash
adduser goldventure
# Follow prompts to set password

# Add to sudo group
usermod -aG sudo goldventure

# Switch to new user
su - goldventure
```

### Step 4: Setup Firewall
```bash
# Allow SSH
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'

# Enable firewall
sudo ufw enable
sudo ufw status
```

### Step 5: Install Required Software
```bash
# Install all dependencies at once
sudo apt install -y python3.12 python3.12-venv python3-pip \
    nodejs npm \
    nginx \
    postgresql postgresql-contrib \
    redis-server \
    git \
    certbot python3-certbot-nginx
```

### Step 6: Verify Installations
```bash
python3 --version   # Should show 3.12.x
node --version      # Should show v18.x or higher
nginx -v            # Should show nginx version
psql --version      # Should show PostgreSQL
redis-cli --version # Should show Redis version
```

---

## Part 4: Setup PostgreSQL Database (10 minutes)

### Step 1: Create Database and User
```bash
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE goldventure_prod;
CREATE USER dbuser WITH PASSWORD 'your-super-secure-password-here';
GRANT ALL PRIVILEGES ON DATABASE goldventure_prod TO dbuser;
ALTER USER dbuser CREATEDB;
\q
```

### Step 2: Test Connection
```bash
psql -U dbuser -d goldventure_prod -h localhost
# Enter password when prompted
# If successful, you'll see goldventure_prod=# prompt
\q
```

---

## Part 5: Deploy Backend (20 minutes)

### Step 1: Clone Repository
```bash
cd ~
git clone <your-github-repo-url> goldventure
cd goldventure
```

**Don't have a git repo yet?** Upload files with scp:
```bash
# On your local machine:
scp -r c:\Users\adamd\Desktop\Nvidia\goldventure-platform goldventure@YOUR_DROPLET_IP:~/goldventure
```

### Step 2: Setup Backend Environment
```bash
cd ~/goldventure/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary django-redis channels-redis
```

### Step 3: Create Production Environment File
```bash
cd ~/goldventure/backend
nano .env.production
```

Paste this and **replace the values**:
```bash
# Django Core
SECRET_KEY=PASTE-NEW-SECRET-KEY-HERE
DEBUG=False
ALLOWED_HOSTS=juniorgoldminingintelligence.com,www.juniorgoldminingintelligence.com,api.juniorgoldminingintelligence.com,YOUR_DROPLET_IP

# Database
DATABASE_URL=postgresql://dbuser:your-super-secure-password-here@localhost:5432/goldventure_prod

# CORS
CORS_ALLOWED_ORIGINS=https://juniorgoldminingintelligence.com,https://www.juniorgoldminingintelligence.com

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECURE_SSL_REDIRECT=True

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@juniorgoldminingintelligence.com

# API Keys (add your keys)
ANTHROPIC_API_KEY=
ALPHA_VANTAGE_API_KEY=
TWELVE_DATA_API_KEY=

# AWS S3
USE_S3=False
```

**Generate SECRET_KEY:**
```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
# Copy output and paste in .env.production
```

Save file: `Ctrl+X`, then `Y`, then `Enter`

### Step 4: Run Migrations and Collect Static
```bash
cd ~/goldventure/backend
source venv/bin/activate

# Export environment variables
export $(cat .env.production | xargs)

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Follow prompts

# Collect static files
python manage.py collectstatic --noinput
```

### Step 5: Test Backend Locally
```bash
python manage.py runserver 0.0.0.0:8000
# Open another terminal and test:
curl http://YOUR_DROPLET_IP:8000/api/companies/
# Should return JSON response
# Press Ctrl+C to stop
```

### Step 6: Setup Gunicorn Service
```bash
sudo nano /etc/systemd/system/goldventure-backend.service
```

Paste this (replace `goldventure` with your username if different):
```ini
[Unit]
Description=GoldVenture Django Backend
After=network.target

[Service]
Type=notify
User=goldventure
Group=goldventure
WorkingDirectory=/home/goldventure/goldventure/backend
Environment="PATH=/home/goldventure/goldventure/backend/venv/bin"
EnvironmentFile=/home/goldventure/goldventure/backend/.env.production
ExecStart=/home/goldventure/goldventure/backend/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    config.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable goldventure-backend
sudo systemctl start goldventure-backend
sudo systemctl status goldventure-backend
# Should show "active (running)"
```

### Step 7: Setup WebSocket Service (Daphne)
```bash
sudo nano /etc/systemd/system/goldventure-websocket.service
```

Paste:
```ini
[Unit]
Description=GoldVenture WebSocket Server
After=network.target

[Service]
Type=simple
User=goldventure
Group=goldventure
WorkingDirectory=/home/goldventure/goldventure/backend
Environment="PATH=/home/goldventure/goldventure/backend/venv/bin"
EnvironmentFile=/home/goldventure/goldventure/backend/.env.production
ExecStart=/home/goldventure/goldventure/backend/venv/bin/daphne \
    -b 127.0.0.1 \
    -p 8002 \
    config.asgi:application

Restart=always

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

## Part 6: Deploy Frontend (15 minutes)

### Step 1: Setup Frontend Environment
```bash
cd ~/goldventure/frontend

# Create production environment file
nano .env.production
```

Paste:
```bash
NEXT_PUBLIC_API_URL=https://api.juniorgoldminingintelligence.com
NEXT_PUBLIC_WS_URL=wss://api.juniorgoldminingintelligence.com
```

Save: `Ctrl+X`, `Y`, `Enter`

### Step 2: Install Dependencies and Build
```bash
cd ~/goldventure/frontend
npm install
npm run build
```

### Step 3: Setup PM2 (Process Manager)
```bash
sudo npm install -g pm2

# Start frontend
cd ~/goldventure/frontend
pm2 start npm --name "goldventure-frontend" -- start

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Copy and run the command it outputs (starts with sudo)
```

### Step 4: Verify Frontend
```bash
pm2 status
pm2 logs goldventure-frontend
```

---

## Part 7: Setup Nginx (15 minutes)

### Step 1: Create Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/goldventure
```

Paste this configuration:
```nginx
# Frontend - Main Site
server {
    listen 80;
    listen [::]:80;
    server_name juniorgoldminingintelligence.com www.juniorgoldminingintelligence.com;

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
    server_name api.juniorgoldminingintelligence.com;

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
        alias /home/goldventure/goldventure/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/goldventure/goldventure/backend/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

Save: `Ctrl+X`, `Y`, `Enter`

### Step 2: Enable Site
```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/goldventure /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t
# Should say "syntax is ok" and "test is successful"

# Restart Nginx
sudo systemctl restart nginx
```

---

## Part 8: Setup SSL Certificate (10 minutes)

**Wait for DNS to propagate first!** Check with:
```bash
dig juniorgoldminingintelligence.com
# Should show your droplet IP
```

### Step 1: Obtain SSL Certificate
```bash
sudo certbot --nginx -d juniorgoldminingintelligence.com -d www.juniorgoldminingintelligence.com -d api.juniorgoldminingintelligence.com
```

Follow prompts:
1. Enter email address
2. Agree to terms
3. Choose whether to share email (optional)
4. Choose: **2** (Redirect HTTP to HTTPS)

### Step 2: Test Auto-Renewal
```bash
sudo certbot renew --dry-run
# Should complete successfully
```

### Step 3: Verify HTTPS
```bash
# Test main site
curl -I https://juniorgoldminingintelligence.com
# Should return 200 OK

# Test API
curl -I https://api.juniorgoldminingintelligence.com
# Should return 200 OK
```

---

## Part 9: Final Verification (10 minutes)

### Step 1: Check All Services
```bash
# Backend
sudo systemctl status goldventure-backend

# WebSocket
sudo systemctl status goldventure-websocket

# Frontend
pm2 status

# Nginx
sudo systemctl status nginx

# Redis
sudo systemctl status redis-server

# PostgreSQL
sudo systemctl status postgresql
```

All should show "active (running)"

### Step 2: Test Website
Open in browser:
- https://juniorgoldminingintelligence.com (should load frontend)
- https://api.juniorgoldminingintelligence.com/admin/ (should load Django admin)
- https://api.juniorgoldminingintelligence.com/api/companies/ (should return JSON)

### Step 3: Test Live Streaming
1. Log in as superuser
2. Create a test event
3. Click "Go Live"
4. Paste YouTube URL
5. Verify video plays

---

## Part 10: Backup & Monitoring Setup

### Daily Database Backup Script
```bash
nano ~/backup-db.sh
```

Paste:
```bash
#!/bin/bash
BACKUP_DIR="/home/goldventure/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U dbuser goldventure_prod > $BACKUP_DIR/goldventure_$DATE.sql
# Keep only last 7 days
find $BACKUP_DIR -name "goldventure_*.sql" -mtime +7 -delete
```

Make executable:
```bash
chmod +x ~/backup-db.sh
```

Add to crontab:
```bash
crontab -e
# Add this line (runs daily at 2 AM):
0 2 * * * /home/goldventure/backup-db.sh
```

---

## Maintenance Commands

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
```

### Update Application
```bash
cd ~/goldventure
git pull

# Backend
cd ~/goldventure/backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart goldventure-backend
sudo systemctl restart goldventure-websocket

# Frontend
cd ~/goldventure/frontend
npm install
npm run build
pm2 restart goldventure-frontend
```

### Restart Services
```bash
sudo systemctl restart goldventure-backend
sudo systemctl restart goldventure-websocket
pm2 restart goldventure-frontend
sudo systemctl restart nginx
```

---

## Troubleshooting

### 502 Bad Gateway
```bash
# Check backend is running
sudo systemctl status goldventure-backend
# Check logs
sudo journalctl -u goldventure-backend -n 50
```

### Can't connect to database
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql
# Check connection
psql -U dbuser -d goldventure_prod -h localhost
```

### Frontend not loading
```bash
# Check PM2
pm2 status
pm2 logs goldventure-frontend
# Restart if needed
pm2 restart goldventure-frontend
```

### SSL certificate issues
```bash
sudo certbot renew
sudo systemctl restart nginx
```

---

## ✅ Deployment Complete!

Your platform should now be live at:
- **https://juniorgoldminingintelligence.com**
- **https://api.juniorgoldminingintelligence.com/admin/**

**Total Cost:** ~$12-18/month for DigitalOcean Droplet

**Next Steps:**
1. Test all features thoroughly
2. Set up monitoring (DigitalOcean Monitoring is free)
3. Configure email sending
4. Add your API keys to .env.production
5. Create user documentation

**Need help?** Check server logs or DigitalOcean's excellent documentation at https://docs.digitalocean.com
