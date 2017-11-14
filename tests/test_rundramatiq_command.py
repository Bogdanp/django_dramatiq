import os
import sys

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django_dramatiq.management.commands import rundramatiq

from .settings import path_to


def test_rundramatiq_command_autodiscovers_modules():
    assert rundramatiq.Command().discover_tasks_modules() == [
        "django_dramatiq.setup",
        "tests.testapp.tasks",
    ]


@patch("os.execvp")
def test_rundramatiq_can_run_dramatiq(execvp_mock):
    # Given an output buffer
    buff = StringIO()

    # When I call the rundramatiq command
    call_command("rundramatiq", stdout=buff)

    # Then stdout should contain a message about discovered task modules
    assert "Discovered tasks module: 'tests.testapp.tasks'" in buff.getvalue()

    expected_exec_path = os.path.join(
        os.path.dirname(sys.executable),
        'dramatiq'
    )

    # And execvp should be called with the appropriate arguments
    cores = str(rundramatiq.CPU_COUNT)
    execvp_mock.assert_called_once_with(expected_exec_path, [
        expected_exec_path, "--processes", cores, "--threads", cores,
        "--watch", path_to().replace("/tests", ""),
        "django_dramatiq.setup",
        "tests.testapp.tasks",
    ])
