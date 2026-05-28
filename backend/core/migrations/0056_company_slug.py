"""
Adds slug field to Company for SEO-friendly URLs (/companies/{id}-{slug}).

Backfills existing rows by slugifying name. Slug is auto-maintained by
Company.save() going forward.
"""

from django.db import migrations, models
from django.utils.text import slugify


def backfill_slugs(apps, schema_editor):
    Company = apps.get_model('core', 'Company')
    for company in Company.objects.all().only('id', 'name', 'slug'):
        new_slug = slugify(company.name or '')[:220]
        if new_slug and company.slug != new_slug:
            company.slug = new_slug
            company.save(update_fields=['slug'])


def reverse_noop(apps, schema_editor):
    # No reverse data migration needed — field removal handles cleanup.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0055_newsreportflag_and_dismissed_reason_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='slug',
            field=models.SlugField(
                blank=True,
                default='',
                help_text='URL-friendly slug derived from name; used in /companies/{id}-{slug}',
                max_length=220,
            ),
        ),
        migrations.AddIndex(
            model_name='company',
            index=models.Index(fields=['slug'], name='idx_company_slug'),
        ),
        migrations.RunPython(backfill_slugs, reverse_noop),
    ]
