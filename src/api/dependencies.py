from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import time
import json
from pathlib import Path
from loguru import logger

from src.config.database import get_db
from src.config.settings import settings
from src.models.fa_xgboost import FAXGBoostModel
from src.models.explainer import ModelExplainer


class ModelManager:
    """Singleton model manager for API"""
    _instance = None
    _model = None
    _explainer = None
    _model_loaded = False
    _last_load_time = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance
    
    def load_model(self, model_path: str = None) -> FAXGBoostModel:
        """Load the trained model"""
        try:
            if self._model_loaded and self._model is not None:
                return self._model
            
            if model_path is None:
                # Find latest model file
                models_dir = Path("data/models")
                if not models_dir.exists():
                    raise FileNotFoundError("Models directory not found")
                
                model_files = list(models_dir.glob("fa_xgboost_*.joblib"))
                if not model_files:
                    raise FileNotFoundError("No trained model found")
                
                # Get the latest model file
                model_path = max(model_files, key=lambda p: p.stat().st_mtime)
            
            logger.info(f"Loading model from {model_path}")
            
            # Load model
            self._model = FAXGBoostModel()
            self._model.load_model(str(model_path))
            
            # Initialize explainer
            self._explainer = ModelExplainer()
            
            self._model_loaded = True
            self._last_load_time = time.time()
            
            logger.success("Model loaded successfully")
            return self._model
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Model loading failed: {str(e)}"
            )
    
    def get_model(self) -> FAXGBoostModel:
        """Get the loaded model"""
        if not self._model_loaded or self._model is None:
            return self.load_model()
        return self._model
    
    def get_explainer(self) -> ModelExplainer:
        """Get the model explainer"""
        if self._explainer is None:
            # Ensure model is loaded first
            self.get_model()
        return self._explainer
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._model_loaded and self._model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        if not self.is_model_loaded():
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "load_time": self._last_load_time,
            "model_type": "FA-XGBoost",
            "is_trained": self._model.is_trained,
            "feature_count": len(self._model.feature_importance) if self._model.feature_importance else 0
        }


# Global model manager instance
model_manager = ModelManager()


# Dependency functions
def get_model() -> FAXGBoostModel:
    """Dependency to get the loaded model"""
    return model_manager.get_model()


def get_explainer() -> ModelExplainer:
    """Dependency to get the model explainer"""
    return model_manager.get_explainer()


class RateLimiter:
    """Simple rate limiter"""
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, client_ip: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """Check if request is allowed based on rate limit"""
        now = time.time()
        
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if now - req_time < window_seconds
        ]
        
        # Check limit
        if len(self.requests[client_ip]) >= max_requests:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True


# Global rate limiter
rate_limiter = RateLimiter()


def check_rate_limit(request: Request):
    """Rate limiting dependency"""
    client_ip = request.client.host
    
    if not rate_limiter.is_allowed(client_ip, max_requests=settings.cors_origins):  # Using cors_origins as placeholder
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    return True


# Authentication (placeholder - implement proper auth in production)
security = HTTPBearer(auto_error=False)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """Get current user from token (placeholder implementation)"""
    if not settings.debug:  # In production, implement proper authentication
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Implement token validation logic here
        # For now, just return a dummy user
        return {"user_id": "system", "role": "admin"}
    
    # In development, return dummy user
    return {"user_id": "dev_user", "role": "admin"}


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Require admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


class CacheManager:
    """Simple in-memory cache manager"""
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = 300  # 5 minutes
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None
        
        # Check if expired
        if time.time() - self.timestamps[key] > self.default_ttl:
            self.delete(key)
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache"""
        self.cache[key] = value
        self.timestamps[key] = time.time()
        
        if ttl:
            # Custom TTL not implemented in this simple version
            pass
    
    def delete(self, key: str) -> None:
        """Delete value from cache"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()


# Global cache manager
cache_manager = CacheManager()


def get_cache() -> CacheManager:
    """Dependency to get cache manager"""
    return cache_manager


class RequestTracker:
    """Track API requests for monitoring"""
    def __init__(self):
        self.request_count = 0
        self.start_time = time.time()
        self.endpoints_stats = {}
    
    def track_request(self, endpoint: str, method: str, response_time: float, status_code: int):
        """Track a request"""
        self.request_count += 1
        
        key = f"{method} {endpoint}"
        if key not in self.endpoints_stats:
            self.endpoints_stats[key] = {
                "count": 0,
                "total_time": 0,
                "avg_time": 0,
                "errors": 0
            }
        
        stats = self.endpoints_stats[key]
        stats["count"] += 1
        stats["total_time"] += response_time
        stats["avg_time"] = stats["total_time"] / stats["count"]
        
        if status_code >= 400:
            stats["errors"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get request statistics"""
        uptime = time.time() - self.start_time
        return {
            "total_requests": self.request_count,
            "uptime_seconds": uptime,
            "requests_per_second": self.request_count / uptime if uptime > 0 else 0,
            "endpoints": self.endpoints_stats
        }


# Global request tracker
request_tracker = RequestTracker()


def track_request(request: Request):
    """Request tracking dependency"""
    start_time = time.time()
    
    def track_response(response):
        response_time = time.time() - start_time
        request_tracker.track_request(
            endpoint=request.url.path,
            method=request.method,
            response_time=response_time,
            status_code=response.status_code
        )
    
    # This would need to be implemented as middleware in the main app
    return track_response


def get_request_stats() -> Dict[str, Any]:
    """Get request statistics"""
    return request_tracker.get_stats()


# Validation helpers
def validate_meter_exists(meter_id: str, db: Session = Depends(get_db)) -> bool:
    """Validate that meter exists in database"""
    from src.database.models import Meter
    
    meter = db.query(Meter).filter(Meter.meter_id == meter_id).first()
    if not meter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meter {meter_id} not found"
        )
    return True


def validate_alert_exists(alert_id: int, db: Session = Depends(get_db)):
    """Validate that alert exists and return it"""
    from src.database.models import TheftAlert
    
    alert = db.query(TheftAlert).filter(TheftAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    return alert


# Error handlers for common scenarios
class APIException(HTTPException):
    """Custom API exception"""
    def __init__(self, status_code: int, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.details = details or {}


def handle_database_error(error: Exception) -> APIException:
    """Handle database errors"""
    logger.error(f"Database error: {error}")
    return APIException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message="Database service unavailable",
        error_code="DATABASE_ERROR",
        details={"error": str(error)}
    )


def handle_model_error(error: Exception) -> APIException:
    """Handle model errors"""
    logger.error(f"Model error: {error}")
    return APIException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        message="Model service unavailable",
        error_code="MODEL_ERROR",
        details={"error": str(error)}
    )


def handle_validation_error(error: Exception) -> APIException:
    """Handle validation errors"""
    logger.warning(f"Validation error: {error}")
    return APIException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation failed",
        error_code="VALIDATION_ERROR",
        details={"error": str(error)}
    )