import dramatiq
from django.apps import AppConfig
from django.conf import settings
from dramatiq.results import Results

from .utils import load_class, load_middleware

DEFAULT_ENCODER = "dramatiq.encoder.JSONEncoder"

DEFAULT_BROKER = "dramatiq.brokers.rabbitmq.RabbitmqBroker"
DEFAULT_BROKER_SETTINGS = {
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

RATE_LIMITER_BACKEND = None


class DjangoDramatiqConfig(AppConfig):
    name = "django_dramatiq"
    verbose_name = "Django Dramatiq"

    @classmethod
    def initialize(cls):
        global RATE_LIMITER_BACKEND

        dramatiq.set_encoder(cls.select_encoder())

        result_backend_settings = cls.result_backend_settings()
        if result_backend_settings:
            result_backend_path = result_backend_settings.get("BACKEND", "dramatiq.results.backends.StubBackend")
            result_backend_class = load_class(result_backend_path)
            result_backend_options = result_backend_settings.get("BACKEND_OPTIONS", {})
            result_backend = result_backend_class(**result_backend_options)

            results_middleware_options = result_backend_settings.get("MIDDLEWARE_OPTIONS", {})
            results_middleware = Results(backend=result_backend, **results_middleware_options)
        else:
            result_backend = None
            results_middleware = None

        rate_limiter_backend_settings = cls.rate_limiter_backend_settings()
        if rate_limiter_backend_settings:
            rate_limiter_backend_path = rate_limiter_backend_settings.get(
                "BACKEND", "dramatiq.rate_limits.backends.stub.StubBackend"
            )
            rate_limiter_backend_class = load_class(rate_limiter_backend_path)
            rate_limiter_backend_options = result_backend_settings.get("BACKEND_OPTIONS", {})
            RATE_LIMITER_BACKEND = rate_limiter_backend_class(**rate_limiter_backend_options)

        broker_settings = cls.broker_settings()
        broker_path = broker_settings["BROKER"]
        broker_class = load_class(broker_path)
        broker_options = broker_settings.get("OPTIONS", {})
        middleware = [load_middleware(path) for path in broker_settings.get("MIDDLEWARE", [])]

        if result_backend is not None:
            middleware.append(results_middleware)

        broker = broker_class(middleware=middleware, **broker_options)
        dramatiq.set_broker(broker)

    @property
    def rate_limiter_backend(self):
        global RATE_LIMITER_BACKEND
        if RATE_LIMITER_BACKEND is None:
            raise RuntimeError("The rate limiter backend has not been configured.")

        return RATE_LIMITER_BACKEND

    @classmethod
    def broker_settings(cls):
        return getattr(settings, "DRAMATIQ_BROKER", DEFAULT_BROKER_SETTINGS)

    @classmethod
    def result_backend_settings(cls):
        return getattr(settings, "DRAMATIQ_RESULT_BACKEND", {})

    @classmethod
    def rate_limiter_backend_settings(cls):
        return getattr(settings, "DRAMATIQ_RATE_LIMITER_BACKEND", {})

    @classmethod
    def tasks_database(cls):
        return getattr(settings, "DRAMATIQ_TASKS_DATABASE", "default")

    @classmethod
    def select_encoder(cls):
        encoder = getattr(settings, "DRAMATIQ_ENCODER", DEFAULT_ENCODER)
        return load_class(encoder)()


DjangoDramatiqConfig.initialize()
