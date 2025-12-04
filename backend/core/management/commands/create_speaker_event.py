from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import User, Company, SpeakerEvent, EventSpeaker


class Command(BaseCommand):
    help = 'Creates a test speaking event with speakers'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating speaker event...'))

        # Get or create users
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )

        # Get company (use existing one or create)
        try:
            company = Company.objects.get(ticker_symbol='GOLD')
        except Company.DoesNotExist:
            company = Company.objects.create(
                name='Golden Minerals Corp',
                ticker_symbol='GOLD',
                description='Premier gold mining company'
            )

        # Create speaking event scheduled for tomorrow
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)

        event, created = SpeakerEvent.objects.get_or_create(
            company=company,
            title='Q4 2024 Exploration Results & 2025 Outlook',
            defaults={
                'created_by': admin,
                'description': 'Join us for an exclusive investor presentation where our CEO and Lead Geologist will discuss our Q4 2024 exploration results, including new high-grade gold discoveries, and unveil our strategic plans for 2025.',
                'topic': 'Quarterly Results & Future Strategy',
                'agenda': '''
**Event Agenda:**

**1. Welcome & Introduction** (5 min)
- Opening remarks
- Event format overview

**2. Q4 2024 Exploration Results** (20 min)
- High-grade gold discoveries at North Zone
- Drilling program summary
- Resource expansion update
- Metallurgical test results

**3. 2025 Strategic Outlook** (15 min)
- Planned drilling campaigns
- Infrastructure development
- Permitting progress
- Capital allocation strategy

**4. Live Q&A Session** (20 min)
- Real-time questions from investors
- Technical discussion
- Investment opportunities
                ''',
                'scheduled_start': start_time,
                'scheduled_end': end_time,
                'timezone': 'America/Toronto',
                'duration_minutes': 60,
                'format': 'video',
                'status': 'scheduled',
                'max_participants': 500,
                'is_recorded': True,
                'recording_url': '',
                'transcript_url': '',
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Created event: {event.title}'))

            # Create speakers
            ceo, _ = User.objects.get_or_create(
                username='john_smith',
                defaults={
                    'email': 'john.smith@goldenminerals.com',
                    'first_name': 'John',
                    'last_name': 'Smith'
                }
            )

            speaker1, created1 = EventSpeaker.objects.get_or_create(
                event=event,
                user=ceo,
                defaults={
                    'title': 'Chief Executive Officer',
                    'bio': 'John Smith brings over 20 years of experience in mining operations and corporate development. He has led Golden Minerals Corp since 2018, overseeing significant resource expansion and operational improvements.',
                    'is_primary': True
                }
            )
            if created1:
                self.stdout.write(self.style.SUCCESS(f'[OK] Added speaker: {ceo.get_full_name()} - CEO'))

            geologist, _ = User.objects.get_or_create(
                username='sarah_jones',
                defaults={
                    'email': 'sarah.jones@goldenminerals.com',
                    'first_name': 'Sarah',
                    'last_name': 'Jones'
                }
            )

            speaker2, created2 = EventSpeaker.objects.get_or_create(
                event=event,
                user=geologist,
                defaults={
                    'title': 'Lead Exploration Geologist',
                    'bio': 'Sarah Jones is a professional geologist with 15 years of experience in mineral exploration. She has been instrumental in the recent high-grade gold discoveries and leads all exploration activities.',
                    'is_primary': False
                }
            )
            if created2:
                self.stdout.write(self.style.SUCCESS(f'[OK] Added speaker: {geologist.get_full_name()} - Lead Geologist'))

        else:
            self.stdout.write('[OK] Event already exists, updating...')
            event.status = 'scheduled'
            event.save()

        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('SPEAKER EVENT CREATED!'))
        self.stdout.write('='*60)
        self.stdout.write(f'\nEvent Details:')
        self.stdout.write(f'  Title: {event.title}')
        self.stdout.write(f'  Company: {event.company.name}')
        self.stdout.write(f'  Status: {event.get_status_display()}')
        self.stdout.write(f'  Format: {event.get_format_display()}')
        self.stdout.write(f'  Scheduled: {event.scheduled_start.strftime("%Y-%m-%d %H:%M %Z")}')
        self.stdout.write(f'  Duration: {event.duration_minutes} minutes')
        self.stdout.write(f'  Max Participants: {event.max_participants}')
        self.stdout.write(f'  Speakers: {event.speakers.count()}')

        for speaker in event.speakers.all():
            marker = '(Primary)' if speaker.is_primary else ''
            self.stdout.write(f'    - {speaker.user.get_full_name()} - {speaker.title} {marker}')

        self.stdout.write(f'\nView event at:')
        self.stdout.write(f'  http://localhost:3000/companies/{company.id}/events/{event.id}')
        self.stdout.write('='*60)
