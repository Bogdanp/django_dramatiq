from django.test import TransactionTestCase, SimpleTestCase, override_settings
from dramatiq import Worker, get_broker, Actor, Broker
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

    @override_settings(DRAMATIQ_TASK_DEFAULT_ACTOR_CLASS=NewActor)
    def test_actor_default_actor_class(self):
        task = self._get_task()
        self.assertIsInstance(task, DramatiqActorTestCase.NewActor)

    @override_settings(DRAMATIQ_TASK_DEFAULT_ACTOR_NAME='new_actor_name')
    def test_actor_default_actor_name(self):
        task = self._get_task()
        self.assertIs(task.actor_name, 'new_actor_name')

    @override_settings(DRAMATIQ_TASK_DEFAULT_QUEUE_NAME='new_default')
    def test_actor_default_queue_name(self):
        task = self._get_task()
        self.assertIs(task.queue_name, 'new_default')

    @override_settings(DRAMATIQ_TASK_DEFAULT_PRIORITY=5)
    def test_actor_default_priority(self):
        task = self._get_task()
        self.assertIs(task.priority, 5)

    @override_settings(DRAMATIQ_TASK_DEFAULT_BROKER=StubBroker())
    def test_actor_default_broker(self):
        task = self._get_task()
        self.assertIsInstance(task.broker, StubBroker)

    @override_settings(DRAMATIQ_TASK_DEFAULT_OPTIONS={'priority': 1338, 'queue_name': 'new_default'})
    def test_actor_default_options(self):
        task = self._get_task(priority=1337)
        self.assertIs(task.priority, 1337)
        self.assertIs(task.queue_name, 'new_default')
