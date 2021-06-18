import time
import datetime

import dramatiq

from django_dramatiq.models import Task
from django_dramatiq.test import DramatiqTestCase
from django_dramatiq.forms import DramatiqLoadGraphForm


class TestDramatiqLoadGraph(DramatiqTestCase):

    def test_dramatiq_load_graph_form(self):
        # Given an actor defined in the test method
        @dramatiq.actor(max_retries=0)
        def do_work():
            time.sleep(0.05)

        # When I send a message 3 times
        for i in range(3):
            do_work.send()
            self.broker.join(do_work.queue_name)
            self.worker.join()

        # Then a 3 finished tasks should be stored to the database
        tasks = Task.tasks.all()
        self.assertEqual(3, tasks.count())

        # And form context for graph built for 2 items
        utcnow = datetime.datetime.utcnow()
        form = DramatiqLoadGraphForm(data=dict(
            start_date=utcnow - datetime.timedelta(minutes=1),
            end_date=utcnow + datetime.timedelta(minutes=1),
            time_interval=10,
            queue='',
            actor='',
            status=Task.STATUS_DONE
        ))
        self.assertTrue(form.is_valid())
        graph_data = form.get_graph_data()
        self.assertEqual({}, graph_data)
