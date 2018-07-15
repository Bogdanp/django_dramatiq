import uuid
from datetime import timedelta

import pytest
from django.utils.timezone import now

from django_dramatiq.models import Task
from django_dramatiq.tasks import delete_old_tasks


def test_can_delete_old_tasks(db):
    # Given a Task that was created more than a day ago
    task = Task(id=uuid.uuid4(), message_data=b"")
    task.save()

    # we have to set the created_at time after the initial save in
    # order to avoid it getting overwritten.
    task.created_at = now() - timedelta(days=2)
    task.save()

    # When I call the delete_old_tasks task
    delete_old_tasks()

    # Then my task should be deleted
    with pytest.raises(Task.DoesNotExist):
        task.refresh_from_db()
