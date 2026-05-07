import os

import pytest
from django.test import override_settings

from django_dramatiq.apps import DEFAULT_BROKER_SETTINGS, DjangoDramatiqConfig
from django_dramatiq.utils import getenv_int


@pytest.mark.parametrize(
    "value, default, expected",
    (
        ("42", None, 42),
        ("invalid", 69, 69),
        ("invalid", None, ValueError),
        ("invalid", lambda: 96, 96),
        (None, 19, 19),
        (None, lambda: 78, 78),
        (None, "hello", "hello"),  # returned default is not checked to be an int
        (None, lambda: "world", "world"),  # idem
    ),
)
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


def test_default_broker_uses_supported_prometheus_import_path():
    assert DEFAULT_BROKER_SETTINGS["MIDDLEWARE"][0] == "dramatiq.middleware.prometheus.Prometheus"


@override_settings(
    DRAMATIQ_BROKER={"BROKER": "dramatiq.brokers.stub.StubBroker", "OPTIONS": {}, "MIDDLEWARE": []},
    DRAMATIQ_RESULT_BACKEND={"BACKEND": "dramatiq.results.backends.stub.StubBackend"},
    DRAMATIQ_RATE_LIMITER_BACKEND={"BACKEND": "dramatiq.rate_limits.backends.stub.StubBackend"},
    DRAMATIQ_TASKS_DATABASE="secondary",
)
def test_config_reads_overrides_from_settings():
    assert DjangoDramatiqConfig.broker_settings()["BROKER"] == "dramatiq.brokers.stub.StubBroker"
    assert DjangoDramatiqConfig.result_backend_settings()["BACKEND"] == "dramatiq.results.backends.stub.StubBackend"
    assert (
        DjangoDramatiqConfig.rate_limiter_backend_settings()["BACKEND"]
        == "dramatiq.rate_limits.backends.stub.StubBackend"
    )
    assert DjangoDramatiqConfig.tasks_database() == "secondary"
