from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "postgresql://username:password@localhost:5432/electricity_theft_db"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "electricity_theft_db"
    database_user: str = "username"
    database_password: str = "password"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "electricity-theft-detection-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Model Configuration
    model_path: str = "./data/models/"
    threshold_probability: float = 0.7
    batch_size: int = 1000
    feature_store_path: str = "./data/features/"
    
    # Application Settings
    debug: bool = True
    log_level: str = "INFO"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # External Services
    notification_email_host: Optional[str] = None
    notification_email_port: Optional[int] = None
    notification_email_user: Optional[str] = None
    notification_email_password: Optional[str] = None
    
    # Monitoring
    prometheus_port: int = 9090
    enable_metrics: bool = True
    
    # Feature Engineering
    tsfresh_n_jobs: int = 4
    feature_selection_k_best: int = 50
    
    # Model Training
    test_size: float = 0.2
    random_state: int = 42
    cv_folds: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()