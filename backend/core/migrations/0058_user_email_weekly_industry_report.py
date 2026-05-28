# Generated for User.email_weekly_industry_report_enabled.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0057_weekly_industry_report'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_weekly_industry_report_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
