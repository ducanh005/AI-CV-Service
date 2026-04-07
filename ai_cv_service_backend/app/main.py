from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from slowapi import _rate_limit_exceeded_handler

from app.api.router import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.exceptions import register_exception_handlers
from app.core.limiter import limiter
from app.core.logging import setup_logging
from app.models import *  # noqa: F401,F403
from app.services.bootstrap_service import ensure_user_profile_columns, seed_default_roles


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        await ensure_user_profile_columns(db)
        await seed_default_roles(db)

    yield


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    """Wrapper for rate limit exception handler."""
    return _rate_limit_exceeded_handler(request, exc)  # type: ignore[arg-type]


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

uploads_path = Path(settings.UPLOAD_DIR)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
