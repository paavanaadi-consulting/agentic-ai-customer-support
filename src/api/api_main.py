"""
API-only main application
Lightweight FastAPI server for customer support API endpoints
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import time

from config.env_settings import CONFIG
from src.api.routes import router as api_router
from src.api.kafka_routes import router as kafka_router
from src.services.service_factory import (
    initialize_service_factory_with_optimized_mcp,
    initialize_service_factory_with_optimized_mcp_default,
    initialize_service_factory
)
from src.mcp.postgres_mcp_client import get_optimized_mcp_client, close_optimized_mcp_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, CONFIG.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
service_factory = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global service_factory
    
    # Startup
    logger.info("Starting API server...")
    try:
        # Try to initialize with optimized MCP client first
        logger.info("Initializing optimized MCP client...")
        try:
            connection_string = os.getenv("DATABASE_URL")
            mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8001")
            
            service_factory = await initialize_service_factory_with_optimized_mcp(
                connection_string=connection_string,
                mcp_server_url=mcp_server_url,
                use_direct_connection=True
            )
            logger.info("Service factory initialized with optimized MCP client")
            
        except Exception as e:
            logger.warning(f"Optimized MCP client initialization failed: {e}")
            logger.info("Trying optimized MCP client with default settings...")
            
            try:
                service_factory = await initialize_service_factory_with_optimized_mcp_default()
                logger.info("Service factory initialized with default optimized MCP client")
                
            except Exception as e2:
                logger.warning(f"Default optimized MCP client failed: {e2}")
                logger.info("Falling back to in-memory services...")
                service_factory = initialize_service_factory()
        
        logger.info("API server started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down API server...")
        
        # Clean up optimized MCP client if it was used
        try:
            await close_optimized_mcp_client()
            logger.info("Optimized MCP client closed")
        except Exception:
            pass

# Create FastAPI application
app = FastAPI(
    title="Agentic AI Customer Support API",
    description="RESTful API for AI-powered customer support system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add custom middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": time.time()
        }
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    try:
        # Check service factory status
        service_status = "not_initialized"
        if service_factory:
            try:
                # Test service factory by checking customer service
                customer_service = service_factory.customer_service
                if customer_service:
                    service_status = "healthy"
                else:
                    service_status = "unhealthy"
            except Exception as e:
                logger.warning(f"Service health check failed: {e}")
                service_status = "unhealthy"
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0",
            "services": {
                "optimized_mcp_client": "available",
                "service_factory": service_status
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": time.time(),
                "error": str(e)
            }
        )

# Include routers
app.include_router(api_router, prefix="/api/v1", tags=["api"])
app.include_router(kafka_router, prefix="/api/v1", tags=["kafka", "streaming"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Agentic AI Customer Support API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        workers=4
    )
