import logging
import sys
import traceback

from django import db
from dramatiq.middleware import Middleware

LOGGER = logging.getLogger("django_dramatiq.AdminMiddleware")


class AdminMiddleware(Middleware):
    """Tracks task execution lifecycle and maintains task status in database.

    This middleware integrates with django_dramatiq's Task model to provide
    visibility into task execution status through Django admin interface.
    It handles status transitions throughout the task lifecycle.
    """

    logger = LOGGER

    def after_enqueue(self, broker, message, delay):
        """Create or update task record after message is enqueued.

        Args:
            broker: Dramatiq broker instance
            message: Dramatiq message containing task data
            delay: Delay in milliseconds before task execution (None if immediate)

        Note:
            Sets task status to ENQUEUED for immediate tasks or DELAYED for
            delayed tasks. Uses concurrent-safe operations to prevent race
            conditions in multi-worker environments.
        """
        from .models import Task

        self.logger.debug("Creating Task from message %r.", message.message_id)

        status = Task.STATUS_ENQUEUED
        if delay:
            status = Task.STATUS_DELAYED

        try:
            Task.tasks.create_or_update_from_message_concurrently(
                message,
                status=status,
                actor_name=message.actor_name,
                queue_name=message.queue_name,
            )
        except Task.MessageStatusTransitionError as exc:
            self.logger.debug(
                "Task status transition ignored for message %r. Incorrect flow: source_status=%r, target_status=%r ",
                message.message_id,
                exc.src_status,
                exc.dst_status,
            )
        except Task.ConcurrentlyError:
            self.logger.debug(
                "Task status transition ignored for message %r. ConcurrentlyError: %r ",
            )

    def before_process_message(self, broker, message):
        """Update task status to RUNNING before worker begins processing.

        Args:
            broker: Dramatiq broker instance
            message: Dramatiq message being processed

        Note:
            Called immediately before worker starts executing the task.
            Updates the task record to indicate active processing.
        """
        from .models import Task

        self.logger.debug("Updating Task from message %r.", message.message_id)
        Task.tasks.create_or_update_from_message(
            message,
            status=Task.STATUS_RUNNING,
            actor_name=message.actor_name,
            queue_name=message.queue_name,
        )

    def after_skip_message(self, broker, message):
        """Mark task as skipped when message is not processed.

        Args:
            broker: Dramatiq broker instance
            message: Dramatiq message that was skipped

        Note:
            Called when a message is skipped due to middleware rules
            or other conditions that prevent processing.
        """
        from .models import Task

        self.after_process_message(broker, message, status=Task.STATUS_SKIPPED)

    def after_process_message(
        self, broker, message, *, result=None, exception=None, status=None
    ):
        """Update task status after processing completion or failure.

        Args:
            broker: Dramatiq broker instance
            message: Dramatiq message that was processed
            result: Task execution result (if successful)
            exception: Exception that occurred during processing (if failed)
            status: Explicit status override (optional)

        Note:
            Sets final task status based on execution outcome:
            - STATUS_FAILED if exception occurred (captures traceback)
            - STATUS_DONE if completed successfully
            - Custom status if explicitly provided

            Clears traceback for successful executions to maintain
            clean admin interface display.
        """
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
        else:
            # No exception now, clear traceback to be consistent in admin panel view
            message.options["traceback"] = ""

            if status is None:
                status = Task.STATUS_DONE

        self.logger.debug("Updating Task from message %r.", message.message_id)
        Task.tasks.create_or_update_from_message(
            message,
            status=status,
            actor_name=message.actor_name,
            queue_name=message.queue_name,
        )


class DbConnectionsMiddleware(Middleware):
    """Manages database connections lifecycle in dramatiq workers.

    Ensures proper cleanup of database connections to prevent connection
    leaks and resource exhaustion in long-running worker processes.
    Handles both connection refreshing during processing and complete
    cleanup during worker shutdown.
    """

    def _close_old_connections(self, *args, **kwargs):
        """Close database connections that have been idle too long.

        Args:
            *args: Unused positional arguments from middleware interface
            **kwargs: Unused keyword arguments from middleware interface

        Note:
            Called before and after message processing to ensure fresh
            database connections. Prevents issues with stale connections
            in long-running worker processes.
        """
        db.close_old_connections()

    before_process_message = _close_old_connections
    after_process_message = _close_old_connections

    def _close_connections(self, *args, **kwargs):
        """Close all active database connections.

        Args:
            *args: Unused positional arguments from middleware interface
            **kwargs: Unused keyword arguments from middleware interface

        Note:
            Called during various worker shutdown phases to ensure complete
            cleanup of database resources. Prevents connection leaks when
            workers are terminated or restarted.
        """
        db.connections.close_all()

    before_consumer_thread_shutdown = _close_connections
    before_worker_thread_shutdown = _close_connections
    before_worker_shutdown = _close_connections
