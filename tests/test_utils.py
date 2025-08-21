import os

import pytest

from django_dramatiq.utils import getenv_int


@pytest.mark.parametrize("value, default, expected", (
    ("42", None, 42),
    ("invalid", 69, 69),
    ("invalid", None, ValueError),
    ("invalid", lambda: 96, 96),
    (None, 19, 19),
    (None, lambda: 78, 78),
    (None, "hello", "hello"),  # returned default is not checked to be an int
    (None, lambda: "world", "world")  # idem
))
def test_getenv_int(value, default, expected):
    varname = "TEST_ENV_20250204"
    if value is not None:
        os.environ[varname] = value
    else:
        os.environ.pop(varname, None)

    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            getenv_int(varname, default)
    else:
        assert getenv_int(varname, default) == expected
