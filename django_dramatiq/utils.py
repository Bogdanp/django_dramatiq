import dramatiq
from django.conf import settings
from django.utils.module_loading import import_string


class NotDefined:
    pass


def load_middleware(path_or_obj):
    if isinstance(path_or_obj, str):
        return import_string(path_or_obj)()
    return path_or_obj


_actor_params = ['actor_class', 'actor_name', 'queue_name', 'priority', 'broker']


def _set_actor_defaults(kwargs):
    for key in _actor_params:
        default = getattr(settings, 'DRAMATIQ_TASK_DEFAULT_{}'.format(key.upper()), NotDefined)
        if default is not NotDefined and key not in kwargs:
            kwargs[key] = default

    # special case for **options
    options = getattr(settings, 'DRAMATIQ_TASK_DEFAULT_OPTIONS', NotDefined)
    if isinstance(options, dict):
        kwargs.update(options)


def actor(fn=None, **kwargs):
    """Declare an actor, using configurable defaults from `django.conf.settings`. """
    _set_actor_defaults(kwargs)
    return dramatiq.actor(fn, **kwargs)
