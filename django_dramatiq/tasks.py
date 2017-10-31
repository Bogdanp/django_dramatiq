import dramatiq
import importlib

from django.conf import settings

DEFAULT_BROKER = "dramatiq.brokers.rabbitmq.RabbitmqBroker"
DEFAULT_SETTINGS = {
    "BROKER": DEFAULT_BROKER,
    "OPTIONS": {
        "host": "127.0.0.1",
        "port": 5672,
        "heartbeat_interval": 0,
        "connection_attempts": 5,
    },
    "MIDDLEWARE": []
}


def load_class(path):
    module_path, _, class_name = path.rpartition(".")
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def load_middleware(path_or_obj):
    if isinstance(path_or_obj, str):
        return load_class(path_or_obj)()
    return path_or_obj


broker_settings = getattr(settings, "DRAMATIQ_BROKER", DEFAULT_SETTINGS)
broker_path = broker_settings["BROKER"]
broker_class = load_class(broker_path)
broker_options = broker_settings.get("OPTIONS", {})
middleware = [load_middleware(path) for path in broker_settings.get("MIDDLEWARE", [])]
broker = broker_class(middleware=middleware, **broker_options)
dramatiq.set_broker(broker)
