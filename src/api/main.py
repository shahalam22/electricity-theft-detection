from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from contextlib import asynccontextmanager
import sys
import os
import time

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import settings
from src.config.logging_config import setup_logging
from src.config.database import engine, Base
from src.api.dependencies import model_manager, request_tracker, get_request_stats
from src.api.routes import data_ingestion, prediction, alerts, explanations
from src.api.models.response_models import HealthCheckResponse, ErrorResponse
from loguru import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Electricity Theft Detection API...")
    setup_logging()
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    # Load ML model
    try:
        model_manager.load_model()
        logger.success("ML model loaded successfully")
    except Exception as e:
        logger.warning(f"ML model not loaded: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Electricity Theft Detection API...")


# Create FastAPI app
app = FastAPI(
    title="Electricity Theft Detection System",
    description="AI-powered electricity theft detection using smart meter data and FA-XGBoost",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Track request
    request_tracker.track_request(
        endpoint=request.url.path,
        method=request.method,
        response_time=process_time,
        status_code=response.status_code
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Custom exception handler
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            error_details={"path": request.url.path, "method": request.method}
        ).dict()
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Electricity Theft Detection System API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/api/docs",
            "data_ingestion": "/api/v1/data",
            "predictions": "/api/v1/predict", 
            "alerts": "/api/v1/alerts",
            "explanations": "/api/v1/explain"
        }
    }


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        start_time = time.time()
        health_status = "healthy"
        
        # Test database connection
        database_status = {"status": "connected", "response_time_ms": 0}
        try:
            db_start = time.time()
            with engine.connect() as conn:
                result = conn.execute("SELECT 1")
                result.fetchone()
            database_status["response_time_ms"] = round((time.time() - db_start) * 1000, 2)
        except Exception as e:
            database_status = {"status": "disconnected", "error": str(e)}
            health_status = "degraded"
        
        # Check model status
        model_info = model_manager.get_model_info()
        model_status = {
            "status": "loaded" if model_info["status"] == "loaded" else "not_loaded",
            "model_type": model_info.get("model_type", "unknown"),
            "is_trained": model_info.get("is_trained", False)
        }
        
        if model_status["status"] != "loaded":
            health_status = "degraded"
        
        # Get system stats
        system_stats = get_request_stats()
        
        total_time = time.time() - start_time
        
        return HealthCheckResponse(
            status=health_status,
            version="1.0.0",
            uptime_seconds=system_stats["uptime_seconds"],
            database=database_status,
            model=model_status,
            metrics={
                "total_requests": system_stats["total_requests"],
                "requests_per_second": system_stats["requests_per_second"],
                "health_check_time_ms": round(total_time * 1000, 2)
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content=HealthCheckResponse(
                status="unhealthy",
                version="1.0.0", 
                uptime_seconds=0,
                database={"status": "unknown", "error": str(e)},
                model={"status": "unknown", "error": str(e)}
            ).dict()
        )


@app.get("/info")
async def app_info():
    """Application information"""
    return {
        "app_name": "Electricity Theft Detection System",
        "version": "1.0.0",
        "description": "AI-powered electricity theft detection using FA-XGBoost and statistical features",
        "features": [
            "Real-time theft detection",
            "Statistical feature engineering", 
            "Explainable AI predictions (SHAP/LIME)",
            "Alert management dashboard",
            "Periodic model retraining",
            "Business impact analysis"
        ],
        "tech_stack": {
            "backend": "FastAPI + Python 3.9+",
            "database": "PostgreSQL",
            "ml_framework": "XGBoost + scikit-learn",
            "feature_engineering": "tsfresh + custom features",
            "explainability": "SHAP + LIME",
            "optimization": "Firefly Algorithm"
        },
        "api_documentation": "/api/docs",
        "model_info": model_manager.get_model_info()
    }


@app.get("/stats")
async def get_system_stats():
    """Get system statistics"""
    return {
        "message": "System statistics",
        "data": get_request_stats()
    }


# Include API routes
app.include_router(data_ingestion.router, prefix="/api/v1", tags=["Data Ingestion"])
app.include_router(prediction.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(alerts.router, prefix="/api/v1", tags=["Alert Management"])
app.include_router(explanations.router, prefix="/api/v1", tags=["Model Explanations"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )