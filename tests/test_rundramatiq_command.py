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
        "tests.testapp1.tasks",
        "tests.testapp2.tasks",
        "tests.testapp3.tasks.other_tasks",
        "tests.testapp3.tasks.tasks",
        "tests.testapp3.tasks.utils",
        "tests.testapp3.tasks.utils.not_a_task",
    ]


@patch("os.execvp")
def test_rundramatiq_can_run_dramatiq(execvp_mock):
    # Given an output buffer
    buff = StringIO()

    # When I call the rundramatiq command
    call_command("rundramatiq", stdout=buff)

    # Then stdout should contain a message about discovered task modules
    assert "Discovered tasks module: 'tests.testapp1.tasks'" in buff.getvalue()
    assert "Discovered tasks module: 'tests.testapp2.tasks'" in buff.getvalue()
    assert "Discovered tasks module: 'tests.testapp3.tasks.tasks'" in buff.getvalue()
    assert "Discovered tasks module: 'tests.testapp3.tasks.other_tasks'" in buff.getvalue()

    # And execvp should be called with the appropriate arguments
    cores = str(rundramatiq.CPU_COUNT)
    expected_exec_name = "dramatiq"
    expected_exec_path = os.path.join(
        os.path.dirname(sys.executable),
        expected_exec_name,
    )

    execvp_mock.assert_called_once_with(expected_exec_path, [
        expected_exec_name, "--path", ".", "--processes", cores, "--threads", cores,
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
        "tests.testapp1.tasks",
        "tests.testapp2.tasks",
        "tests.testapp3.tasks.other_tasks",
        "tests.testapp3.tasks.tasks",
        "tests.testapp3.tasks.utils",
        "tests.testapp3.tasks.utils.not_a_task",
    ])


@patch("os.execvp")
def test_rundramatiq_can_run_dramatiq_reload(execvp_mock):
    # Given an output buffer
    buff = StringIO()

    # When I call the rundramatiq command with --reload-use-polling
    call_command("rundramatiq", "--reload", stdout=buff)

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
        "tests.testapp1.tasks",
        "tests.testapp2.tasks",
        "tests.testapp3.tasks.other_tasks",
        "tests.testapp3.tasks.tasks",
        "tests.testapp3.tasks.utils",
        "tests.testapp3.tasks.utils.not_a_task",
    ])


@patch("os.execvp")
def test_rundramatiq_can_run_dramatiq_with_polling(execvp_mock):
    # Given an output buffer
    buff = StringIO()

    # When I call the rundramatiq command with --reload-use-polling
    call_command("rundramatiq", "--reload", "--reload-use-polling", stdout=buff)

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
        "tests.testapp1.tasks",
        "tests.testapp2.tasks",
        "tests.testapp3.tasks.other_tasks",
        "tests.testapp3.tasks.tasks",
        "tests.testapp3.tasks.utils",
        "tests.testapp3.tasks.utils.not_a_task",
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
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
        "tests.testapp1.tasks",
        "tests.testapp2.tasks",
        "tests.testapp3.tasks.other_tasks",
        "tests.testapp3.tasks.tasks",
        "tests.testapp3.tasks.utils",
        "tests.testapp3.tasks.utils.not_a_task",
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
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
        "tests.testapp1.tasks",
        "tests.testapp2.tasks",
        "tests.testapp3.tasks.other_tasks",
        "tests.testapp3.tasks.tasks",
        "tests.testapp3.tasks.utils",
        "tests.testapp3.tasks.utils.not_a_task",
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
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
        "tests.testapp1.tasks",
        "tests.testapp2.tasks",
        "tests.testapp3.tasks.other_tasks",
        "tests.testapp3.tasks.tasks",
        "tests.testapp3.tasks.utils",
        "tests.testapp3.tasks.utils.not_a_task",
        "--log-file", "drama.log"
    ])


@patch("os.execvp")
def test_rundramatiq_can_ignore_modules(execvp_mock, settings):
    # Given an output buffer
    buff = StringIO()

    # And 'tests.testapp2.tasks' in DRAMATIQ_IGNORED_MODULES
    # And 'tests.testapp3.tasks.other_tasks' in DRAMATIQ_IGNORED_MODULES
    settings.DRAMATIQ_IGNORED_MODULES = (
        "tests.testapp2.tasks",
        "tests.testapp3.tasks.other_tasks",
        "tests.testapp3.tasks.utils.*",
    )

    # When I call the rundramatiq command
    call_command("rundramatiq", stdout=buff)

    # Then stdout should contain a message about ignored task modules
    assert "Discovered tasks module: 'tests.testapp1.tasks'" in buff.getvalue()
    assert "Discovered tasks module: 'tests.testapp3.tasks.tasks'" in buff.getvalue()
    assert "Discovered tasks module: 'tests.testapp3.tasks.utils'" in buff.getvalue()
    assert "Ignored tasks module: 'tests.testapp2.tasks'" in buff.getvalue()
    assert "Ignored tasks module: 'tests.testapp3.tasks.other_tasks'" in buff.getvalue()
    assert "Ignored tasks module: 'tests.testapp3.tasks.utils.not_a_task'" in buff.getvalue()

    # And execvp should be called with the appropriate arguments
    cores = str(rundramatiq.CPU_COUNT)
    expected_exec_name = "dramatiq"
    expected_exec_path = os.path.join(
        os.path.dirname(sys.executable),
        expected_exec_name,
    )

    execvp_mock.assert_called_once_with(expected_exec_path, [
        expected_exec_name, "--path", ".", "--processes", cores, "--threads", cores,
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
        "tests.testapp1.tasks",
        "tests.testapp3.tasks.tasks",
        "tests.testapp3.tasks.utils",
    ])


@patch("os.execvp")
def test_rundramatiq_can_fork(execvp_mock, settings):
    # Given an output buffer
    buff = StringIO()

    # When I call the rundramatiq command with --log-file
    call_command("rundramatiq", "--fork-function", "a", "--fork-function", "b", stdout=buff)

    # Then execvp should be called with the appropriate arguments
    cores = str(rundramatiq.CPU_COUNT)
    expected_exec_name = "dramatiq"
    expected_exec_path = os.path.join(
        os.path.dirname(sys.executable),
        expected_exec_name,
    )

    execvp_mock.assert_called_once_with(expected_exec_path, [
        expected_exec_name, "--path", ".", "--processes", cores, "--threads", cores,
        "--fork-function", "a",
        "--fork-function", "b",
        "django_dramatiq.setup",
        "django_dramatiq.tasks",
        "tests.testapp1.tasks",
        "tests.testapp2.tasks",
        "tests.testapp3.tasks.other_tasks",
        "tests.testapp3.tasks.tasks",
        "tests.testapp3.tasks.utils",
        "tests.testapp3.tasks.utils.not_a_task",
    ])
