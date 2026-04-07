from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.services.rabbitmq_consumer import RabbitMQScoringConsumer
from app.utils.logging import setup_logging


consumer = RabbitMQScoringConsumer()


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()

    if settings.ENABLE_RABBITMQ_CONSUMER:
        consumer.start()

    yield

    consumer.stop()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "scoring-cv-ai",
        "consumer_enabled": settings.ENABLE_RABBITMQ_CONSUMER,
        "consumer_running": consumer.is_running,
    }
