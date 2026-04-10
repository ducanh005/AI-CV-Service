import asyncio
import json
import logging
import time

import pika

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import setup_logging
from app.services.scoring_request_service import ScoringRequestService


logger = logging.getLogger(__name__)


class ScoringResultConsumer:
    def __init__(self) -> None:
        self._connection: pika.BlockingConnection | None = None
        self._channel: pika.adapters.blocking_connection.BlockingChannel | None = None
        self._event_loop = asyncio.new_event_loop()

    def run(self) -> None:
        setup_logging()
        while True:
            try:
                self._connect()
                logger.info("Scoring request consumer started")
                assert self._channel is not None
                self._channel.start_consuming()
            except KeyboardInterrupt:
                logger.info("Scoring request consumer stopped")
                break
            except Exception:
                logger.exception("Scoring request consumer crashed; retrying")
                time.sleep(3)
            finally:
                self._close()

        if not self._event_loop.is_closed():
            self._event_loop.close()

    def _run_async(self, coro):
        if self._event_loop.is_closed():
            self._event_loop = asyncio.new_event_loop()
        return self._event_loop.run_until_complete(coro)

    def _connect(self) -> None:
        params = pika.URLParameters(settings.RABBITMQ_URL)
        params.heartbeat = 60
        params.blocked_connection_timeout = 30

        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
        self._channel.exchange_declare(exchange=settings.RABBITMQ_EXCHANGE, exchange_type="topic", durable=True)

        self._channel.queue_declare(queue=settings.RABBITMQ_REQUEST_QUEUE, durable=True)
        self._channel.queue_bind(
            exchange=settings.RABBITMQ_EXCHANGE,
            queue=settings.RABBITMQ_REQUEST_QUEUE,
            routing_key=settings.RABBITMQ_SCORING_REQUEST_ROUTING_KEY,
        )

        self._channel.basic_qos(prefetch_count=10)
        self._channel.basic_consume(queue=settings.RABBITMQ_REQUEST_QUEUE, on_message_callback=self._on_request)

    def _close(self) -> None:
        if self._channel and self._channel.is_open:
            try:
                self._channel.close()
            except Exception:
                logger.exception("Failed to close channel")

        if self._connection and self._connection.is_open:
            try:
                self._connection.close()
            except Exception:
                logger.exception("Failed to close connection")

        self._channel = None
        self._connection = None

    def _on_request(self, ch, method, _properties, body: bytes) -> None:
        try:
            event = json.loads(body.decode("utf-8"))
            payload = event.get("payload", event)
            self._run_async(self._process_request(payload))
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            logger.exception("Failed to handle scoring request")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    async def _process_request(self, payload: dict) -> None:
        async with AsyncSessionLocal() as db:
            service = ScoringRequestService(db)
            await service.process_request(payload)


def main() -> None:
    ScoringResultConsumer().run()


if __name__ == "__main__":
    main()
