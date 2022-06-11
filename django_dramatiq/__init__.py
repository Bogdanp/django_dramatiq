import django

__version__ = "0.11.0"

if django.VERSION < (3, 2):
    default_app_config = "django_dramatiq.apps.DjangoDramatiqConfig"
