import pytest

from django_dramatiq import tasks
from dramatiq import Worker


@pytest.fixture
def broker():
    yield tasks.broker
    tasks.broker.flush_all()


@pytest.fixture
def worker(broker):
    worker = Worker(broker, worker_timeout=100)
    worker.start()
    yield worker
    worker.stop()
