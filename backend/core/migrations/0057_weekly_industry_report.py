# Generated for WeeklyIndustryReport (Friday weekly industry report).

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0056_company_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeeklyIndustryReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_ending', models.DateField(unique=True)),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('generating', 'Generating'),
                        ('completed', 'Completed'),
                        ('failed', 'Failed'),
                    ],
                    default='pending',
                    max_length=20,
                )),
                ('html', models.TextField(blank=True, default='')),
                ('pdf_file', models.FileField(blank=True, null=True, upload_to='reports/weekly/')),
                ('data_snapshot', models.JSONField(blank=True, default=dict)),
                ('executive_summary', models.TextField(blank=True, default='')),
                ('generated_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('generation_duration_seconds', models.IntegerField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'weekly_industry_reports',
                'ordering': ['-week_ending'],
                'indexes': [
                    models.Index(fields=['-week_ending'], name='weekly_repo_week_en_idx'),
                    models.Index(fields=['status', '-week_ending'], name='weekly_repo_status__idx'),
                ],
            },
        ),
    ]
