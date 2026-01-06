from django.apps import AppConfig


class DesignConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Design'

    def ready(self):
        """
        Import signals when Django starts
        This ensures automatic cache invalidation works
        """
        import Design.signals  # noqa
