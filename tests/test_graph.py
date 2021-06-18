import time
import json
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

        # And form context for graph built for 3 items
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
        self.assertIs(str, type(graph_data['graph_title']))
        self.assertEqual('225', graph_data['graph_height'])
        self.assertEqual(False, graph_data['empty_qs'])
        self.assertEqual(["do_work"], json.loads(graph_data['categories']))
        self.assertEqual(13, len(json.loads(graph_data['dates'])))
        working_actors_count = json.loads(graph_data['working_actors_count'])
        self.assertEqual(13, len(working_actors_count[0]))
        self.assertEqual(3, sum(i for i in working_actors_count[0] if i))
