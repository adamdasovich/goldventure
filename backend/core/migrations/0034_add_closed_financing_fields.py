# Generated migration for closed financing tracking fields

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_add_dismissed_news_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='financing',
            name='is_closed',
            field=models.BooleanField(default=False, help_text='Whether this financing has been marked as closed for display'),
        ),
        migrations.AddField(
            model_name='financing',
            name='closed_at',
            field=models.DateTimeField(blank=True, help_text='When the financing was marked as closed', null=True),
        ),
        migrations.AddField(
            model_name='financing',
            name='closed_by',
            field=models.ForeignKey(blank=True, help_text='User who marked this financing as closed', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='closed_financings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='financing',
            name='source_news_flag',
            field=models.ForeignKey(blank=True, help_text='The news flag that originated this financing', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='closed_financings', to='core.newsreleaseflag'),
        ),
    ]
