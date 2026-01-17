#!/usr/bin/env python3
"""
GPU Orchestrator Service

Manages on-demand GPU droplets for document processing.
Runs on the main CPU droplet and:
1. Monitors DocumentProcessingJob queue for pending heavy jobs
2. Spins up GPU droplet when work is available
3. Monitors GPU droplet health and job progress
4. Destroys GPU droplet when queue is empty

Security Features:
- File-based locking prevents multiple orchestrator instances
- Credentials passed via SCP after droplet boot (not in cloud-init)
- SSH host key verification after first connection
"""

import os
import sys
import time
import json
import logging
import requests
import subprocess
import fcntl
import atexit
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

# Django setup (must be before Django imports)
sys.path.insert(0, '/var/www/goldventure/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from django.db import connection
from core.models import DocumentProcessingJob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/gpu_orchestrator.log')
    ]
)
logger = logging.getLogger(__name__)

# Lock file for single instance enforcement (use /tmp for www-data access)
LOCK_FILE = '/tmp/gpu_orchestrator.lock'
_lock_fd = None


def acquire_lock():
    """Acquire exclusive lock to prevent multiple orchestrator instances"""
    global _lock_fd
    try:
        _lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(_lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_fd.write(str(os.getpid()))
        _lock_fd.flush()
        logger.info(f"Acquired lock (PID: {os.getpid()})")
        return True
    except (IOError, OSError) as e:
        logger.error(f"Could not acquire lock - another orchestrator may be running: {e}")
        return False


def release_lock():
    """Release the exclusive lock"""
    global _lock_fd
    if _lock_fd:
        try:
            fcntl.flock(_lock_fd.fileno(), fcntl.LOCK_UN)
            _lock_fd.close()
            os.unlink(LOCK_FILE)
            logger.info("Released lock")
        except Exception as e:
            logger.warning(f"Error releasing lock: {e}")


class GPUOrchestrator:
    """Manages GPU droplet lifecycle for document processing"""

    # Configuration
    DO_API_URL = "https://api.digitalocean.com/v2"
    GPU_REGION = "tor1"  # TOR1 has L40S and RTX 6000 Ada
    GPU_SIZE = "gpu-6000adax1-48gb"  # RTX 6000 Ada at $1.57/hr (available in TOR1)
    GPU_IMAGE = "gpu-h100x1-base"  # GPU-optimized base image with CUDA drivers

    # Timing
    POLL_INTERVAL = 60  # Check queue every 60 seconds
    GPU_STARTUP_TIMEOUT = 300  # 5 minutes to boot
    GPU_IDLE_TIMEOUT = 300  # Destroy after 5 minutes idle
    MAX_GPU_RUNTIME = 7200  # Force destroy after 2 hours (safety)
    JOB_STUCK_TIMEOUT = 900  # Mark job as failed after 15 minutes processing

    # Job types that require GPU processing
    # NOTE: company_scrape removed - it's just HTTP/BeautifulSoup, no GPU needed
    HEAVY_JOB_TYPES = ['ni43101', 'pea', 'presentation', 'fact_sheet', 'news_release']

    def __init__(self):
        self.api_token = os.environ.get('DO_API_TOKEN')
        if not self.api_token:
            raise ValueError("DO_API_TOKEN environment variable not set")

        self.ssh_key_id = os.environ.get('DO_SSH_KEY_ID')
        self.worker_start_failures = 0  # Track consecutive worker start failures
        self.MAX_WORKER_FAILURES = 3  # Destroy droplet after this many failures
        self.gpu_droplet_id: Optional[str] = None
        self.gpu_droplet_ip: Optional[str] = None
        self.gpu_created_at: Optional[datetime] = None
        self.last_job_completed_at: Optional[datetime] = None

        # Load state from file if exists
        self._load_state()

        # Check for orphaned GPU droplets on startup (uses the hard timeout version)
        self.cleanup_orphaned_droplets()

    def _load_state(self):
        """Load orchestrator state from file"""
        state_file = Path('/var/run/gpu_orchestrator_state.json')
        if state_file.exists():
            try:
                with open(state_file) as f:
                    state = json.load(f)
                self.gpu_droplet_id = state.get('droplet_id')
                self.gpu_droplet_ip = state.get('droplet_ip')
                if state.get('created_at'):
                    self.gpu_created_at = datetime.fromisoformat(state['created_at'])
                logger.info(f"Loaded state: droplet_id={self.gpu_droplet_id}")
            except Exception as e:
                logger.warning(f"Could not load state: {e}")

    def _save_state(self):
        """Save orchestrator state to file"""
        state_file = Path('/var/run/gpu_orchestrator_state.json')
        state = {
            'droplet_id': self.gpu_droplet_id,
            'droplet_ip': self.gpu_droplet_ip,
            'created_at': self.gpu_created_at.isoformat() if self.gpu_created_at else None
        }
        with open(state_file, 'w') as f:
            json.dump(state, f)

    def _api_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to DigitalOcean API"""
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        url = f"{self.DO_API_URL}/{endpoint}"

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code >= 400:
            logger.error(f"API error: {response.status_code} - {response.text}")
            response.raise_for_status()

        return response.json() if response.text else {}

    def get_pending_heavy_jobs(self) -> int:
        """Count pending jobs that require GPU processing"""
        count = DocumentProcessingJob.objects.filter(
            status='pending',
            document_type__in=self.HEAVY_JOB_TYPES
        ).count()
        return count

    def get_processing_jobs(self) -> int:
        """Count jobs currently being processed"""
        count = DocumentProcessingJob.objects.filter(
            status='processing',
            document_type__in=self.HEAVY_JOB_TYPES
        ).count()
        return count

    def check_and_handle_stuck_jobs(self) -> int:
        """Check for jobs stuck in 'processing' state and mark them as failed.

        Returns the number of stuck jobs that were marked as failed.
        """
        from django.utils import timezone
        stuck_threshold = timezone.now() - timedelta(seconds=self.JOB_STUCK_TIMEOUT)

        # Find jobs that started processing more than JOB_STUCK_TIMEOUT ago
        stuck_jobs = DocumentProcessingJob.objects.filter(
            status='processing',
            document_type__in=self.HEAVY_JOB_TYPES,
            started_at__lt=stuck_threshold
        )

        stuck_count = 0
        for job in stuck_jobs:
            job_runtime = (timezone.now() - job.started_at).total_seconds() / 60
            logger.warning(
                f"Job {job.id} ({job.document_type}) stuck for {job_runtime:.1f} minutes, marking as failed"
            )
            job.status = 'failed'
            job.error_message = f"Job timed out after {job_runtime:.1f} minutes (stuck job detection)"
            job.completed_at = timezone.now()
            job.save()
            stuck_count += 1

        if stuck_count > 0:
            logger.info(f"Marked {stuck_count} stuck job(s) as failed")

        return stuck_count

    def create_gpu_droplet(self) -> bool:
        """Create a new GPU droplet"""
        logger.info("Creating GPU droplet...")

        # User data script to set up the GPU worker
        user_data = self._get_cloud_init_script()

        droplet_config = {
            "name": f"goldventure-gpu-worker-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "region": self.GPU_REGION,
            "size": self.GPU_SIZE,
            "image": self.GPU_IMAGE,
            "ssh_keys": [self.ssh_key_id] if self.ssh_key_id else [],
            "user_data": user_data,
            "tags": ["goldventure", "gpu-worker", "auto-created"],
            "monitoring": True
        }

        try:
            response = self._api_request('POST', 'droplets', droplet_config)
            droplet = response.get('droplet', {})
            self.gpu_droplet_id = str(droplet.get('id'))
            self.gpu_created_at = datetime.now()
            self._save_state()

            logger.info(f"GPU droplet created: ID={self.gpu_droplet_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create GPU droplet: {e}")
            return False

    def wait_for_droplet_ready(self) -> bool:
        """Wait for GPU droplet to be active and get its IP"""
        logger.info(f"Waiting for droplet {self.gpu_droplet_id} to be ready...")

        start_time = time.time()
        while time.time() - start_time < self.GPU_STARTUP_TIMEOUT:
            try:
                response = self._api_request('GET', f'droplets/{self.gpu_droplet_id}')
                droplet = response.get('droplet', {})
                status = droplet.get('status')

                if status == 'active':
                    # Get public IP
                    networks = droplet.get('networks', {})
                    for network in networks.get('v4', []):
                        if network.get('type') == 'public':
                            self.gpu_droplet_ip = network.get('ip_address')
                            self._save_state()
                            logger.info(f"Droplet ready: IP={self.gpu_droplet_ip}")

                            # Add GPU droplet IP to pg_hba.conf for database access
                            self._add_ip_to_pg_hba(self.gpu_droplet_ip)
                            return True

                logger.info(f"Droplet status: {status}, waiting...")
                time.sleep(10)

            except Exception as e:
                logger.error(f"Error checking droplet status: {e}")
                time.sleep(10)

        logger.error("Timeout waiting for droplet to be ready")
        return False

    def _add_ip_to_pg_hba(self, ip: str) -> None:
        """Add GPU droplet IP to pg_hba.conf for database access"""
        try:
            pg_hba_entry = f"host goldventure goldventure {ip}/32 md5"

            # Check if IP already in pg_hba.conf
            with open('/etc/postgresql/16/main/pg_hba.conf', 'r') as f:
                if ip in f.read():
                    logger.info(f"IP {ip} already in pg_hba.conf")
                    return

            # Add the entry
            with open('/etc/postgresql/16/main/pg_hba.conf', 'a') as f:
                f.write(f"\n{pg_hba_entry}\n")

            # Reload PostgreSQL
            subprocess.run(['systemctl', 'reload', 'postgresql'], timeout=10)
            logger.info(f"Added {ip} to pg_hba.conf and reloaded PostgreSQL")

        except Exception as e:
            logger.error(f"Failed to add IP to pg_hba.conf: {e}")

    def check_gpu_worker_health(self) -> bool:
        """Check if GPU worker is running and healthy"""
        if not self.gpu_droplet_ip:
            return False

        try:
            # SSH to check worker status - use longer timeout and be more lenient
            result = subprocess.run(
                ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=15',
                 '-o', 'ServerAliveInterval=5',
                 f'root@{self.gpu_droplet_ip}', 'pgrep -f gpu_worker.py'],
                capture_output=True,
                timeout=30
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            # If SSH times out, assume worker might still be running
            # Don't restart unnecessarily - just log and return True to avoid restart loops
            logger.warning("Health check SSH timeout - assuming worker is running")
            return True
        except Exception as e:
            logger.warning(f"Could not check GPU worker health: {e}")
            return False

    def start_gpu_worker(self) -> bool:
        """Start the GPU worker process on the droplet"""
        if not self.gpu_droplet_ip:
            return False

        logger.info("Starting GPU worker...")

        try:
            # First check if worker is already running - don't restart if it is
            check_result = subprocess.run(
                ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
                 f'root@{self.gpu_droplet_ip}', 'pgrep -f "python gpu_worker.py"'],
                capture_output=True,
                timeout=20
            )
            if check_result.returncode == 0:
                logger.info("GPU worker already running, skipping start")
                return True

            # Copy worker script
            subprocess.run(
                ['scp', '-o', 'StrictHostKeyChecking=no',
                 '/var/www/goldventure/backend/gpu_worker.py',
                 f'root@{self.gpu_droplet_ip}:/opt/goldventure/'],
                timeout=60
            )

            # Copy website crawler for scraping jobs
            subprocess.run(
                ['scp', '-o', 'StrictHostKeyChecking=no',
                 '/var/www/goldventure/backend/mcp_servers/website_crawler.py',
                 f'root@{self.gpu_droplet_ip}:/opt/goldventure/'],
                timeout=60
            )

            # Start worker in background - use 'sh -c' with exit to ensure SSH returns
            subprocess.run(
                ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
                 f'root@{self.gpu_droplet_ip}',
                 'sh -c "cd /opt/goldventure && source venv/bin/activate && nohup python gpu_worker.py > /var/log/gpu_worker.log 2>&1 &" && exit 0'],
                timeout=60
            )

            logger.info("GPU worker started")
            return True

        except subprocess.TimeoutExpired:
            # SSH timeout during start - worker may still have started
            logger.warning("SSH timeout during worker start - checking if worker is running")
            try:
                check = subprocess.run(
                    ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
                     f'root@{self.gpu_droplet_ip}', 'pgrep -f "python gpu_worker.py"'],
                    capture_output=True,
                    timeout=20
                )
                if check.returncode == 0:
                    logger.info("Worker is running despite SSH timeout")
                    return True
            except:
                pass
            logger.error("Worker start failed with timeout")
            return False

        except Exception as e:
            logger.error(f"Failed to start GPU worker: {e}")
            return False

    def destroy_gpu_droplet(self) -> bool:
        """Destroy the GPU droplet"""
        if not self.gpu_droplet_id:
            return True

        logger.info(f"Destroying GPU droplet {self.gpu_droplet_id}...")

        try:
            self._api_request('DELETE', f'droplets/{self.gpu_droplet_id}')

            # Calculate cost
            if self.gpu_created_at:
                runtime_hours = (datetime.now() - self.gpu_created_at).total_seconds() / 3600
                estimated_cost = runtime_hours * 1.57  # RTX 6000 Ada rate
                logger.info(f"GPU droplet destroyed. Runtime: {runtime_hours:.2f}h, Est. cost: ${estimated_cost:.2f}")

            self.gpu_droplet_id = None
            self.gpu_droplet_ip = None
            self.gpu_created_at = None
            self._save_state()

            return True

        except Exception as e:
            logger.error(f"Failed to destroy GPU droplet: {e}")
            return False

    def should_create_gpu(self) -> bool:
        """Determine if we should spin up a GPU droplet"""
        if self.gpu_droplet_id:
            return False  # Already have one

        pending = self.get_pending_heavy_jobs()
        return pending > 0

    def should_destroy_gpu(self) -> bool:
        """Determine if we should destroy the GPU droplet"""
        if not self.gpu_droplet_id:
            return False  # Nothing to destroy

        # Check if max runtime exceeded
        if self.gpu_created_at:
            runtime = (datetime.now() - self.gpu_created_at).total_seconds()
            if runtime > self.MAX_GPU_RUNTIME:
                logger.warning("Max GPU runtime exceeded, forcing destroy")
                return True

        # Check if queue is empty and idle timeout reached
        pending = self.get_pending_heavy_jobs()
        processing = self.get_processing_jobs()

        if pending == 0 and processing == 0:
            if self.last_job_completed_at:
                idle_time = (datetime.now() - self.last_job_completed_at).total_seconds()
                if idle_time > self.GPU_IDLE_TIMEOUT:
                    logger.info("GPU idle timeout reached, destroying")
                    return True
            else:
                # First time seeing empty queue
                self.last_job_completed_at = datetime.now()
        else:
            # Queue not empty, reset idle timer
            self.last_job_completed_at = None

        return False

    def _get_cloud_init_script(self) -> str:
        """Generate cloud-init script for GPU droplet setup.

        SECURITY: Credentials are NOT included here - they are transferred
        securely via SCP after the droplet boots (see _transfer_credentials).
        """
        return '''#!/bin/bash
set -e

# Update system
apt-get update
apt-get install -y python3-pip python3-venv postgresql-client

# Create working directory with secure permissions
mkdir -p /opt/goldventure
chmod 700 /opt/goldventure
cd /opt/goldventure

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install psycopg2-binary requests tiktoken sentence-transformers pypdfium2

# Install scraping dependencies
pip install crawl4ai beautifulsoup4 playwright
playwright install chromium

# Install PyTorch with CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Create placeholder for credentials (will be transferred via SCP)
touch /opt/goldventure/.env
chmod 600 /opt/goldventure/.env

# Signal ready for credential transfer
touch /opt/goldventure/.ready
'''

    # Main server's external IP for GPU workers to connect back
    MAIN_SERVER_IP = "137.184.168.166"

    def _transfer_credentials(self) -> bool:
        """Securely transfer credentials to GPU droplet via SCP.

        This is called after the droplet boots, avoiding credential
        exposure in cloud-init logs.
        """
        if not self.gpu_droplet_ip:
            return False

        logger.info("Transferring credentials securely via SCP...")

        # Get password from environment, but use external IP for remote connection
        db_password = os.environ.get('DB_PASSWORD')

        if not db_password:
            logger.error("DB_PASSWORD must be set in environment")
            return False

        # Use the main server's external IP for GPU worker to connect back
        db_host = self.MAIN_SERVER_IP

        # Create temporary env file locally
        env_content = f"""# GPU Worker Environment - Securely Transferred
DB_HOST={db_host}
DB_PORT=5432
DB_NAME=goldventure
DB_USER=goldventure
DB_PASSWORD={db_password}
CHROMA_HOST={db_host}
CHROMA_PORT=8002
"""

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write(env_content)
            temp_env_path = f.name

        try:
            # Transfer credentials via SCP
            result = subprocess.run(
                ['scp', '-o', 'StrictHostKeyChecking=accept-new',
                 '-o', 'ConnectTimeout=30',
                 temp_env_path,
                 f'root@{self.gpu_droplet_ip}:/opt/goldventure/.env'],
                capture_output=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"Failed to transfer credentials: {result.stderr.decode()}")
                return False

            # Set proper permissions on remote file
            subprocess.run(
                ['ssh', '-o', 'StrictHostKeyChecking=accept-new',
                 f'root@{self.gpu_droplet_ip}',
                 'chmod 600 /opt/goldventure/.env'],
                timeout=30
            )

            logger.info("Credentials transferred securely")
            return True

        finally:
            # Clean up local temp file
            os.unlink(temp_env_path)

    def cleanup_orphaned_droplets(self):
        """Destroy any GPU droplets that are orphaned OR older than MAX_GPU_RUNTIME.
        This is a hard safety limit that works even if the orchestrator restarts."""
        try:
            response = self._api_request('GET', 'droplets?tag_name=gpu-worker&per_page=100')
            droplets = response.get('droplets', [])

            for droplet in droplets:
                droplet_id = str(droplet.get('id'))
                created_at_str = droplet.get('created_at', '')

                # Parse droplet creation time from API
                droplet_age_seconds = 0
                if created_at_str:
                    try:
                        # Parse ISO format: 2026-01-16T07:00:24Z
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        from datetime import timezone as tz
                        droplet_age_seconds = (datetime.now(tz.utc) - created_at).total_seconds()
                    except:
                        pass

                # HARD SAFETY: Destroy ANY gpu-worker droplet older than MAX_GPU_RUNTIME
                if droplet_age_seconds > self.MAX_GPU_RUNTIME:
                    logger.warning(f"GPU droplet {droplet_id} is {droplet_age_seconds/3600:.1f} hours old (exceeds {self.MAX_GPU_RUNTIME/3600:.1f}h limit), destroying!")
                    self._api_request('DELETE', f'droplets/{droplet_id}')
                    logger.info(f"Destroyed old droplet {droplet_id}")
                    # Also clear local state if this was our tracked droplet
                    if droplet_id == self.gpu_droplet_id:
                        self.gpu_droplet_id = None
                        self.gpu_droplet_ip = None
                        self.gpu_created_at = None
                        self._save_state()
                    continue

                # If not tracking this droplet and it's not ours, destroy it
                if droplet_id != self.gpu_droplet_id:
                    logger.warning(f"Found orphaned GPU droplet {droplet_id}, destroying to stop costs")
                    self._api_request('DELETE', f'droplets/{droplet_id}')
                    logger.info(f"Destroyed orphaned droplet {droplet_id}")

            if not droplets:
                logger.info("No orphaned GPU droplets found")
            elif self.gpu_droplet_id:
                logger.info(f"Found tracked GPU droplet: {self.gpu_droplet_id}")

        except Exception as e:
            logger.error(f"Error cleaning up orphaned droplets: {e}")

    def run(self):
        """Main orchestrator loop"""
        # First, clean up any orphaned droplets to prevent runaway costs
        self.cleanup_orphaned_droplets()

        logger.info("GPU Orchestrator starting...")

        while True:
            try:
                # Check if we need to create GPU droplet
                if self.should_create_gpu():
                    if self.create_gpu_droplet():
                        if self.wait_for_droplet_ready():
                            # Give it time to run cloud-init
                            logger.info("Waiting for GPU droplet initialization...")
                            time.sleep(120)
                            # Transfer credentials securely (not via cloud-init)
                            if self._transfer_credentials():
                                self.start_gpu_worker()
                            else:
                                logger.error("Failed to transfer credentials, destroying droplet")
                                self.destroy_gpu_droplet()

                # Check if we should destroy GPU droplet
                if self.should_destroy_gpu():
                    self.destroy_gpu_droplet()

                # SAFETY: Always check for old/orphaned droplets every loop iteration
                self.cleanup_orphaned_droplets()

                # Check for stuck jobs and mark them as failed
                stuck_count = self.check_and_handle_stuck_jobs()
                if stuck_count > 0 and self.gpu_droplet_id:
                    # If we found stuck jobs, the GPU worker is likely dead/frozen
                    # Destroy the droplet to stop costs and let it recreate if needed
                    logger.warning(f"Found {stuck_count} stuck jobs - destroying GPU droplet")
                    self.destroy_gpu_droplet()

                # Check GPU worker health if active and there's work to do
                pending = self.get_pending_heavy_jobs()
                processing = self.get_processing_jobs()

                if self.gpu_droplet_id:
                    # Only try to restart worker if there's work pending
                    if pending > 0 and not self.check_gpu_worker_health():
                        logger.warning("GPU worker not healthy and work pending, attempting restart...")
                        if self.start_gpu_worker():
                            self.worker_start_failures = 0  # Reset on success
                        else:
                            self.worker_start_failures += 1
                            logger.error(f"Worker start failed ({self.worker_start_failures}/{self.MAX_WORKER_FAILURES})")

                            if self.worker_start_failures >= self.MAX_WORKER_FAILURES:
                                logger.error("Too many worker failures, destroying droplet to stop costs")
                                self.destroy_gpu_droplet()
                                self.worker_start_failures = 0

                # Log status
                logger.debug(f"Queue status: {pending} pending, {processing} processing, GPU active: {bool(self.gpu_droplet_id)}")

            except Exception as e:
                logger.error(f"Orchestrator error: {e}")

            time.sleep(self.POLL_INTERVAL)


def main():
    """Entry point with exclusive lock"""
    # Acquire lock to prevent multiple instances
    if not acquire_lock():
        logger.error("Failed to acquire lock. Exiting.")
        sys.exit(1)

    # Register cleanup on exit
    atexit.register(release_lock)

    try:
        orchestrator = GPUOrchestrator()
        orchestrator.run()
    finally:
        release_lock()


if __name__ == '__main__':
    main()
