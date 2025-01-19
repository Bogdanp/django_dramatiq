import logging
import sys
import traceback

from django import db
from dramatiq.middleware import Middleware

logger = logging.getLogger(__name__)


class AdminMiddleware(Middleware):
    """This middleware keeps track of task executions.
    """

    def after_enqueue(self, broker, message, delay):
        from .models import Task

        logger.debug("Creating Task from message %r.", message.message_id)
        status = Task.STATUS_ENQUEUED
        if delay:
            status = Task.STATUS_DELAYED

        Task.tasks.create_or_update_from_message(
            message,
            status=status,
            actor_name=message.actor_name,
            queue_name=message.queue_name,
        )

    def before_process_message(self, broker, message):
        from .models import Task

        logger.debug("Updating Task from message %r.", message.message_id)
        Task.tasks.create_or_update_from_message(
            message,
            status=Task.STATUS_RUNNING,
            actor_name=message.actor_name,
            queue_name=message.queue_name,
        )

    def after_skip_message(self, broker, message):
        from .models import Task

        self.after_process_message(broker, message, status=Task.STATUS_SKIPPED)

    def after_process_message(self, broker, message, *, result=None, exception=None, status=None):
        from .models import Task

        if exception is not None:
            status = Task.STATUS_FAILED
            exc_type, exc_value, exc_traceback = sys.exc_info()
            formatted_exception = traceback.format_exception(
                exception,
                exc_value,
                exc_traceback,
                limit=30,
            )
            message.options["traceback"] = "".join(formatted_exception)
        elif status is None:
            status = Task.STATUS_DONE

        logger.debug("Updating Task from message %r.", message.message_id)
        Task.tasks.create_or_update_from_message(
            message,
            status=status,
            actor_name=message.actor_name,
            queue_name=message.queue_name,
        )


class DbConnectionsMiddleware(Middleware):
    """This middleware cleans up db connections on worker shutdown.
    """

    def _close_old_connections(self, *args, **kwargs):
        db.close_old_connections()

    before_process_message = _close_old_connections
    after_process_message = _close_old_connections

    def _close_connections(self, *args, **kwargs):
        db.connections.close_all()

    before_consumer_thread_shutdown = _close_connections
    before_worker_thread_shutdown = _close_connections
    before_worker_shutdown = _close_connections
