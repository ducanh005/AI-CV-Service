import json
import logging
import threading
import uuid
from datetime import datetime, timezone

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from app.config import settings
from app.schemas import ScoringFailedPayload, ScoringRequestPayload, ScoringResultPayload
from app.services.cv_parser import extract_cv_text
from app.services.scoring_service import ScoringService


logger = logging.getLogger(__name__)


class RabbitMQScoringConsumer:
    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None
        self._scoring = ScoringService()

    @property
    def is_running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="scoring-rabbitmq-consumer")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

        if self._connection and self._connection.is_open and self._channel and self._channel.is_open:
            try:
                self._connection.add_callback_threadsafe(self._channel.stop_consuming)
            except Exception:
                logger.exception("Failed to stop RabbitMQ consumer gracefully")

        if self._thread:
            self._thread.join(timeout=8)

        self._close_connection()
        self._running = False

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._connect()
                self._running = True
                logger.info("RabbitMQ scoring consumer started")
                assert self._channel is not None
                self._channel.start_consuming()
            except Exception:
                logger.exception("RabbitMQ consumer loop failed")
            finally:
                self._running = False
                self._close_connection()

            if self._stop_event.is_set():
                break

            self._stop_event.wait(settings.RABBITMQ_RECONNECT_DELAY_SECONDS)

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
            routing_key=settings.RABBITMQ_REQUEST_ROUTING_KEY,
        )
        self._channel.basic_qos(prefetch_count=settings.RABBITMQ_PREFETCH_COUNT)
        self._channel.basic_consume(queue=settings.RABBITMQ_REQUEST_QUEUE, on_message_callback=self._on_message)

    def _close_connection(self) -> None:
        if self._channel and self._channel.is_open:
            try:
                self._channel.close()
            except Exception:
                logger.exception("Error closing RabbitMQ channel")

        if self._connection and self._connection.is_open:
            try:
                self._connection.close()
            except Exception:
                logger.exception("Error closing RabbitMQ connection")

        self._channel = None
        self._connection = None

    def _on_message(
        self,
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ) -> None:
        correlation_id = properties.correlation_id if properties else None

        try:
            decoded = json.loads(body.decode("utf-8"))
            payload = decoded.get("payload", decoded)
            request = ScoringRequestPayload.model_validate(payload)

            cv_text = extract_cv_text(request.cv_file_path)
            score, reasoning, provider = self._scoring.score(cv_text, request.job_description, request.criteria)

            result_payload = ScoringResultPayload(
                request_id=request.request_id,
                scoring_job_id=request.scoring_job_id,
                application_id=request.application_id,
                job_id=request.job_id,
                score=score,
                reasoning=reasoning,
                provider=provider,
                processed_at=datetime.now(timezone.utc),
            )

            published = self._publish_event(
                channel=ch,
                event_type="cv.scoring.result",
                routing_key=settings.RABBITMQ_RESULT_ROUTING_KEY,
                payload=result_payload.model_dump(mode="json"),
                correlation_id=correlation_id or request.request_id,
            )
            if published:
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        except Exception as exc:
            logger.exception("Failed to process scoring request")
            failed_payload = self._build_failed_payload(body=body, error=str(exc))
            published = self._publish_event(
                channel=ch,
                event_type="cv.scoring.failed",
                routing_key=settings.RABBITMQ_FAILED_ROUTING_KEY,
                payload=failed_payload,
                correlation_id=correlation_id,
            )
            if published:
                ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def _build_failed_payload(self, body: bytes, error: str) -> dict:
        try:
            decoded = json.loads(body.decode("utf-8"))
            payload = decoded.get("payload", decoded)
            request = ScoringRequestPayload.model_validate(payload)
            failed = ScoringFailedPayload(
                request_id=request.request_id,
                scoring_job_id=request.scoring_job_id,
                application_id=request.application_id,
                job_id=request.job_id,
                error=error,
                processed_at=datetime.now(timezone.utc),
            )
            return failed.model_dump(mode="json")
        except Exception:
            return {
                "request_id": "unknown",
                "scoring_job_id": "unknown",
                "application_id": -1,
                "job_id": -1,
                "error": error,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            }

    def _publish_event(
        self,
        channel: BlockingChannel,
        event_type: str,
        routing_key: str,
        payload: dict,
        correlation_id: str | None,
    ) -> bool:
        envelope = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }

        try:
            channel.basic_publish(
                exchange=settings.RABBITMQ_EXCHANGE,
                routing_key=routing_key,
                body=json.dumps(envelope),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                    message_id=str(uuid.uuid4()),
                    correlation_id=correlation_id,
                ),
            )
            return True
        except Exception:
            logger.exception("Failed to publish RabbitMQ event", extra={"event_type": event_type})
            return False
