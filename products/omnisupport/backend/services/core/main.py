"""Core API Service - Main FastAPI application."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.config import get_settings
from shared.database import close_db, init_db
from shared.events.publisher import close_publisher

from services.core.api.v1 import router as api_v1_router
from services.core.websocket.router import router as ws_router
from services.channel.widget_api import router as widget_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    # Note: In production, use Alembic migrations instead
    # await init_db()
    yield
    # Shutdown
    await close_db()
    await close_publisher()


app = FastAPI(
    title="OmniSupport API",
    description="Омниканальная SaaS-платформа поддержки клиентов",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "core"}


# API routes
app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

# WebSocket endpoint
app.include_router(ws_router)

# Widget public API (no auth required)
app.include_router(widget_router, prefix="/widget/v1", tags=["Widget"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "services.core.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
