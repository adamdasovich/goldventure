# Generated manually for custom news URL support
# Add news_url field to Company model for sites with non-standard news paths

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add news_url field to Company model.

    This allows specifying a custom news page URL for companies that don't
    follow standard patterns like /news/, /press-releases/, etc.

    Example: Exploration Puma uses /en/puma-news/ instead of /en/news/
    """

    dependencies = [
        ('core', '0041_add_soft_delete_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='news_url',
            field=models.URLField(
                blank=True,
                default='',
                help_text='Custom news page URL if different from standard patterns'
            ),
        ),
    ]
