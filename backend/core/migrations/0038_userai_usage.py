# Generated manually for AI usage tracking
# Adds UserAIUsage model for cost control

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0037_add_performance_indexes'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAIUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('messages_today', models.IntegerField(default=0, help_text='Messages sent today')),
                ('tokens_today', models.IntegerField(default=0, help_text='Total tokens used today (input + output)')),
                ('last_reset_date', models.DateField(auto_now_add=True, help_text='Date of last counter reset')),
                ('total_messages', models.IntegerField(default=0)),
                ('total_tokens', models.IntegerField(default=0)),
                ('daily_message_limit', models.IntegerField(default=50, help_text='Max messages per day (0 = unlimited)')),
                ('daily_token_limit', models.IntegerField(default=100000, help_text='Max tokens per day (0 = unlimited)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='ai_usage', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User AI Usage',
                'verbose_name_plural': 'User AI Usage',
                'db_table': 'user_ai_usage',
            },
        ),
    ]
