import dramatiq
from django.conf import settings
from django.utils.module_loading import import_string


def load_middleware(path_or_obj):
    if isinstance(path_or_obj, str):
        return import_string(path_or_obj)()
    return path_or_obj


def actor(fn=None, **kwargs):
    """Declare an actor, using configurable defaults from `django.conf.settings`. """
    options = getattr(settings, 'DRAMATIQ_TASK_DEFAULTS', None)
    if isinstance(options, dict):
        for k, v in options.items():
            kwargs.setdefault(k, v)
    return dramatiq.actor(fn, **kwargs)
