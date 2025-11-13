from django.test import TransactionTestCase
from dramatiq import Worker, get_broker


class DramatiqTestCase(TransactionTestCase):
    def setUp(self):
        self.broker = get_broker()
        self.broker.flush_all()

        self.worker = Worker(self.broker, worker_timeout=100)
        self.worker.start()
        super().setUp()

    def tearDown(self):
        super().tearDown()
        self.worker.stop()
