"""
Abstract Base Models for GoldVenture Platform

These abstract models provide common functionality that can be inherited
by concrete models throughout the application.

Usage:
    from core.base_models import TimestampedModel, SoftDeleteModel

    class MyModel(TimestampedModel, SoftDeleteModel):
        name = models.CharField(max_length=200)
        # ...
"""

from django.db import models
from django.utils import timezone


# =============================================================================
# MODEL MANAGERS
# =============================================================================

class SoftDeleteManager(models.Manager):
    """
    Manager that filters out soft-deleted records by default.
    Use .all_with_deleted() to include deleted records.
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        """Return all objects including soft-deleted ones."""
        return super().get_queryset()

    def deleted_only(self):
        """Return only soft-deleted objects."""
        return super().get_queryset().filter(is_deleted=True)


class ActiveManager(models.Manager):
    """
    Manager that filters to only active records.
    Use on models with is_active field.
    """

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


# =============================================================================
# ABSTRACT BASE MODELS
# =============================================================================

class TimestampedModel(models.Model):
    """
    Abstract base model that provides self-updating created_at and updated_at fields.

    Usage:
        class MyModel(TimestampedModel):
            name = models.CharField(max_length=200)
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):
    """
    Abstract base model that provides soft delete functionality.

    Instead of actually deleting records, marks them as deleted with a timestamp.
    Soft-deleted records are excluded from default queries.

    Usage:
        class MyModel(SoftDeleteModel):
            name = models.CharField(max_length=200)

        # Normal queries exclude deleted records
        MyModel.objects.all()

        # Include deleted records
        MyModel.objects.all_with_deleted()

        # Only deleted records
        MyModel.objects.deleted_only()

        # Soft delete
        instance.soft_delete()

        # Restore
        instance.restore()
    """
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted_set'
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Includes deleted records

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        """
        Soft delete this record.

        Args:
            user: Optional user who performed the deletion
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def hard_delete(self):
        """Actually delete the record from the database."""
        super().delete()


class ActivatableModel(models.Model):
    """
    Abstract base model for records that can be activated/deactivated.

    Usage:
        class MyModel(ActivatableModel):
            name = models.CharField(max_length=200)

        # Get only active records
        MyModel.active_objects.all()

        # Deactivate
        instance.deactivate()

        # Activate
        instance.activate()
    """
    is_active = models.BooleanField(default=True, db_index=True)

    objects = models.Manager()  # Default manager includes all
    active_objects = ActiveManager()  # Only active records

    class Meta:
        abstract = True

    def activate(self):
        """Activate this record."""
        self.is_active = True
        self.save(update_fields=['is_active'])

    def deactivate(self):
        """Deactivate this record."""
        self.is_active = False
        self.save(update_fields=['is_active'])


class SluggedModel(models.Model):
    """
    Abstract base model for records with URL-friendly slugs.

    Usage:
        class MyModel(SluggedModel):
            name = models.CharField(max_length=200)

            def save(self, *args, **kwargs):
                if not self.slug:
                    self.slug = slugify(self.name)
                super().save(*args, **kwargs)
    """
    slug = models.SlugField(max_length=255, unique=True, db_index=True)

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    """
    Abstract base model for records that need explicit ordering.

    Usage:
        class MyModel(OrderedModel):
            name = models.CharField(max_length=200)
    """
    display_order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ['display_order']


class AuditedModel(TimestampedModel):
    """
    Abstract base model that tracks who created and last modified a record.

    Usage:
        class MyModel(AuditedModel):
            name = models.CharField(max_length=200)
    """
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created_set'
    )
    updated_by = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated_set'
    )

    class Meta:
        abstract = True


# =============================================================================
# COMBINED ABSTRACT MODELS (Common Patterns)
# =============================================================================

class BaseContentModel(TimestampedModel, ActivatableModel):
    """
    Combined abstract model for content records that need timestamps and activation.

    Common pattern for: news, articles, announcements, etc.
    """

    class Meta:
        abstract = True
        ordering = ['-created_at']


class BaseCriticalModel(TimestampedModel, SoftDeleteModel):
    """
    Combined abstract model for critical records that should never be hard deleted.

    Common pattern for: transactions, financings, investments, etc.
    """

    class Meta:
        abstract = True
        ordering = ['-created_at']
