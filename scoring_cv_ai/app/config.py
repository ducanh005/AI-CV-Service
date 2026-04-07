from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "CV Scoring AI Service"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    SERVICE_PORT: int = 5005

    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672/%2F"
    RABBITMQ_EXCHANGE: str = "recruitment.events"
    RABBITMQ_REQUEST_ROUTING_KEY: str = "cv.scoring.request"
    RABBITMQ_RESULT_ROUTING_KEY: str = "cv.scoring.result"
    RABBITMQ_FAILED_ROUTING_KEY: str = "cv.scoring.failed"
    RABBITMQ_REQUEST_QUEUE: str = "cv.scoring.request.queue"
    RABBITMQ_PREFETCH_COUNT: int = 4
    RABBITMQ_RECONNECT_DELAY_SECONDS: int = 3
    ENABLE_RABBITMQ_CONSUMER: bool = True

    CV_BASE_DIR: str = "/app"
    CV_ALLOWED_ROOTS: str = "/app/uploads/cvs,/data/uploads/cvs"

    AISTUDIO_API_KEY: str = ""
    AISTUDIO_MODEL: str = "gemini-1.5-flash"
    AISTUDIO_TIMEOUT_SECONDS: int = 25

    @property
    def allowed_cv_roots(self) -> list[Path]:
        roots: list[Path] = []
        for raw in self.CV_ALLOWED_ROOTS.split(","):
            cleaned = raw.strip()
            if cleaned:
                roots.append(Path(cleaned).resolve())
        return roots


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
