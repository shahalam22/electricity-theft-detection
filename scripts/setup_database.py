#!/usr/bin/env python3
"""
Database setup script for Electricity Theft Detection System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from src.config.database import Base, engine
from src.config.settings import settings
from src.database.models import Meter, ConsumptionData, TheftAlert, ModelMetadata, SystemLog
from loguru import logger


def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Extract database name from URL
        db_name = settings.database_name
        
        # Create connection to PostgreSQL server (without specific database)
        server_url = f"postgresql://{settings.database_user}:{settings.database_password}@{settings.database_host}:{settings.database_port}/postgres"
        server_engine = create_engine(server_url)
        
        # Check if database exists
        with server_engine.connect() as conn:
            conn.execute(text("COMMIT"))  # End any existing transaction
            result = conn.execute(
                text("SELECT 1 FROM pg_catalog.pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if not result.fetchone():
                logger.info(f"Creating database: {db_name}")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                logger.success(f"Database {db_name} created successfully")
            else:
                logger.info(f"Database {db_name} already exists")
                
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise


def create_tables():
    """Create all tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.success("All tables created successfully")
        
        # Create indexes for better performance
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_consumption_data_meter_date 
                ON consumption_data (meter_id, date);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_theft_alerts_status_priority 
                ON theft_alerts (status, priority);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_theft_alerts_prediction_date 
                ON theft_alerts (prediction_date DESC);
            """))
            
            conn.commit()
            logger.success("Database indexes created successfully")
            
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


def insert_sample_data():
    """Insert sample data for testing"""
    try:
        logger.info("Inserting sample data...")
        
        from src.config.database import SessionLocal
        from datetime import date, datetime
        
        db = SessionLocal()
        
        # Sample meters
        sample_meters = [
            Meter(
                meter_id="METER_001",
                customer_id="CUST_001",
                location="Dhaka_Zone_A_Block_1",
                customer_category="residential",
                billing_cycle=30
            ),
            Meter(
                meter_id="METER_002",
                customer_id="CUST_002",
                location="Dhaka_Zone_A_Block_2",
                customer_category="commercial",
                billing_cycle=30
            ),
            Meter(
                meter_id="METER_003",
                customer_id="CUST_003",
                location="Dhaka_Zone_B_Block_1",
                customer_category="industrial",
                billing_cycle=30
            )
        ]
        
        for meter in sample_meters:
            existing = db.query(Meter).filter(Meter.meter_id == meter.meter_id).first()
            if not existing:
                db.add(meter)
        
        db.commit()
        db.close()
        
        logger.success("Sample data inserted successfully")
        
    except Exception as e:
        logger.error(f"Error inserting sample data: {e}")
        raise


def main():
    """Main setup function"""
    try:
        logger.info("Starting database setup...")
        
        # Create database
        create_database()
        
        # Create tables
        create_tables()
        
        # Insert sample data
        insert_sample_data()
        
        logger.success("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()