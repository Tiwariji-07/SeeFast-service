"""
FastAPI Application Entry Point
===============================

Initializes the app with ChromaDB (Swagger endpoints) and Redis on startup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    
    On startup:
    - Initialize ChromaDB with Swagger endpoints
    - Initialize Redis connection
    """
    # STARTUP
    print("🚀 Starting Seefast Data Canvas Agent...")
    
    # Load Swagger endpoints into ChromaDB
    try:
        from app.registry.endpoint_registry import get_registry
        registry = get_registry()
        count = await registry.load_swagger(settings.swagger_url)
        print(f"✅ Loaded {count} endpoints from Swagger")
    except Exception as e:
        print(f"⚠️ Failed to load Swagger: {e}")
    
    # Initialize cache (connects to Redis)
    try:
        from app.services.cache import get_cache
        get_cache()
    except Exception as e:
        print(f"⚠️ Cache init warning: {e}")
    
    print("✅ Seefast ready!")
    
    yield  # App runs here
    
    # SHUTDOWN
    print("👋 Shutting down...")


# Create app with lifespan
app = FastAPI(
    title="Seefast Data Canvas Agent",
    description="AI-powered API data visualization",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Seefast Data Canvas Agent",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.registry.endpoint_registry import get_registry
    registry = get_registry()
    return {
        "status": "healthy",
        "endpoints_loaded": registry.get_endpoint_count(),
    }
