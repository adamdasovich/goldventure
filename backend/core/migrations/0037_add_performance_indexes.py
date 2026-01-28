# Generated manually for performance optimization
# Add missing database indexes identified in deep dive audit

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_add_missing_fields_to_marketdata_and_metalprice'),
    ]

    operations = [
        # NewsRelease indexes - frequently queried by date and company
        migrations.AddIndex(
            model_name='newsrelease',
            index=models.Index(fields=['-release_date'], name='newsrel_date_idx'),
        ),
        migrations.AddIndex(
            model_name='newsrelease',
            index=models.Index(fields=['company', '-release_date'], name='newsrel_comp_date_idx'),
        ),

        # Financing indexes - queried by announced_date, company
        migrations.AddIndex(
            model_name='financing',
            index=models.Index(fields=['-announced_date'], name='financing_ann_date_idx'),
        ),
        migrations.AddIndex(
            model_name='financing',
            index=models.Index(fields=['company', '-announced_date'], name='financing_comp_date_idx'),
        ),
        migrations.AddIndex(
            model_name='financing',
            index=models.Index(fields=['status', '-announced_date'], name='financing_status_date_idx'),
        ),

        # ScrapingJob indexes - job monitoring queries
        migrations.AddIndex(
            model_name='scrapingjob',
            index=models.Index(fields=['status', '-created_at'], name='scraping_status_date_idx'),
        ),
        migrations.AddIndex(
            model_name='scrapingjob',
            index=models.Index(fields=['company', '-created_at'], name='scraping_comp_date_idx'),
        ),

        # CompanyNews additional indexes - filtering by type
        migrations.AddIndex(
            model_name='companynews',
            index=models.Index(fields=['news_type', '-publication_date'], name='compnews_type_date_idx'),
        ),
        migrations.AddIndex(
            model_name='companynews',
            index=models.Index(fields=['is_material', '-publication_date'], name='compnews_mat_date_idx'),
        ),

        # NewsReleaseFlag indexes - admin review queries
        migrations.AddIndex(
            model_name='newsreleaseflag',
            index=models.Index(fields=['status', '-flagged_at'], name='newsflg_status_date_idx'),
        ),
    ]
