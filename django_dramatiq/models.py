import logging
from datetime import timedelta

from django.db import models, transaction
from django.utils.functional import cached_property
from django.utils.timezone import now
from dramatiq import Message

from .apps import DjangoDramatiqConfig

#: The database label to use when storing task metadata.
DATABASE_LABEL = DjangoDramatiqConfig.tasks_database()


class MessageStatusTransitionError(Exception):
    def __init__(self, msg, src_status, dst_status):
        self.src_status = src_status
        self.dst_status = dst_status
        super().__init__("%s: src=%s dst=%s" % (msg, src_status, dst_status))


class ConcurrentlyError(Exception):
    pass


class TaskManager(models.Manager):
    logger = logging.getLogger("django_dramatiq.TaskManager")

    @cached_property
    def transitions(self):
        # target_status -> [source_status, ...]
        transitions = {
            Task.STATUS_ENQUEUED: [  # Task has been enqueued for processing
                None,  # Task didn't exist, created new one
                Task.STATUS_DELAYED,  # Moved from DELAYED queue
            ],
            Task.STATUS_RUNNING: [  # Worker took the task for execution
                Task.STATUS_ENQUEUED,
                Task.STATUS_DELAYED,
            ],
            Task.STATUS_FAILED: [  # Task completed with error (e.g. Exception)
                Task.STATUS_RUNNING,
            ],
            Task.STATUS_DELAYED: [  # Task is delayed
                # Task can be delayed from any final status
                Task.STATUS_FAILED,
                Task.STATUS_SKIPPED,
                Task.STATUS_DONE,
            ],
        }
        return transitions

    def create_or_update_from_message(self, message, **extra_fields):
        task, _ = self.using(DATABASE_LABEL).update_or_create(
            id=message.message_id,
            defaults={
                "message_data": message.encode(),
                **extra_fields,
            }
        )
        return task

    def create_or_update_from_message_concurrently(self, message, status, **extra_fields):
        """Create or Update Task from given message and status.
        But, ensure Task.status flow will be correct.

        :raises MessageStatusTransitionError: you cannot transit

        """
        data = {
            'message_data': message.encode(),
            'status': status,
        }
        data.update(extra_fields)

        target_status = status

        with transaction.atomic(using=DATABASE_LABEL):
            obj, created = self.get_or_create(
                id=message.message_id,
                defaults=data,
            )
            if created:
                return

            source_status = obj.status
            status_changed = target_status != source_status or False

            if (
                status_changed
                and source_status not in self.transitions[target_status]
            ):
                raise MessageStatusTransitionError(
                    "Incorrect task transition flow",
                    src_status=source_status,
                    dst_status=target_status,
                )

            if status_changed:
                self.logger.debug(
                    'Updating Task status for message %r: %s -> %s',
                    message.message_id,
                    source_status,
                    target_status,
                )

            updated = self.filter(
                id=message.message_id,
                status=source_status,  # re-check status instead select for update
            ).update(**data)

            if not updated:
                raise ConcurrentlyError(
                    'Message deleted or status changed'
                )

    def delete_old_tasks(self, max_task_age):
        self.using(DATABASE_LABEL).filter(
            created_at__lte=now() - timedelta(seconds=max_task_age)
        ).delete()


class Task(models.Model):
    ConcurrentlyError = ConcurrentlyError
    MessageStatusTransitionError = MessageStatusTransitionError

    STATUS_ENQUEUED = "enqueued"
    STATUS_DELAYED = "delayed"
    STATUS_RUNNING = "running"
    STATUS_FAILED = "failed"
    STATUS_DONE = "done"
    STATUS_SKIPPED = "skipped"
    STATUSES = [
        (STATUS_ENQUEUED, "Enqueued"),
        (STATUS_DELAYED, "Delayed"),
        (STATUS_RUNNING, "Running"),
        (STATUS_FAILED, "Failed"),
        (STATUS_DONE, "Done"),
        (STATUS_SKIPPED, "Skipped"),
    ]

    id = models.UUIDField(primary_key=True, editable=False)
    status = models.CharField(max_length=8, choices=STATUSES, default=STATUS_ENQUEUED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    message_data = models.BinaryField()

    actor_name = models.CharField(max_length=300, null=True)
    queue_name = models.CharField(max_length=100, null=True)

    tasks = TaskManager()

    class Meta:
        ordering = ["-updated_at"]

    @cached_property
    def message(self):
        return Message.decode(bytes(self.message_data))

    def __str__(self):
        return str(self.message)
