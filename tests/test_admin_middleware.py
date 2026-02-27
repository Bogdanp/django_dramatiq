from threading import Event

import dramatiq
import pytest
from dramatiq import Middleware
from dramatiq.middleware import SkipMessage

from django_dramatiq.apps import get_string_sequence_from_settings
from django_dramatiq.models import Task


def test_admin_middleware_keeps_track_of_tasks(transactional_db, broker, worker):
    # Given an actor
    evt = Event()

    @dramatiq.actor
    def do_work():
        evt.set()

    # When I send it a delayed message
    do_work.send_with_options(delay=250)

    # Then a Task should be stored to the database
    task = Task.tasks.get()
    assert task
    assert task.status == Task.STATUS_DELAYED

    # When I join on the broker
    evt.wait()
    broker.join(do_work.queue_name, fail_fast=True)
    worker.join()

    # And reload the task
    task.refresh_from_db()

    # Then the Task's status should be updated
    assert task.status == Task.STATUS_DONE


@pytest.mark.skip(reason="flaky due to SQLite concurrency issues with select_for_update")
def test_admin_middleware_keeps_track_of_failed_tasks(transactional_db, broker, worker):
    # Given an actor that always fails
    @dramatiq.actor(max_retries=0)
    def do_work():
        raise RuntimeError("failed")

    # When I send it a message
    do_work.send()

    # And I join on the broker
    broker.join(do_work.queue_name)
    worker.join()

    # Then a failed Task should be stored to the database
    task = Task.tasks.get()
    assert task
    assert task.status == Task.STATUS_FAILED
    assert "RuntimeError" in task.message.options["traceback"]


def test_admin_middleware_keeps_track_of_skipped_tasks(transactional_db, broker, worker):
    # Given an actor that does nothing
    @dramatiq.actor(max_retries=0)
    def do_work():
        pass

    # And a middleware that skips all messages
    class Skipper(Middleware):
        def before_process_message(self, broker, message):
            raise SkipMessage()

    # When I enable the middleware
    broker.add_middleware(Skipper())

    # And I send the actor a message
    do_work.send()

    # And I join on the broker
    broker.join(do_work.queue_name)
    worker.join()

    # Then a skipped Task should be stored to the database
    task = Task.tasks.get()
    assert task
    assert task.status == Task.STATUS_SKIPPED


def test_tasks_allowlist_and_blocklist(transactional_db, broker, worker, monkeypatch):
    @dramatiq.actor
    def actor_lists_check1():
        pass

    @dramatiq.actor
    def actor_lists_check2():
        pass

    # BLOCKLIST and ALLOWLIST is None - default
    monkeypatch.setattr("django_dramatiq.models.TASKS_ALLOWLIST", None)
    monkeypatch.setattr("django_dramatiq.models.TASKS_BLOCKLIST", None)
    Task.tasks.all().delete()
    actor_lists_check1.send()
    broker.join(actor_lists_check1.queue_name)
    worker.join()
    actor_lists_check2.send()
    broker.join(actor_lists_check2.queue_name)
    worker.join()
    assert Task.tasks.all().count() == 2

    # ALLOWLIST set only
    Task.tasks.all().delete()
    monkeypatch.setattr("django_dramatiq.models.TASKS_ALLOWLIST", ["actor_lists_check1"])
    monkeypatch.setattr("django_dramatiq.models.TASKS_BLOCKLIST", None)
    actor_lists_check1.send()
    broker.join(actor_lists_check1.queue_name)
    worker.join()
    actor_lists_check2.send()
    broker.join(actor_lists_check2.queue_name)
    worker.join()
    assert Task.tasks.all().count() == 1
    assert Task.tasks.filter(actor_name="actor_lists_check1").count() == 1

    # BLOCKLIST set only
    Task.tasks.all().delete()
    monkeypatch.setattr("django_dramatiq.models.TASKS_ALLOWLIST", None)
    monkeypatch.setattr("django_dramatiq.models.TASKS_BLOCKLIST", ["actor_lists_check1"])
    actor_lists_check1.send()
    broker.join(actor_lists_check1.queue_name)
    worker.join()
    actor_lists_check2.send()
    broker.join(actor_lists_check2.queue_name)
    worker.join()
    assert Task.tasks.all().count() == 1
    assert Task.tasks.filter(actor_name="actor_lists_check2").count() == 1

    # BLOCKLIST and ALLOWLIST set
    Task.tasks.all().delete()
    monkeypatch.setattr("django_dramatiq.models.TASKS_ALLOWLIST", ["actor_lists_check1", "actor_lists_check3"])
    monkeypatch.setattr("django_dramatiq.models.TASKS_BLOCKLIST", ["actor_lists_check2", "actor_lists_check4"])
    actor_lists_check1.send()
    broker.join(actor_lists_check1.queue_name)
    worker.join()
    actor_lists_check2.send()
    broker.join(actor_lists_check2.queue_name)
    worker.join()
    assert Task.tasks.all().count() == 1
    assert Task.tasks.filter(actor_name="actor_lists_check1").count() == 1

    # get_string_sequence_from_settings
    assert get_string_sequence_from_settings("DJANGO_DRAMATIQ_TASKS_ALLOWLIST") is None
    assert get_string_sequence_from_settings("DJANGO_DRAMATIQ_TASKS_BLOCKLIST") is None
    with pytest.raises(ValueError):
        get_string_sequence_from_settings("_CHECK_GET_STRING_SEQUENCE_FROM_SETTINGS")
