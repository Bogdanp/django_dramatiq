from django.apps import AppConfig


class Testapp1Config(AppConfig):
    name = "tests.testapp1"

    def ready(self):
        from . import tasks  # noqa
