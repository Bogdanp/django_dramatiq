import dramatiq
from django.conf import settings


def actor(fn=None, **kwargs):
    """Declare an actor, using configurable defaults from `django.conf.settings`. """
    options = getattr(settings, 'DRAMATIQ_TASK_DEFAULTS', None)
    if isinstance(options, dict):
        for k, v in options.items():
            kwargs.setdefault(k, v)
    return dramatiq.actor(fn, **kwargs)
