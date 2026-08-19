import pytest
from dramatiq.worker import Worker
from testcontainers.community.rabbitmq import RabbitMqContainer

from app.config.broker import configure_broker


@pytest.fixture(scope="session")
def rabbitmq_container():
    with RabbitMqContainer("rabbitmq:4-management") as container:
        host = container.get_container_host_ip()
        port = int(container.get_exposed_port(5672))

        yield host, port


@pytest.fixture
def dramatiq_broker(monkeypatch, rabbitmq_container):
    host, port = rabbitmq_container

    monkeypatch.setenv("RABBITMQ_HOST", host)
    monkeypatch.setenv("RABBITMQ_PORT", str(port))

    return configure_broker()


@pytest.fixture
def dramatiq_worker(dramatiq_broker):
    from app.tasks.reports import generate_report

    generate_report.broker = dramatiq_broker
    dramatiq_broker.declare_actor(generate_report)

    worker = Worker(dramatiq_broker, worker_threads=1)

    worker.start()
    yield worker
    worker.stop()
