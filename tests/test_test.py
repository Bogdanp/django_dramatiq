import dramatiq
import pytest

from django_dramatiq.models import Task


class TestDramatiqTestCase:

    @pytest.mark.django_db(transaction=True)
    def test_worker_consumes_tasks(self, broker, worker):
        # Given an actor defined in the test method
        @dramatiq.actor(max_retries=0)
        def do_work():
            assert Task.tasks.count() == 1

        # When I send it a message
        do_work.send()

        # And I join on the broker
        broker.join(do_work.queue_name)
        worker.join()

        # Then a finished Task should be stored to the database
        task = Task.tasks.get()
        assert task
        assert task.status == Task.STATUS_DONE
