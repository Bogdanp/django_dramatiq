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
    return load_class(path_or_obj)()


broker_settings = getattr(settings, "DRAMATIQ_BROKER", DEFAULT_SETTINGS)
broker_path = broker_settings["BROKER"]
broker_class = load_class(broker_path)
broker_options = broker_settings.get("OPTIONS", {})
middleware = [load_middleware(path) for path in broker_settings.get("MIDDLEWARE", [])]
broker = broker_class(middleware=middleware, **broker_options)
dramatiq.set_broker(broker)


@dramatiq.actor
def delete_old_tasks(max_task_age=86400):
    """This task deletes all tasks older than `max_task_age` from the
    database.
    """
    from .models import Task
    Task.tasks.delete_old_tasks(max_task_age)
