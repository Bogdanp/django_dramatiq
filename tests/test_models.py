import uuid
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
