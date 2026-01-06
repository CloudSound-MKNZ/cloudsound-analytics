"""Analytics service main application."""
from contextlib import asynccontextmanager
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from cloudsound_shared.health import router as health_router
from cloudsound_shared.metrics import get_metrics
from cloudsound_shared.middleware.error_handler import register_exception_handlers
from cloudsound_shared.middleware.correlation import CorrelationIDMiddleware
from cloudsound_shared.logging import configure_logging, get_logger
from cloudsound_shared.config.settings import app_settings

# Configure logging
configure_logging(log_level=app_settings.log_level, log_format=app_settings.log_format)
logger = get_logger(__name__)

# Global consumer thread
_consumer_thread = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with graceful shutdown."""
    global _consumer_thread
    
    # Startup
    logger.info("analytics_service_starting", version=app_settings.app_version)
    
    # Start Kafka consumer in background
    try:
        from .consumers.playback_consumer import get_consumer
        
        consumer = get_consumer()
        _consumer_thread = threading.Thread(target=consumer.start, daemon=True)
        _consumer_thread.start()
        logger.info("playback_event_consumer_started")
    except Exception as e:
        logger.warning("playback_consumer_init_failed", error=str(e))
    
    logger.info("analytics_service_started", version=app_settings.app_version)
    
    yield
    
    # Shutdown
    logger.info("analytics_service_shutting_down")
    
    # Consumer thread is daemon, will be stopped automatically
    
    logger.info("analytics_service_shutdown")


# Create FastAPI app
app = FastAPI(
    title="CloudSound Analytics Service",
    version=app_settings.app_version,
    description="Playback statistics and analytics service",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
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

# Register all exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(health_router)


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)

