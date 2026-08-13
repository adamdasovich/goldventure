"""Add ProcessedStripeEvent, the webhook idempotency ledger.

Hand-trimmed. `makemigrations` also wanted to fold in six unrelated operations
that come from pre-existing drift between the models and the migration history
(dropping company.idx_company_slug, renaming three indexes, and rewriting the
`id` column on newsreportflag/weeklyindustryreport). Dropping a live index and
rewriting two tables under lock has no business riding along with a payments
change, so those are left for a deliberate migration of their own.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0059_user_welcome_email_sent_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessedStripeEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.CharField(max_length=255, unique=True)),
                ('event_type', models.CharField(max_length=100)),
                ('handler', models.CharField(max_length=50)),
                ('processed_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'processed_stripe_events',
                'ordering': ['-processed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='processedstripeevent',
            index=models.Index(fields=['event_id'], name='processed_s_event_i_10cf4f_idx'),
        ),
        migrations.AddIndex(
            model_name='processedstripeevent',
            index=models.Index(fields=['processed_at'], name='processed_s_process_0fde32_idx'),
        ),
    ]
