from django.utils.module_loading import import_string


def load_middleware(path_or_obj, **kwargs):
    if isinstance(path_or_obj, str):
        return import_string(path_or_obj)(**kwargs)
    return path_or_obj
