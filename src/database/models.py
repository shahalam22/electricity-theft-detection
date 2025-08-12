from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from src.config.database import Base


class Meter(Base):
    """Smart meter information"""
    __tablename__ = "meters"
    
    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(String(50), unique=True, index=True, nullable=False)
    customer_id = Column(String(50), index=True)
    location = Column(String(255))
    customer_category = Column(String(50))  # residential, commercial, industrial
    billing_cycle = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    consumption_data = relationship("ConsumptionData", back_populates="meter")
    theft_alerts = relationship("TheftAlert", back_populates="meter")


class ConsumptionData(Base):
    """Daily electricity consumption data"""
    __tablename__ = "consumption_data"
    
    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(String(50), ForeignKey("meters.meter_id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    consumption = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    meter = relationship("Meter", back_populates="consumption_data")
    
    # Composite unique constraint will be added via Alembic migration


class TheftAlert(Base):
    """Theft detection alerts"""
    __tablename__ = "theft_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    meter_id = Column(String(50), ForeignKey("meters.meter_id"), nullable=False)
    prediction_date = Column(Date, nullable=False, index=True)
    theft_probability = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    features_explanation = Column(JSON)
    status = Column(String(20), default="pending", index=True)  # pending, confirmed, rejected
    reviewed_by = Column(String(100))
    review_date = Column(DateTime(timezone=True))
    estimated_loss_bdt = Column(Float)
    priority = Column(String(10), default="medium")  # high, medium, low
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    meter = relationship("Meter", back_populates="theft_alerts")


class ModelMetadata(Base):
    """ML model metadata and performance tracking"""
    __tablename__ = "model_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    training_date = Column(DateTime(timezone=True), nullable=False)
    accuracy = Column(Float)
    precision_score = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    roc_auc = Column(Float)
    model_path = Column(String(255))
    hyperparameters = Column(JSON)
    feature_importance = Column(JSON)
    is_active = Column(Boolean, default=False)
    training_data_size = Column(Integer)
    validation_data_size = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemLog(Base):
    """System operation logs"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_level = Column(String(10), nullable=False)  # INFO, WARNING, ERROR
    component = Column(String(50), nullable=False)  # api, model, data_pipeline
    message = Column(Text, nullable=False)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)