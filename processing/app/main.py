from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import time
from contextlib import asynccontextmanager

from .api.endpoints import router as api_router
from .config.settings import API_PREFIX, DEBUG
from .config.logging_config import setup_logging

from .config import settings

class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status (online/offline)")
    service: str = Field(..., description="Name of the service")
    version: Optional[str] = Field(None, description="API version")
    uptime: Optional[str] = Field(None, description="Service uptime")

# Setup logging
logger = setup_logging()

# Track startup time for uptime calculation
startup_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events, replacing @app.on_event decorators.
    https://fastapi.tiangolo.com/advanced/events/#lifespan
    """
    global startup_time
    # Startup code (before the yield)
    startup_time = time.time()
    logger.info(f"{app.title} is starting up")
    
    # Log all configuration variables
    logger.info("Configuration settings:")
    for setting_name in dir(settings):
        # Escludiamo metodi interni e importazioni
        if not setting_name.startswith('__') and not callable(getattr(settings, setting_name)):
            setting_value = getattr(settings, setting_name)
            logger.info(f"    {setting_name} = {setting_value}")
    
    yield  # Application execution happens here
    
    # Shutdown code (after the yield)
    logger.info(f"{app.title} is shutting down")

# Create FastAPI app with lifespan context manager
app = FastAPI(
    title="Wind and Fuel Moisture service API",
    description="API for running Wind and Fuel Moisture processing tasks",
    version="1.0.0",
    debug=DEBUG,
    lifespan=lifespan  # Use the lifespan context manager
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=API_PREFIX)

@app.get("/", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    This endpoint is used to verify the health and availability of the service API.
    
    Returns:
        HealthCheckResponse: A JSON response containing the status and service information.
    """
    logger.info("Health check endpoint called")
    uptime_seconds = int(time.time() - startup_time)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    
    return HealthCheckResponse(
        status="online",
        service=app.title,
        version=app.version,
        uptime=uptime_str
    )
