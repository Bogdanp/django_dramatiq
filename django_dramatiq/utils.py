import logging
import os

from django.utils.module_loading import import_string


def getenv_int(varname, default=None):
    """Retrieves an environment variable as an int."""
    envstr = os.getenv(varname, None)

    if envstr is not None:
        try:
            return int(envstr)
        except ValueError:
            if default is None:
                raise
            msgf = "Invalid value for %s: %r. Reverting to default."
            logging.warning(msgf, varname, envstr)

    if callable(default):
        return default()
    else:
        return default


def load_middleware(path_or_obj, **kwargs):
    if isinstance(path_or_obj, str):
        return import_string(path_or_obj)(**kwargs)
    return path_or_obj
