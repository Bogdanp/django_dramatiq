import os
import sys
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command

from django_dramatiq.management.commands import rundramatiq


def test_rundramatiq_command_autodiscovers_modules():
    assert rundramatiq.Command().discover_tasks_modules() == [
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
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
        expected_exec_name, "--path", ".", "--processes", cores, "--threads", cores,
        "--watch", ".",
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
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
        expected_exec_name, "--path", ".", "--processes", cores, "--threads", cores,
        "--watch", ".",
        "--watch-use-polling",
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
        "tests.testapp.tasks",
    ])


@patch("os.execvp")
def test_rundramatiq_can_run_dramatiq_with_only_some_queues(execvp_mock):
    # Given an output buffer
    buff = StringIO()

    # When I call the rundramatiq command with --queues
    call_command("rundramatiq", "--queues", "A B C", stdout=buff)

    # Then execvp should be called with the appropriate arguments
    cores = str(rundramatiq.CPU_COUNT)
    expected_exec_name = "dramatiq"
    expected_exec_path = os.path.join(
        os.path.dirname(sys.executable),
        expected_exec_name,
    )

    execvp_mock.assert_called_once_with(expected_exec_path, [
        expected_exec_name, "--path", ".", "--processes", cores, "--threads", cores,
        "--watch", ".",
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
        "tests.testapp.tasks",
        "--queues", "A B C"
    ])


@patch("os.execvp")
def test_rundramatiq_can_run_dramatiq_with_specified_pid_file(execvp_mock):
    # Given an output buffer
    buff = StringIO()

    # When I call the rundramatiq command with --pid-file
    call_command("rundramatiq", "--pid-file", "drama.pid", stdout=buff)

    # Then execvp should be called with the appropriate arguments
    cores = str(rundramatiq.CPU_COUNT)
    expected_exec_name = "dramatiq"
    expected_exec_path = os.path.join(
        os.path.dirname(sys.executable),
        expected_exec_name,
    )

    execvp_mock.assert_called_once_with(expected_exec_path, [
        expected_exec_name, "--path", ".", "--processes", cores, "--threads", cores,
        "--watch", ".",
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
        "tests.testapp.tasks",
        "--pid-file", "drama.pid"
    ])


@patch("os.execvp")
def test_rundramatiq_can_run_dramatiq_with_specified_log_file(execvp_mock):
    # Given an output buffer
    buff = StringIO()

    # When I call the rundramatiq command with --log-file
    call_command("rundramatiq", "--log-file", "drama.log", stdout=buff)

    # Then execvp should be called with the appropriate arguments
    cores = str(rundramatiq.CPU_COUNT)
    expected_exec_name = "dramatiq"
    expected_exec_path = os.path.join(
        os.path.dirname(sys.executable),
        expected_exec_name,
    )

    execvp_mock.assert_called_once_with(expected_exec_path, [
        expected_exec_name, "--path", ".", "--processes", cores, "--threads", cores,
        "--watch", ".",
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
        "tests.testapp.tasks",
        "--log-file", "drama.log"
    ])
