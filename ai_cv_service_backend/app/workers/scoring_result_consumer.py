import asyncio
import json
import logging
import time

import pika

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import setup_logging
from app.services.ai_service import AICVScoringService
from app.services.async_scoring_service import AsyncScoringService
from app.services.notification_service import NotificationService


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
                logger.info("Scoring result consumer started")
                assert self._channel is not None
                self._channel.start_consuming()
            except KeyboardInterrupt:
                logger.info("Scoring result consumer stopped")
                break
            except Exception:
                logger.exception("Scoring result consumer crashed; retrying")
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

        self._channel.queue_declare(queue=settings.RABBITMQ_RESULT_QUEUE, durable=True)
        self._channel.queue_bind(
            exchange=settings.RABBITMQ_EXCHANGE,
            queue=settings.RABBITMQ_RESULT_QUEUE,
            routing_key=settings.RABBITMQ_SCORING_RESULT_ROUTING_KEY,
        )

        self._channel.queue_declare(queue=settings.RABBITMQ_FAILED_QUEUE, durable=True)
        self._channel.queue_bind(
            exchange=settings.RABBITMQ_EXCHANGE,
            queue=settings.RABBITMQ_FAILED_QUEUE,
            routing_key=settings.RABBITMQ_SCORING_FAILED_ROUTING_KEY,
        )

        self._channel.basic_qos(prefetch_count=10)
        self._channel.basic_consume(queue=settings.RABBITMQ_RESULT_QUEUE, on_message_callback=self._on_result)
        self._channel.basic_consume(queue=settings.RABBITMQ_FAILED_QUEUE, on_message_callback=self._on_failed)

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

    def _on_result(self, ch, method, _properties, body: bytes) -> None:
        try:
            event = json.loads(body.decode("utf-8"))
            payload = event.get("payload", event)
            self._run_async(self._process_result(payload))
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            logger.exception("Failed to handle scoring result")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _on_failed(self, ch, method, _properties, body: bytes) -> None:
        try:
            event = json.loads(body.decode("utf-8"))
            payload = event.get("payload", event)
            self._run_async(self._process_failed(payload))
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            logger.exception("Failed to handle scoring failure")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    async def _process_result(self, payload: dict) -> None:
        request_id = str(payload.get("request_id", "")).strip()
        if not request_id:
            logger.warning("Result payload missing request_id")
            return

        score = float(payload.get("score", 0.0))
        reasoning = str(payload.get("reasoning", ""))
        provider = str(payload.get("provider", "unknown"))

        async with AsyncSessionLocal() as db:
            service = AsyncScoringService(db)
            item = await service.record_result(
                request_id=request_id,
                score=score,
                reasoning=reasoning,
                provider=provider,
            )
            if not item:
                logger.warning("No scoring item found for request_id=%s", request_id)
                return

            ai_service = AICVScoringService(db)
            await ai_service.upsert_application_score(
                item.application_id,
                score,
                reasoning,
                min_score=item.scoring_job.min_score,
            )

            if item.scoring_job.notify_candidates and item.application and item.application.candidate and item.application.job:
                passed = score >= item.scoring_job.min_score
                NotificationService.send_screening_result(
                    email=item.application.candidate.email,
                    job_title=item.application.job.title,
                    passed=passed,
                    score=score,
                    threshold=item.scoring_job.min_score,
                )

    async def _process_failed(self, payload: dict) -> None:
        request_id = str(payload.get("request_id", "")).strip()
        if not request_id:
            logger.warning("Failed payload missing request_id")
            return

        error_message = str(payload.get("error", "Unknown scoring error"))

        async with AsyncSessionLocal() as db:
            service = AsyncScoringService(db)
            item = await service.record_failed(request_id=request_id, error_message=error_message)
            if not item:
                logger.warning("No scoring item found for request_id=%s", request_id)


def main() -> None:
    ScoringResultConsumer().run()


if __name__ == "__main__":
    main()
