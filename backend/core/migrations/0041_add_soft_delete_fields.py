# Generated manually for soft delete functionality
# Add soft delete fields to critical models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Add soft delete fields to critical business models.

    This ensures that important records are never permanently deleted,
    allowing for audit trails and data recovery.
    """

    dependencies = [
        ('core', '0040_failedtasklog'),
    ]

    operations = [
        # =====================================================================
        # COMPANY MODEL - Soft Delete Fields
        # =====================================================================
        migrations.AddField(
            model_name='company',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='company',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='deleted_companies',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # =====================================================================
        # FINANCING MODEL - Soft Delete Fields
        # =====================================================================
        migrations.AddField(
            model_name='financing',
            name='is_deleted',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='financing',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='financing',
            name='deleted_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='deleted_financings',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # =====================================================================
        # INDEXES for soft delete queries
        # =====================================================================
        migrations.AddIndex(
            model_name='company',
            index=models.Index(fields=['is_deleted', 'is_active'], name='company_soft_del_idx'),
        ),
        migrations.AddIndex(
            model_name='financing',
            index=models.Index(fields=['is_deleted', '-announced_date'], name='financing_soft_del_idx'),
        ),
    ]
