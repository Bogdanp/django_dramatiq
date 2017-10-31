import pytest

from django_dramatiq import tasks
from dramatiq import Worker


@pytest.fixture(scope="session")
def broker():
    return tasks.broker


@pytest.fixture
def worker(broker):
    worker = Worker(broker, worker_timeout=100)
    worker.start()
    yield worker
    worker.stop()
