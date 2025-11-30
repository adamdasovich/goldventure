"""
Create a test speaker event for demonstration
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Company, User, SpeakerEvent, EventSpeaker

# Get company (1911 Gold Corporation - ID 2)
try:
    company = Company.objects.get(id=2)
    print(f"[OK] Found company: {company.name}")
except Company.DoesNotExist:
    print("[ERROR] Company with ID 2 not found. Using first available company.")
    company = Company.objects.first()
    if not company:
        print("[ERROR] No companies found in database!")
        exit(1)

# Get or create a user to be the event creator
user = User.objects.first()
if not user:
    print("[ERROR] No users found in database!")
    exit(1)
print(f"[OK] Using user: {user.username}")

# Create a speaker event scheduled for tomorrow
scheduled_start = datetime.now() + timedelta(days=1)
scheduled_end = scheduled_start + timedelta(hours=1)

event, created = SpeakerEvent.objects.get_or_create(
    company=company,
    title="Q4 2024 Results & 2025 Outlook",
    defaults={
        'created_by': user,
        'description': 'Join our executive team as we discuss Q4 2024 financial results, operational highlights, and our strategic vision for 2025. This is an excellent opportunity for investors and analysts to ask questions directly to our CEO and CFO.',
        'topic': 'Financial Results',
        'scheduled_start': scheduled_start,
        'scheduled_end': scheduled_end,
        'duration_minutes': 60,
        'format': 'video',
        'status': 'scheduled',
        'max_participants': 100,
    }
)

if created:
    print(f"[OK] Created event: {event.title}")
    print(f"  Scheduled for: {event.scheduled_start}")
    print(f"  Format: {event.format}")
    print(f"  Status: {event.status}")

    # Add a speaker
    speaker, created = EventSpeaker.objects.get_or_create(
        event=event,
        user=user,
        defaults={
            'title': 'CEO & President',
            'bio': 'Leading 1911 Gold Corporation with over 20 years of mining industry experience.',
            'is_primary': True,
        }
    )
    if created:
        print(f"[OK] Added speaker: {speaker.user.username} - {speaker.title}")
else:
    print(f"[OK] Event already exists: {event.title}")

print("\n[SUCCESS] Test event ready!")
print(f"\nView on homepage: http://localhost:3000/")
print(f"View on company page: http://localhost:3000/companies/{company.id}")
print(f"Django admin: http://localhost:8000/admin/core/speakerevent/{event.id}/change/")
