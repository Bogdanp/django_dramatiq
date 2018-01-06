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

    # And execvp should be called with the appropriate arguments
    cores = str(rundramatiq.CPU_COUNT)
    expected_exec_name = "dramatiq"
    expected_exec_path = os.path.join(
        os.path.dirname(sys.executable),
        expected_exec_name,
    )

    execvp_mock.assert_called_once_with(expected_exec_path, [
        expected_exec_name, "--processes", cores, "--threads", cores, "--path", ".",
        "--watch", path_to().replace("/tests", ""),
        "django_dramatiq.setup",
        "tests.testapp.tasks",
    ])


@patch("os.execvp")
def test_rundramatiq_can_run_dramatiq_with_polling(execvp_mock):
    # Given an output buffer
    buff = StringIO()

    # When I call the rundramatiq command with --reload-use-polling
    call_command("rundramatiq", "--reload-use-polling", stdout=buff)

    # Then execvp should be called with the appropriate arguments
    cores = str(rundramatiq.CPU_COUNT)
    expected_exec_name = "dramatiq"
    expected_exec_path = os.path.join(
        os.path.dirname(sys.executable),
        expected_exec_name,
    )

    execvp_mock.assert_called_once_with(expected_exec_path, [
        expected_exec_name, "--processes", cores, "--threads", cores, "--path", ".",
        "--watch", path_to().replace("/tests", ""),
        "--watch-use-polling",
        "django_dramatiq.setup",
        "tests.testapp.tasks",
    ])
