from datetime import timedelta

from django.db import models, utils
from django.utils.functional import cached_property
from django.utils.timezone import now
from dramatiq import Message

from .apps import DjangoDramatiqConfig

#: The database label to use when storing task metadata.
DATABASE_LABEL = DjangoDramatiqConfig.tasks_database()


class TaskManager(models.Manager):
    def create_or_update_from_message(self, message, **extra_fields):
        try:
            return self.using(DATABASE_LABEL).create(
                id=message.message_id,
                message_data=message.encode(),
                **extra_fields,
            )

        except (utils.OperationalError, utils.IntegrityError):
            task = self.using(DATABASE_LABEL).get(id=message.message_id)
            task.message_data = message.encode()
            for name, value in extra_fields.items():
                setattr(task, name, value)

            task.save()
            return task

    def delete_old_tasks(self, max_task_age):
        self.using(DATABASE_LABEL).filter(
            created_at__lte=now() - timedelta(seconds=max_task_age)
        ).delete()


class Task(models.Model):
    STATUS_ENQUEUED = "enqueued"
    STATUS_DELAYED = "delayed"
    STATUS_RUNNING = "running"
    STATUS_FAILED = "failed"
    STATUS_DONE = "done"
    STATUSES = [
        (STATUS_ENQUEUED, "Enqueued"),
        (STATUS_DELAYED, "Delayed"),
        (STATUS_RUNNING, "Running"),
        (STATUS_FAILED, "Failed"),
        (STATUS_DONE, "Done"),
    ]

    id = models.UUIDField(primary_key=True, editable=False)
    status = models.CharField(max_length=8, choices=STATUSES, default=STATUS_ENQUEUED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    message_data = models.BinaryField()

    tasks = TaskManager()

    class Meta:
        ordering = ["-updated_at"]

    @cached_property
    def message(self):
        return Message.decode(bytes(self.message_data))

    def __str__(self):
        return str(self.message)
