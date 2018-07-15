import dramatiq
import pytest
from dramatiq import Worker


@pytest.fixture(scope="session")
def broker():
    return dramatiq.get_broker()


@pytest.fixture
def worker(broker):
    worker = Worker(broker, worker_timeout=100)
    worker.start()
    yield worker
    worker.stop()
