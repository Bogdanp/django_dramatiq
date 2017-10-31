import django
django.setup()

from .tasks import broker  # noqa
