import uuid
import logging
import dramatiq
from unittest import mock
from django_dramatiq.models import Task


def test_task_create_or_update_from_message(transactional_db, broker, worker):
    message = mock.Mock()
    message_id = uuid.uuid4()
    message.encode.return_value = b"{}"
    message.message_id = message_id

    Task.tasks.create_or_update_from_message(message)

    # Created it
    t = Task.tasks.get(pk=message.message_id)
    message.encode.assert_called_once_with()
    assert t.message_data == message.encode.return_value
    message.encode.reset_mock()
    message.encode.return_value = b'{"another_one", 12}'
    Task.tasks.create_or_update_from_message(message)

    # Updated it
    t.refresh_from_db()
    message.encode.assert_called_once_with()
    assert Task.tasks.count() == 1
    assert t.message_data == message.encode.return_value


def test_task_str_normal(transactional_db, broker, worker):
    """
    Test that __str__ returns the string representation of the underlying
    dramatiq message when the message data is valid
    """
    # task with valid dramatiq message
    message = dramatiq.Message(queue_name="default", actor_name="my_actor1", args=(), kwargs={}, options={})
    message_data = message.encode()
    task = Task.tasks.create(
        id=message.message_id, message_data=message_data, actor_name=message.actor_name, queue_name=message.queue_name
    )
    assert str(task) == str(message)


def test_task_str_failure(transactional_db, caplog, broker, worker):
    """
    Test that __str__ returns a fallback error message and logs an exception
    when the message data is corrupted
    """
    # task with invalid message data
    task = Task.tasks.create(
        id=uuid.uuid4(), message_data=b"invalid dramatiq message", actor_name="my_actor1", queue_name="default"
    )
    # when we convert the task to a string
    with caplog.at_level(logging.ERROR):
        result = str(task)
    # then it returns a fallback error message
    assert result.startswith("Failed to display Task:")
    # and an ERROR log message is recorded with exception info
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.levelname == "ERROR"
    assert f"Failed to display Task {task.id}" in record.message
    assert record.exc_info is not None
