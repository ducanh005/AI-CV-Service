import json
import logging
import uuid
from datetime import datetime, timezone

import pika


logger = logging.getLogger(__name__)


def publish_event(
    rabbitmq_url: str,
    event_type: str,
    payload: dict,
    exchange: str,
    routing_key: str,
    correlation_id: str | None = None,
) -> bool:
    message = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }

    try:
        params = pika.URLParameters(rabbitmq_url)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
                message_id=str(uuid.uuid4()),
                correlation_id=correlation_id,
            ),
        )
        connection.close()
        return True
    except Exception:
        logger.exception("Failed to publish RabbitMQ event", extra={"event_type": event_type})
        return False
