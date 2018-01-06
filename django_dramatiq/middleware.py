import logging

from django import db
from dramatiq.middleware import Middleware

from .models import Task

LOGGER = logging.getLogger("django_dramatiq.AdminMiddleware")


class AdminMiddleware(Middleware):
    """This middleware keeps track of task executions.
    """

    def after_enqueue(self, broker, message, delay):
        LOGGER.debug("Creating Task from message %r.", message.message_id)
        status = Task.STATUS_ENQUEUED
        if delay:
            status = Task.STATUS_DELAYED

        Task.tasks.create_or_update_from_message(message, status=status)

    def before_process_message(self, broker, message):
        LOGGER.debug("Updating Task from message %r.", message.message_id)
        Task.tasks.create_or_update_from_message(message, status=Task.STATUS_RUNNING)

    def after_process_message(self, broker, message, *, result=None, exception=None):
        status = Task.STATUS_DONE
        if exception is not None:
            status = Task.STATUS_FAILED

        LOGGER.debug("Updating Task from message %r.", message.message_id)
        Task.tasks.create_or_update_from_message(message, status=status)


class DbConnectionsMiddleware(Middleware):
    """This middleware cleans up db connections on worker shutdown.
    """

    def _close_connections(self, *args, **kwargs):
        db.connections.close_all()

    before_consumer_thread_shutdown = _close_connections
    before_worker_thread_shutdown = _close_connections
    before_worker_shutdown = _close_connections
