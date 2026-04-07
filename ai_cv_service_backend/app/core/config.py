from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Smart Recruitment & HR Platform"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = Field(default="change-me", min_length=16)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    JWT_ALGORITHM: str = "HS256"

    AISTUDIO_API_KEY: str = ""
    AISTUDIO_MODEL: str = "gemini-1.5-flash"
    AISTUDIO_TIMEOUT_SECONDS: int = 25
    AI_DEFAULT_PASS_SCORE: float = 60.0

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_cv_service"
    REDIS_URL: str = "redis://localhost:6379/0"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/%2F"
    RABBITMQ_EXCHANGE: str = "recruitment.events"
    RABBITMQ_SCORING_REQUEST_ROUTING_KEY: str = "cv.scoring.request"
    RABBITMQ_SCORING_RESULT_ROUTING_KEY: str = "cv.scoring.result"
    RABBITMQ_SCORING_FAILED_ROUTING_KEY: str = "cv.scoring.failed"
    RABBITMQ_RESULT_QUEUE: str = "cv.scoring.result.queue"
    RABBITMQ_FAILED_QUEUE: str = "cv.scoring.failed.queue"

    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    STORAGE_PROVIDER: str = "local"
    UPLOAD_DIR: str = "uploads"
    AVATAR_DIR: str = "uploads/avatars"
    CV_DIR: str = "uploads/cvs"
    MAX_FILE_SIZE_MB: int = 10

    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = ""
    LINKEDIN_FRONTEND_CALLBACK_URI: str = "http://localhost:5173/oauth/linkedin/callback"
    LINKEDIN_OAUTH_SCOPE: str = "openid profile email"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    GOOGLE_FRONTEND_CALLBACK_URI: str = "http://localhost:5173/oauth/google/callback"
    GOOGLE_OAUTH_SCOPE: str = "openid email profile"
    GMAIL_SENDER_EMAIL: str = ""
    GMAIL_APP_PASSWORD: str = ""

    ENABLE_SOCIAL_AUTH: bool = True

    RATE_LIMIT_DEFAULT: str = "100/minute"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
