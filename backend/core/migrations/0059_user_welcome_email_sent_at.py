# Generated for User.welcome_email_sent_at.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0058_user_email_weekly_industry_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='welcome_email_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
