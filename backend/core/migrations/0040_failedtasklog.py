# Generated manually for failed task logging
# Add FailedTaskLog model for dead letter queue functionality

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_add_check_constraints'),
    ]

    operations = [
        migrations.CreateModel(
            name='FailedTaskLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_name', models.CharField(db_index=True, max_length=255)),
                ('task_id', models.CharField(max_length=255, unique=True)),
                ('args', models.TextField(blank=True, default='')),
                ('kwargs', models.TextField(blank=True, default='')),
                ('exception_type', models.CharField(max_length=255)),
                ('exception_message', models.TextField()),
                ('traceback', models.TextField()),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending Review'),
                        ('reviewed', 'Reviewed'),
                        ('reprocessed', 'Reprocessed'),
                        ('ignored', 'Ignored'),
                    ],
                    db_index=True,
                    default='pending',
                    max_length=20
                )),
                ('review_notes', models.TextField(blank=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_failed_tasks',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Failed Task Log',
                'verbose_name_plural': 'Failed Task Logs',
                'db_table': 'failed_task_log',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='failedtasklog',
            index=models.Index(fields=['task_name', '-created_at'], name='failedtask_name_date_idx'),
        ),
        migrations.AddIndex(
            model_name='failedtasklog',
            index=models.Index(fields=['status', '-created_at'], name='failedtask_status_date_idx'),
        ),
    ]
