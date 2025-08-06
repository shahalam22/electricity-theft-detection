#!/usr/bin/env python3
"""
Simple FastAPI server for Electricity Theft Detection System
This version runs without database and ML model dependencies for demo purposes
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import random
import time
from datetime import datetime, timedelta
import uvicorn

# Mock data models
class MeterData(BaseModel):
    meter_id: str
    customer_name: Optional[str] = None
    location: Optional[str] = None
    area: Optional[str] = None
    customer_type: str = "residential"

class PredictionRequest(BaseModel):
    meter_id: str
    days: int = 30
    include_features: bool = True

class AlertResponse(BaseModel):
    id: int
    meter_id: str
    risk_score: float
    risk_level: str
    status: str
    location: Optional[str]
    area: Optional[str]
    estimated_loss: float
    created_at: str
    confidence: float

# Create FastAPI app
app = FastAPI(
    title="Electricity Theft Detection System (Demo Mode)",
    description="AI-powered electricity theft detection - Demo without database",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data storage
mock_alerts = []
mock_meters = []

# Initialize with some mock data
def init_mock_data():
    global mock_alerts, mock_meters
    
    # Mock meters
    for i in range(1, 21):
        mock_meters.append({
            "meter_id": f"M{i:06d}",
            "customer_name": f"Customer {i}",
            "location": f"Address {i}, Zone {(i-1)//5 + 1}",
            "area": f"Area {(i-1)//5 + 1}",
            "customer_type": random.choice(["residential", "commercial", "industrial"])
        })
    
    # Mock alerts
    risk_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    statuses = ["pending", "confirmed", "rejected"]
    
    for i in range(1, 16):
        risk_level = random.choice(risk_levels)
        risk_score = {
            "LOW": random.uniform(0.1, 0.4),
            "MEDIUM": random.uniform(0.4, 0.6),
            "HIGH": random.uniform(0.6, 0.8),
            "CRITICAL": random.uniform(0.8, 1.0)
        }[risk_level]
        
        mock_alerts.append({
            "id": i,
            "meter_id": f"M{i:06d}",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "status": random.choice(statuses),
            "location": f"Address {i}, Zone {(i-1)//5 + 1}",
            "area": f"Area {(i-1)//5 + 1}",
            "estimated_loss": random.uniform(1000, 50000),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "confidence": random.uniform(0.7, 0.95),
            "consumption_reduction": random.uniform(10, 60)
        })

# Initialize mock data
init_mock_data()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Electricity Theft Detection System API (Demo Mode)",
        "version": "1.0.0",
        "status": "running",
        "mode": "demo",
        "endpoints": {
            "health": "/health",
            "docs": "/api/docs",
            "data_ingestion": "/api/v1/data",
            "predictions": "/api/v1/predict", 
            "alerts": "/api/v1/alerts",
            "explanations": "/api/v1/explain"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "mode": "demo",
        "uptime_seconds": 3600,
        "database": {"status": "mock", "response_time_ms": 1.5},
        "model": {"status": "mock", "model_type": "FA-XGBoost", "is_trained": True},
        "metrics": {
            "total_requests": random.randint(100, 1000),
            "requests_per_second": random.uniform(1.0, 5.0),
            "health_check_time_ms": 2.3
        }
    }

@app.get("/info")
async def app_info():
    """Application information"""
    return {
        "app_name": "Electricity Theft Detection System",
        "version": "1.0.0",
        "mode": "demo",
        "description": "AI-powered electricity theft detection using FA-XGBoost",
        "features": [
            "Real-time theft detection",
            "Statistical feature engineering", 
            "Explainable AI predictions (SHAP/LIME)",
            "Alert management dashboard",
            "Periodic model retraining"
        ],
        "model_info": {
            "status": "loaded",
            "model_type": "FA-XGBoost",
            "version": "2.1.0",
            "is_trained": True,
            "accuracy": 0.942,
            "precision": 0.918,
            "recall": 0.883
        }
    }

@app.get("/stats")
async def get_system_stats():
    """System statistics"""
    return {
        "message": "System statistics",
        "data": {
            "uptime_seconds": 3600,
            "total_requests": random.randint(500, 2000),
            "requests_per_second": random.uniform(2.0, 8.0),
            "average_response_time": random.uniform(50, 200),
            "error_rate": random.uniform(0.001, 0.01)
        }
    }

# Data endpoints
@app.post("/api/v1/data/meters/register")
async def register_meter(meter: MeterData):
    """Register a new meter"""
    # Check if meter already exists
    if any(m["meter_id"] == meter.meter_id for m in mock_meters):
        raise HTTPException(status_code=400, detail="Meter already exists")
    
    new_meter = meter.dict()
    mock_meters.append(new_meter)
    
    return {
        "status": "success",
        "message": "Meter registered successfully",
        "data": new_meter
    }

@app.get("/api/v1/data/meters")
async def get_meters(limit: int = 100):
    """Get all registered meters"""
    return {
        "status": "success",
        "data": {
            "meters": mock_meters[:limit],
            "total": len(mock_meters)
        }
    }

# Prediction endpoints
@app.post("/api/v1/predict/single")
async def predict_single(request: PredictionRequest):
    """Single meter prediction"""
    # Simulate processing time
    time.sleep(0.5)
    
    # Generate mock prediction
    risk_score = random.uniform(0.1, 0.95)
    risk_level = "LOW" if risk_score < 0.4 else "MEDIUM" if risk_score < 0.6 else "HIGH" if risk_score < 0.8 else "CRITICAL"
    
    prediction = {
        "meter_id": request.meter_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "confidence": random.uniform(0.7, 0.95),
        "features": {
            "consumption_variance": random.uniform(0.1, 0.9),
            "peak_hour_ratio": random.uniform(0.2, 0.8),
            "monthly_trend": random.uniform(-0.5, 0.5),
            "weekend_pattern": random.uniform(0.1, 0.7),
            "usage_consistency": random.uniform(0.3, 0.9)
        } if request.include_features else None
    }
    
    return {
        "status": "success",
        "message": "Prediction completed",
        "data": prediction
    }

# Alert endpoints
@app.get("/api/v1/alerts/")
async def get_alerts(
    limit: int = 20, 
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    days: Optional[int] = None
):
    """Get alerts with optional filtering"""
    filtered_alerts = mock_alerts.copy()
    
    if status:
        filtered_alerts = [a for a in filtered_alerts if a["status"] == status]
    
    if risk_level:
        filtered_alerts = [a for a in filtered_alerts if a["risk_level"] == risk_level]
    
    if days:
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_alerts = [
            a for a in filtered_alerts 
            if datetime.fromisoformat(a["created_at"]) >= cutoff_date
        ]
    
    return {
        "status": "success",
        "data": {
            "alerts": filtered_alerts[:limit],
            "total": len(filtered_alerts)
        }
    }

@app.get("/api/v1/alerts/{alert_id}")
async def get_alert(alert_id: int):
    """Get specific alert details"""
    alert = next((a for a in mock_alerts if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "status": "success",
        "data": alert
    }

@app.post("/api/v1/alerts/{alert_id}/confirm")
async def confirm_alert(alert_id: int, notes: Optional[Dict[str, str]] = None):
    """Confirm an alert"""
    alert = next((a for a in mock_alerts if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert["status"] = "confirmed"
    alert["updated_at"] = datetime.now().isoformat()
    if notes:
        alert["investigation_notes"] = notes.get("notes", "")
    
    return {
        "status": "success",
        "message": "Alert confirmed successfully",
        "data": alert
    }

@app.post("/api/v1/alerts/{alert_id}/reject")
async def reject_alert(alert_id: int, notes: Optional[Dict[str, str]] = None):
    """Reject an alert"""
    alert = next((a for a in mock_alerts if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert["status"] = "rejected"
    alert["updated_at"] = datetime.now().isoformat()
    if notes:
        alert["investigation_notes"] = notes.get("notes", "")
    
    return {
        "status": "success",
        "message": "Alert rejected successfully",
        "data": alert
    }

@app.get("/api/v1/alerts/dashboard/summary")
async def get_dashboard_summary():
    """Get dashboard summary statistics"""
    pending_alerts = len([a for a in mock_alerts if a["status"] == "pending"])
    confirmed_alerts = len([a for a in mock_alerts if a["status"] == "confirmed"])
    total_meters = len(mock_meters)
    
    return {
        "status": "success",
        "data": {
            "summary": {
                "pending_alerts": pending_alerts,
                "confirmed_alerts": confirmed_alerts,
                "total_alerts": len(mock_alerts),
                "total_meters": total_meters,
                "low_risk_alerts": len([a for a in mock_alerts if a["risk_level"] == "LOW"]),
                "medium_risk_alerts": len([a for a in mock_alerts if a["risk_level"] == "MEDIUM"]),
                "high_risk_alerts": len([a for a in mock_alerts if a["risk_level"] == "HIGH"]),
                "critical_risk_alerts": len([a for a in mock_alerts if a["risk_level"] == "CRITICAL"]),
                "potential_savings": sum(a["estimated_loss"] for a in mock_alerts if a["status"] == "confirmed"),
                "detection_rate": 0.942,
                "alert_change_percentage": random.uniform(-5, 15),
                "meter_growth_percentage": random.uniform(2, 8),
                "savings_change_percentage": random.uniform(5, 25),
                "detection_improvement": random.uniform(1, 3)
            }
        }
    }

# Explanation endpoints
@app.get("/api/v1/explain/alert/{alert_id}")
async def explain_alert(alert_id: int):
    """Get explanation for an alert"""
    alert = next((a for a in mock_alerts if a["id"] == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {
        "status": "success",
        "data": {
            "alert_id": alert_id,
            "explanation": {
                "shap_values": [random.uniform(-0.1, 0.1) for _ in range(10)],
                "feature_names": ["consumption_variance", "peak_hour_ratio", "monthly_trend", "weekend_pattern", "usage_consistency"],
                "lime_explanation": "High consumption variance and irregular peak hour patterns indicate potential theft"
            }
        }
    }

if __name__ == "__main__":
    print("Starting Electricity Theft Detection System (Demo Mode)")
    print("Dashboard will be available at: http://localhost:3000")
    print("API Documentation: http://localhost:8000/api/docs")
    print("Backend API: http://localhost:8000")
    
    uvicorn.run(
        "run_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )