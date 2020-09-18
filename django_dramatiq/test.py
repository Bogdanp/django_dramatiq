from django.test import TransactionTestCase, SimpleTestCase, override_settings
from dramatiq import Worker, get_broker, Actor
from dramatiq.brokers.stub import StubBroker

from .utils import actor


class DramatiqTestCase(TransactionTestCase):

    def _pre_setup(self):
        super()._pre_setup()

        self.broker = get_broker()
        self.broker.flush_all()

        self.worker = Worker(self.broker, worker_timeout=100)
        self.worker.start()

    def _post_teardown(self):
        self.worker.stop()

        super()._post_teardown()


class DramatiqActorTestCase(SimpleTestCase):

    class NewActor(Actor):
        pass

    def _get_task(self, **options):
        @actor(**options)
        def task():
            pass
        return task

    @override_settings(DRAMATIQ_TASK_DEFAULTS={'actor_name': 'new_actor_name',
                                               'actor_class': NewActor})
    def test_actor_defaults_actor_related(self):
        task = self._get_task()
        self.assertEqual(task.actor_name, 'new_actor_name')
        self.assertIsInstance(task, DramatiqActorTestCase.NewActor)

    @override_settings(DRAMATIQ_TASK_DEFAULTS={'queue_name': 'new_default'})
    def test_actor_defaults_queue_name(self):
        task = self._get_task()
        self.assertEqual(task.queue_name, 'new_default')

    @override_settings(DRAMATIQ_TASK_DEFAULTS={'priority': 5})
    def test_actor_defaults_priority(self):
        task = self._get_task()
        self.assertEqual(task.priority, 5)

    @override_settings(DRAMATIQ_TASK_DEFAULTS={'broker': StubBroker()})
    def test_actor_defaults_broker(self):
        task = self._get_task()
        self.assertIsInstance(task.broker, StubBroker)

    @override_settings(DRAMATIQ_TASK_DEFAULTS={'priority': 1338,
                                               'queue_name': 'new_default'})
    def test_actor_defaults_not_overwriting(self):
        task = self._get_task(priority=1337)
        self.assertEqual(task.priority, 1337)
        self.assertEqual(task.queue_name, 'new_default')
