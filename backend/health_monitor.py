#!/usr/bin/env python3
"""
Health Monitor for GoldVenture Services
Checks critical services and sends email alerts when they fail.
Run via cron every 5 minutes.
"""

import subprocess
import json
import urllib.request
import urllib.error
import os
import sys
from datetime import datetime
from pathlib import Path

# Load environment from .env file
env_file = Path('/var/www/goldventure/backend/.env')
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            key, _, value = line.partition('=')
            os.environ.setdefault(key.strip(), value.strip())

# Configuration
ALERT_EMAIL = 'adamdasovich@gmail.com'
SENDGRID_API_KEY = os.environ.get('EMAIL_HOST_PASSWORD', '')
FROM_EMAIL = 'info@juniorminingintelligence.com'

# Services to monitor
CRITICAL_SERVICES = [
    'celery-worker',
    'celery-beat', 
    'chromadb',
    'gpu-orchestrator',
    'nginx',
    'postgresql',
]

STATE_FILE = Path('/var/run/health_monitor_state')
LOG_FILE = Path('/var/log/health_monitor.log')

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + '\n')

def get_service_status(service_name):
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() == 'active'
    except Exception:
        return False

def get_failed_services():
    return [s for s in CRITICAL_SERVICES if not get_service_status(s)]

def load_previous_state():
    try:
        if STATE_FILE.exists():
            content = STATE_FILE.read_text().strip()
            return set(content.split('\n')) if content else set()
    except Exception:
        pass
    return set()

def save_state(failed_services):
    STATE_FILE.write_text('\n'.join(failed_services) if failed_services else '')

def send_email(subject, body):
    if not SENDGRID_API_KEY:
        log("No SendGrid API key configured")
        return False

    data = {
        "personalizations": [{"to": [{"email": ALERT_EMAIL}]}],
        "from": {"email": FROM_EMAIL},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}]
    }
    
    req = urllib.request.Request(
        'https://api.sendgrid.com/v3/mail/send',
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {SENDGRID_API_KEY}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            log(f"Email sent: {subject}")
            return True
    except urllib.error.HTTPError as e:
        log(f"SendGrid error {e.code}: {e.read().decode()}")
        return False
    except Exception as e:
        log(f"Email failed: {e}")
        return False

def attempt_restart(service_name):
    try:
        log(f"Auto-restarting {service_name}...")
        subprocess.run(['systemctl', 'restart', service_name], timeout=60)
        return True
    except Exception as e:
        log(f"Restart failed: {e}")
        return False

def main():
    current_failed = set(get_failed_services())
    previous_failed = load_previous_state()
    
    newly_failed = current_failed - previous_failed
    recovered = previous_failed - current_failed
    
    # Auto-restart newly failed services
    restart_results = {}
    for service in newly_failed:
        restart_results[service] = attempt_restart(service)
    
    # Re-check after restarts
    if newly_failed:
        import time
        time.sleep(5)
        current_failed = set(get_failed_services())
        newly_failed = current_failed - previous_failed
        recovered = previous_failed - current_failed
    
    # Send alerts
    if newly_failed:
        subject = f"🔴 ALERT: {len(newly_failed)} GoldVenture service(s) DOWN"
        body = f"""GoldVenture Health Monitor Alert
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Server: 137.184.168.166

FAILED SERVICES:
""" + '\n'.join(f"  - {s}" for s in newly_failed) + """

SSH to investigate: ssh root@137.184.168.166
"""
        send_email(subject, body)
    
    if recovered:
        subject = f"🟢 RECOVERED: {len(recovered)} GoldVenture service(s) back online"
        body = f"""Services recovered:
""" + '\n'.join(f"  - {s}" for s in recovered)
        send_email(subject, body)
    
    save_state(current_failed)
    
    if current_failed:
        log(f"DOWN: {', '.join(current_failed)}")
        sys.exit(1)
    else:
        log("All healthy")
        sys.exit(0)

if __name__ == '__main__':
    main()
