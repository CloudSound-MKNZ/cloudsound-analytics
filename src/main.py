"""Analytics service main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cloudsound_shared.health import router as health_router
from cloudsound_shared.metrics import get_metrics
from fastapi.responses import Response
from cloudsound_shared.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from cloudsound_shared.middleware.correlation import CorrelationIDMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from cloudsound_shared.logging import configure_logging, get_logger
from cloudsound_shared.config.settings import app_settings

# Configure logging
configure_logging(log_level=app_settings.log_level, log_format=app_settings.log_format)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CloudSound Analytics Service",
    version=app_settings.app_version,
    description="Playback statistics and analytics service",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# Exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health_router)

# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("analytics_service_started", version=app_settings.app_version)
    
    # Start Kafka consumer in background
    import asyncio
    from .consumers.playback_consumer import get_consumer
    
    consumer = get_consumer()
    # Run consumer in background thread
    import threading
    consumer_thread = threading.Thread(target=consumer.start, daemon=True)
    consumer_thread.start()
    logger.info("playback_event_consumer_started")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("analytics_service_shutdown")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)

