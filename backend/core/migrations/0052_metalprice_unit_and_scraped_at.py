import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_platform_subscriptions'),
    ]

    operations = [
        migrations.AddField(
            model_name='metalprice',
            name='unit',
            field=models.CharField(default='oz', max_length=10),
        ),
        # Switch scraped_at off auto_now_add so backfill jobs can write the
        # real historical trading datetime. Existing rows keep their values.
        migrations.AlterField(
            model_name='metalprice',
            name='scraped_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
