import dramatiq

from django.apps import AppConfig
from django.conf import settings

from .utils import load_class, load_middleware

DEFAULT_BROKER = "dramatiq.brokers.rabbitmq.RabbitmqBroker"
DEFAULT_SETTINGS = {
    "BROKER": DEFAULT_BROKER,
    "OPTIONS": {
        "host": "127.0.0.1",
        "port": 5672,
        "heartbeat_interval": 0,
        "connection_attempts": 5,
    },
    "MIDDLEWARE": [
        "dramatiq.middleware.Prometheus",
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.AdminMiddleware",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
    ]
}


class DjangoDramatiqConfig(AppConfig):
    name = "django_dramatiq"
    verbose_name = "Django Dramatiq"

    def ready(self):
        broker_settings = type(self).broker_settings()
        broker_path = broker_settings["BROKER"]
        broker_class = load_class(broker_path)
        broker_options = broker_settings.get("OPTIONS", {})
        middleware = [load_middleware(path) for path in broker_settings.get("MIDDLEWARE", [])]
        broker = broker_class(middleware=middleware, **broker_options)
        dramatiq.set_broker(broker)

    @classmethod
    def broker_settings(cls):
        return getattr(settings, "DRAMATIQ_BROKER", DEFAULT_SETTINGS)

    @classmethod
    def tasks_database(cls):
        return getattr(settings, "DRAMATIQ_TASKS_DATABASE", "default")
