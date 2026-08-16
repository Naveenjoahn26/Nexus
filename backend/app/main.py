"""
NEXUS EDU — Main FastAPI Application.

Entry point for the backend. Wires up routers, exception handlers,
CORS middleware, and application lifecycle events.
"""

import time
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import (
    analysis,
    auth,
    chat,
    courses,
    documents,
    lecture,
    ppt,
    question_paper,
    summary,
    youtube,
)
from app.core.config import get_settings

from app.core.exceptions import APIException, NexusBaseError
from app.core.logger import telemetry_logger
import logging

logger = logging.getLogger(__name__)

import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context: initialises DB tables and pre-warms ML models.

    Both tasks run as background asyncio tasks so the health-check endpoint
    responds immediately while heavy I/O (DB schema, model download) completes
    in the background.
    """
    async def _init_db():
        try:
            from app.database.database import get_engine
            from app.database.base import Base
            import app.models  # Register all ORM models
            engine = get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables verified/created successfully.")
        except Exception as exc:
            logger.warning("Database table auto-creation skipped/failed: %s", exc)

    asyncio.create_task(_init_db())
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="NEXUS EDU Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Middlewares ──────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name}

@app.middleware("http")
async def add_request_context_and_log(request: Request, call_next: Any) -> Any:
    """Middleware to inject Request ID and log API latencies."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time

    response.headers["X-Request-ID"] = request_id
    
    # Log the request
    telemetry_logger.info(
        "API Request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url.path),
            "status_code": response.status_code,
            "latency_ms": round(process_time * 1000, 2),
        }
    )
    
    return response


# ── Exception Handlers ───────────────────────────────────────────

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom HTTP exceptions smoothly."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "metadata": {"request_id": getattr(request.state, "request_id", None)}
        },
    )

@app.exception_handler(NexusBaseError)
async def nexus_error_handler(request: Request, exc: NexusBaseError) -> JSONResponse:
    """Catch all internal Nexus errors and mask as 500 for safety."""
    logger.error("Internal Nexus Error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An internal system error occurred.",
            "metadata": {"request_id": getattr(request.state, "request_id", None)}
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions."""
    logger.error("Unhandled Exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal Server Error",
            "metadata": {"request_id": getattr(request.state, "request_id", None)}
        },
    )


# ── Routers ──────────────────────────────────────────────────────

app.include_router(auth.router, prefix="/api/v1")
app.include_router(courses.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(lecture.router, prefix="/api/v1")
app.include_router(question_paper.router, prefix="/api/v1")
app.include_router(ppt.router, prefix="/api/v1")
app.include_router(summary.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(youtube.router, prefix="/youtube")

