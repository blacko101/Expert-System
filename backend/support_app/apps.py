from django.apps import AppConfig


class SupportAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'support_app'
    
    def ready(self):
        """Initialize application"""
        import support_app.signals