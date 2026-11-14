import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import AsyncIO

from app.config.settings import get_rabbitmq_settings


def configure_broker() -> RabbitmqBroker:
    url = get_rabbitmq_settings().url

    broker = RabbitmqBroker(url=url)
    broker.add_middleware(AsyncIO())

    dramatiq.set_broker(broker)

    return broker
