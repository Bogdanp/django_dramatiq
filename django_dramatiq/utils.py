import importlib


def load_class(path):
    try:
        module_path, _, class_name = path.rpartition(".")
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except AttributeError:
        raise ImportError("Module '%s' doesn't have a class named '%s'." % (
            module_path, class_name,
        ))


def load_middleware(path_or_obj):
    if isinstance(path_or_obj, str):
        return load_class(path_or_obj)()
    return path_or_obj
