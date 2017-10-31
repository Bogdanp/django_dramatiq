from django.apps import AppConfig

from .tasks import broker  # noqa


class DjangoDramatiqConfig(AppConfig):
    name = "django_dramatiq"
    verbose_name = "Django Dramatiq"
