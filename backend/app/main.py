"""
BLB3D ERP - Main FastAPI Application
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import router as api_v1_router
from app.core.config import settings
from app.exceptions import BLB3DException
from app.logging_config import setup_logging, get_logger

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(
        "Starting BLB3D ERP API",
        extra={
            "version": settings.VERSION,
            "environment": getattr(settings, "ENVIRONMENT", "development"),
            "debug": getattr(settings, "DEBUG", False),
        }
    )
    yield
    # Shutdown
    logger.info("Shutting down BLB3D ERP API")


# Create FastAPI app
app = FastAPI(
    title="BLB3D ERP API",
    description="Enterprise Resource Planning system for BLB3D Printing",
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if hasattr(settings, 'ALLOWED_ORIGINS') else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================
# Exception Handlers
# ===================


@app.exception_handler(BLB3DException)
async def blb3d_exception_handler(request: Request, exc: BLB3DException):
    """Handle all custom BLB3D exceptions."""
    logger.warning(
        f"BLB3D Exception: {exc.error_code} - {exc.message}",
        extra={"error_code": exc.error_code, "details": exc.details, "path": request.url.path}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with cleaner format."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(
        f"Validation error on {request.url.path}",
        extra={"errors": errors}
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": errors},
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database errors."""
    # Log full error for debugging but don't expose to client
    logger.error(
        f"Database error on {request.url.path}: {str(exc)}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "DATABASE_ERROR",
            "message": "A database error occurred. Please try again.",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler for unexpected errors."""
    # Log full stack trace for debugging
    logger.error(
        f"Unexpected error on {request.url.path}: {str(exc)}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


# Include API routes
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BLB3D ERP API",
        "version": "1.0.0",
        "status": "online"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
