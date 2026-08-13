"""Settle long-standing drift between the models and the migration history.

'makemigrations' had been proposing these on every run, which meant any new
migration risked dragging them along unreviewed - migration 0060 nearly did.

Three index renames (metadata-only in Postgres) and two id columns widened from
integer to bigint to match DEFAULT_AUTO_FIELD. Both rewrites are on small
tables - 216 and 12 rows in production - so the lock is momentary.

Deliberately NOT here: dropping companies.idx_company_slug. makemigrations
wanted to, because migration 0056 created the index but the model never
declared it. Slug is the lookup key for company URLs, so the index has been
declared on the model instead and stays in place.
"""


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0060_processed_stripe_event'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='newsreportflag',
            new_name='news_report_status_30a85c_idx',
            old_name='news_report_status_46c2b9_idx',
        ),
        migrations.RenameIndex(
            model_name='weeklyindustryreport',
            new_name='weekly_indu_week_en_b1a12c_idx',
            old_name='weekly_repo_week_en_idx',
        ),
        migrations.RenameIndex(
            model_name='weeklyindustryreport',
            new_name='weekly_indu_status_a558f9_idx',
            old_name='weekly_repo_status__idx',
        ),
        migrations.AlterField(
            model_name='newsreportflag',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='weeklyindustryreport',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
