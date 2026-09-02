from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Registers the post_delete receivers that keep ChromaDB from
        # outliving the chunk rows it mirrors. Imported for the side effect.
        from . import signals  # noqa: F401
