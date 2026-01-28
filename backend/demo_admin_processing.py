"""
Demo: Admin Document Processing System
Shows how to programmatically create and process document jobs
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import DocumentProcessingJob, User
from core.tasks import process_single_job


def demo_batch_processing():
    """Demo creating multiple jobs and processing them"""

    print("="*80)
    print("DEMO: ADMIN DOCUMENT PROCESSING SYSTEM")
    print("="*80)

    # Get or create admin user
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("\n[!] No admin user found. Creating one...")
        # Use environment variable for password, fail if not set
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            raise ValueError("ADMIN_PASSWORD environment variable required to create admin user")
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password=admin_password
        )
        print(f"[OK] Created admin user: {admin_user.username}")
    else:
        print(f"\n[OK] Using existing admin: {admin_user.username}")

    # Example URLs (you can replace with real URLs)
    example_urls = [
        "https://www.1911gold.com/_resources/reports/2024-43-101-True-North-Gold-Project.pdf",
        # Add more URLs here for batch processing
    ]

    print(f"\n{'='*80}")
    print("CREATING PROCESSING JOBS")
    print("="*80)

    jobs_created = []
    for url in example_urls:
        job = DocumentProcessingJob.objects.create(
            url=url,
            document_type='ni43101',
            company_name='',  # Auto-detect
            project_name='',  # Auto-detect
            created_by=admin_user
        )
        jobs_created.append(job)
        print(f"[OK] Created job #{job.id}: {url[:60]}...")

    print(f"\n[OK] Created {len(jobs_created)} job(s)")

    # Show admin URLs
    print(f"\n{'='*80}")
    print("ADMIN INTERFACE ACCESS")
    print("="*80)
    print("\n1. Start Django server:")
    print("   python manage.py runserver")
    print("\n2. Go to admin:")
    print("   http://localhost:8000/admin/")
    print("\n3. Navigate to:")
    print("   Core → Document processing jobs")
    print("\n4. View your jobs:")
    for job in jobs_created:
        print(f"   - Job #{job.id}: {job.get_status_display()}")

    print(f"\n5. Click 'Process Queue' to start processing")

    print(f"\n{'='*80}")
    print("PROGRAMMATIC PROCESSING (OPTIONAL)")
    print("="*80)

    response = input("\n Would you like to process the first job now? (y/n): ").strip().lower()

    if response == 'y':
        job = jobs_created[0]
        print(f"\n[INFO] Processing job #{job.id}...")
        print(f"[INFO] URL: {job.url}")
        print(f"[INFO] This will take 30-90 minutes depending on document size")
        print(f"[INFO] Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        from datetime import datetime
        process_single_job(job)

        # Refresh from database
        job.refresh_from_db()

        print(f"\n{'='*80}")
        print(f"JOB #{job.id} RESULTS")
        print("="*80)
        print(f"Status: {job.get_status_display()}")
        print(f"Duration: {job.duration_display}")

        if job.status == 'completed':
            print(f"Document ID: {job.document_id}")
            print(f"Resources created: {job.resources_created}")
            print(f"Chunks created: {job.chunks_created}")
            print(f"\n[OK] Document successfully processed and searchable via chatbot!")
        else:
            print(f"Error: {job.error_message}")

    else:
        print("\n[OK] Jobs created but not processed.")
        print("     Use the admin interface to process them when ready.")

    print(f"\n{'='*80}")
    print("DEMO COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Access admin at http://localhost:8000/admin/")
    print("2. Use 'Batch Add' to add multiple URLs at once")
    print("3. Click 'Process Queue' to process all pending jobs")
    print("4. Monitor progress in real-time")
    print("\nFor more info, see: ADMIN_DOCUMENT_PROCESSING.md")


if __name__ == "__main__":
    demo_batch_processing()
