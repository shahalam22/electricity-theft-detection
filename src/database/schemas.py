from pydantic import BaseModel, validator
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from enum import Enum


class CustomerCategory(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"


class AlertStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Meter Schemas
class MeterBase(BaseModel):
    meter_id: str
    customer_id: Optional[str] = None
    location: Optional[str] = None
    customer_category: Optional[CustomerCategory] = None
    billing_cycle: Optional[int] = 30


class MeterCreate(MeterBase):
    pass


class Meter(MeterBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Consumption Data Schemas
class ConsumptionDataBase(BaseModel):
    meter_id: str
    date: date
    consumption: float
    
    @validator('consumption')
    def validate_consumption(cls, v):
        if v < 0:
            raise ValueError('Consumption cannot be negative')
        return v


class ConsumptionDataCreate(ConsumptionDataBase):
    pass


class ConsumptionData(ConsumptionDataBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Batch consumption data for bulk upload
class ConsumptionDataBatch(BaseModel):
    data: List[ConsumptionDataCreate]


# Theft Alert Schemas
class TheftAlertBase(BaseModel):
    meter_id: str
    prediction_date: date
    theft_probability: float
    anomaly_score: float
    features_explanation: Optional[Dict[str, Any]] = None
    estimated_loss_bdt: Optional[float] = None
    priority: Optional[Priority] = Priority.MEDIUM


class TheftAlertCreate(TheftAlertBase):
    pass


class TheftAlertUpdate(BaseModel):
    status: AlertStatus
    reviewed_by: Optional[str] = None


class TheftAlert(TheftAlertBase):
    id: int
    status: AlertStatus
    reviewed_by: Optional[str] = None
    review_date: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Prediction Request/Response Schemas
class PredictionRequest(BaseModel):
    meter_id: str
    consumption_data: List[Dict[str, Any]]  # List of {date, consumption} pairs
    
    @validator('consumption_data')
    def validate_consumption_data(cls, v):
        if len(v) < 30:  # Minimum 30 days of data required
            raise ValueError('At least 30 days of consumption data required')
        return v


class PredictionResponse(BaseModel):
    meter_id: str
    prediction_date: date
    theft_probability: float
    anomaly_score: float
    risk_level: str
    confidence: float
    feature_explanations: Dict[str, Dict[str, float]]
    recommended_action: str
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        if v not in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
            raise ValueError('Invalid risk level')
        return v


# Model Metadata Schemas
class ModelMetadataBase(BaseModel):
    model_name: str
    version: str
    accuracy: Optional[float] = None
    precision_score: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    roc_auc: Optional[float] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    feature_importance: Optional[Dict[str, float]] = None


class ModelMetadataCreate(ModelMetadataBase):
    training_date: datetime
    model_path: str
    training_data_size: Optional[int] = None
    validation_data_size: Optional[int] = None


class ModelMetadata(ModelMetadataBase):
    id: int
    training_date: datetime
    model_path: str
    is_active: bool
    training_data_size: Optional[int] = None
    validation_data_size: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Dashboard Summary Schemas
class DashboardSummary(BaseModel):
    total_meters: int
    total_alerts: int
    pending_reviews: int
    confirmed_thefts: int
    false_positives: int
    estimated_total_loss_bdt: float
    detection_rate: float
    false_positive_rate: float


# API Response Schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None