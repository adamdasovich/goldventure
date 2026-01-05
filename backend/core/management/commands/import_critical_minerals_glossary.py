"""
Django management command to import critical minerals glossary terms
Usage: python manage.py import_critical_minerals_glossary
"""

import json
import os
from django.core.management.base import BaseCommand
from core.models import GlossaryTerm


class Command(BaseCommand):
    help = 'Import critical minerals, silver, lithium, REE, and battery metals glossary terms'

    def handle(self, *args, **options):
        """Import 50+ new glossary terms for multi-commodity expansion"""

        # Load JSON file
        json_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'glossary_terms_critical_minerals.json')

        self.stdout.write(self.style.NOTICE(f'Loading glossary terms from: {json_path}'))

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                terms_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'JSON file not found at: {json_path}'))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON format: {e}'))
            return

        self.stdout.write(self.style.NOTICE(f'Found {len(terms_data)} terms to import'))

        created_count = 0
        updated_count = 0
        error_count = 0

        for term_data in terms_data:
            try:
                term, created = GlossaryTerm.objects.update_or_create(
                    term=term_data['term'],
                    defaults={
                        'definition': term_data['definition'],
                        'category': term_data['category'],
                        'related_links': term_data.get('related_links', []),
                        'keywords': term_data.get('keywords', ''),
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'✓ Created: {term.term}'))
                else:
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f'↻ Updated: {term.term}'))

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'✗ Error importing {term_data.get("term", "Unknown")}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\n=== Critical Minerals Glossary Import Complete ==='))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count} new terms'))
        self.stdout.write(self.style.SUCCESS(f'Updated: {updated_count} existing terms'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count} terms failed'))
        self.stdout.write(self.style.SUCCESS(f'Total processed: {created_count + updated_count} terms'))

        # Show category breakdown
        self.stdout.write(self.style.NOTICE(f'\nCategory Breakdown:'))
        categories = {}
        for term_data in terms_data:
            cat = term_data['category']
            categories[cat] = categories.get(cat, 0) + 1

        for category, count in sorted(categories.items()):
            self.stdout.write(f'  {category}: {count} terms')
