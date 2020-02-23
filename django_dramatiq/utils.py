from django.utils.module_loading import import_string


def load_middleware(path_or_obj):
    if isinstance(path_or_obj, str):
        return import_string(path_or_obj)()
    return path_or_obj
