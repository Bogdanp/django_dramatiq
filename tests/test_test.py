import dramatiq

from django_dramatiq.models import Task
from django_dramatiq.test import DramatiqTestCase


class TestDramatiqTestCase(DramatiqTestCase):

    def test_worker_consumes_tasks(self):
        # Given an actor defined in the test method
        @dramatiq.actor(max_retries=0)
        def do_work():
            self.assertEqual(1, Task.tasks.count())

        # When I send it a message
        do_work.send()

        # And I join on the broker
        self.broker.join(do_work.queue_name)
        self.worker.join()

        # Then a finished Task should be stored to the database
        task = Task.tasks.get()
        self.assertIsNotNone(task)
        self.assertEqual(task.status, Task.STATUS_DONE)
