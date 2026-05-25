"""
Adds NewsReportFlag for flagging news releases that mention technical reports
(NI 43-101, PEA, PFS, DFS, MRE, etc.) and relaxes the DismissedNewsURL uniqueness
constraint from `url` alone to `(url, reason)` so financing-flag dismissals and
report-flag dismissals are tracked independently.
"""

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0054_user_email_briefing_enabled'),
    ]

    operations = [
        # Step 1: drop the old `url` unique=True constraint so we can recreate
        # it as a unique-together on (url, reason).
        migrations.AlterField(
            model_name='dismissednewsurl',
            name='url',
            field=models.URLField(db_index=True, max_length=2000),
        ),
        migrations.AddConstraint(
            model_name='dismissednewsurl',
            constraint=models.UniqueConstraint(
                fields=['url', 'reason'],
                name='uniq_dismissed_url_reason',
            ),
        ),

        # Step 2: create NewsReportFlag.
        migrations.CreateModel(
            name='NewsReportFlag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flagged_at', models.DateTimeField(auto_now_add=True)),
                ('detected_keywords', models.JSONField(default=list, help_text='List of technical-report keywords that triggered the flag')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending Review'),
                        ('reviewed_processed', 'Submitted for Processing'),
                        ('reviewed_false_positive', 'False Positive - Dismissed'),
                    ],
                    default='pending',
                    max_length=30,
                )),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('report_url', models.URLField(blank=True, default='', max_length=2000)),
                ('report_type', models.CharField(
                    blank=True,
                    choices=[
                        ('ni43101', 'NI 43-101 Technical Report'),
                        ('pea', 'Preliminary Economic Assessment'),
                        ('pfs', 'Prefeasibility Study'),
                        ('dfs', 'Definitive Feasibility Study'),
                        ('mre', 'Mineral Resource Estimate'),
                        ('other', 'Other Technical Report'),
                    ],
                    default='',
                    max_length=20,
                )),
                ('review_notes', models.TextField(blank=True)),
                ('news_release', models.OneToOneField(
                    on_delete=models.deletion.CASCADE,
                    related_name='report_flag',
                    to='core.newsrelease',
                )),
                ('processing_job', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=models.deletion.SET_NULL,
                    related_name='source_report_flags',
                    to='core.documentprocessingjob',
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=models.deletion.SET_NULL,
                    related_name='reviewed_report_flags',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'news_report_flags',
                'ordering': ['-flagged_at'],
                'indexes': [
                    models.Index(fields=['status', '-flagged_at'], name='news_report_status_46c2b9_idx'),
                ],
            },
        ),
    ]
