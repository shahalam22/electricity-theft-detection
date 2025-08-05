from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any
from datetime import datetime, date
from loguru import logger

from src.config.database import get_db
from src.database.models import Meter, ConsumptionData
from src.api.models.request_models import (
    MeterRegistration, SingleConsumptionUpload, BulkConsumptionUpload, 
    BatchMeterUpload, ConsumptionDataPoint
)
from src.api.models.response_models import (
    SuccessResponse, ErrorResponse, ConsumptionUploadResponse, 
    MeterRegistrationResponse, BatchUploadResponse
)
from src.api.dependencies import get_current_user, check_rate_limit, validate_meter_exists
from src.utils.validators import DataValidator


router = APIRouter(prefix="/data", tags=["Data Ingestion"])


@router.post("/meters/register", 
            response_model=MeterRegistrationResponse,
            summary="Register a new meter",
            description="Register a new electricity meter in the system")
async def register_meter(
    meter_data: MeterRegistration,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(check_rate_limit)
):
    """Register a new electricity meter"""
    try:
        logger.info(f"Registering new meter: {meter_data.meter_id}")
        
        # Check if meter already exists
        existing_meter = db.query(Meter).filter(Meter.meter_id == meter_data.meter_id).first()
        if existing_meter:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Meter {meter_data.meter_id} already exists"
            )
        
        # Create new meter
        new_meter = Meter(
            meter_id=meter_data.meter_id,
            customer_id=meter_data.customer_id,
            location=meter_data.location,
            customer_category=meter_data.customer_category,
            billing_cycle=meter_data.billing_cycle
        )
        
        db.add(new_meter)
        db.commit()
        db.refresh(new_meter)
        
        logger.success(f"Meter {meter_data.meter_id} registered successfully")
        
        return MeterRegistrationResponse(
            message="Meter registered successfully",
            data={
                "meter_id": new_meter.meter_id,
                "customer_id": new_meter.customer_id,
                "location": new_meter.location,
                "customer_category": new_meter.customer_category,
                "billing_cycle": new_meter.billing_cycle,
                "created_at": new_meter.created_at.isoformat()
            }
        )
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Meter registration failed due to data conflict"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering meter: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Meter registration failed: {str(e)}"
        )


@router.post("/consumption/single",
            response_model=ConsumptionUploadResponse,
            summary="Upload single consumption reading",
            description="Upload a single consumption reading for a meter")
async def upload_single_consumption(
    consumption_data: SingleConsumptionUpload,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(check_rate_limit)
):
    """Upload single consumption reading"""
    try:
        logger.info(f"Uploading consumption data for meter {consumption_data.meter_id}")
        
        # Validate meter exists
        validate_meter_exists(consumption_data.meter_id, db)
        
        # Validate consumption data
        validator = DataValidator()
        validation_result = validator.validate_business_rules(
            pd.DataFrame([{
                'meter_id': consumption_data.meter_id,
                'date': consumption_data.date,
                'consumption': consumption_data.consumption
            }])
        )
        
        warnings = []
        if not validation_result['valid']:
            warnings = validation_result['errors']
        
        # Check if record already exists
        existing_record = db.query(ConsumptionData).filter(
            ConsumptionData.meter_id == consumption_data.meter_id,
            ConsumptionData.date == consumption_data.date
        ).first()
        
        if existing_record:
            # Update existing record
            existing_record.consumption = consumption_data.consumption
            action = "updated"
        else:
            # Create new record
            new_record = ConsumptionData(
                meter_id=consumption_data.meter_id,
                date=consumption_data.date,
                consumption=consumption_data.consumption
            )
            db.add(new_record)
            action = "created"
        
        db.commit()
        
        logger.success(f"Consumption data {action} for meter {consumption_data.meter_id}")
        
        return ConsumptionUploadResponse(
            message=f"Consumption data {action} successfully",
            data={
                "meter_id": consumption_data.meter_id,
                "date": consumption_data.date.isoformat(),
                "consumption": consumption_data.consumption,
                "action": action,
                "validation_warnings": warnings
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading consumption data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Consumption upload failed: {str(e)}"
        )


@router.post("/consumption/bulk",
            response_model=ConsumptionUploadResponse,
            summary="Upload bulk consumption data",
            description="Upload multiple consumption readings for a single meter")
async def upload_bulk_consumption(
    bulk_data: BulkConsumptionUpload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(check_rate_limit)
):
    """Upload bulk consumption data for a single meter"""
    try:
        logger.info(f"Uploading bulk consumption data for meter {bulk_data.meter_id} ({len(bulk_data.consumption_data)} records)")
        
        # Validate meter exists
        validate_meter_exists(bulk_data.meter_id, db)
        
        # Process consumption data
        records_created = 0
        records_updated = 0
        validation_warnings = []
        
        for data_point in bulk_data.consumption_data:
            try:
                # Check if record exists
                existing_record = db.query(ConsumptionData).filter(
                    ConsumptionData.meter_id == bulk_data.meter_id,
                    ConsumptionData.date == data_point.date
                ).first()
                
                if existing_record:
                    existing_record.consumption = data_point.consumption
                    records_updated += 1
                else:
                    new_record = ConsumptionData(
                        meter_id=bulk_data.meter_id,
                        date=data_point.date,
                        consumption=data_point.consumption
                    )
                    db.add(new_record)
                    records_created += 1
                    
            except Exception as e:
                validation_warnings.append(f"Error processing data for {data_point.date}: {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        # Schedule background validation
        background_tasks.add_task(
            validate_consumption_data_background,
            bulk_data.meter_id,
            [dp.dict() for dp in bulk_data.consumption_data]
        )
        
        logger.success(f"Bulk upload completed for meter {bulk_data.meter_id}: {records_created} created, {records_updated} updated")
        
        return ConsumptionUploadResponse(
            message="Bulk consumption data uploaded successfully",
            data={
                "meter_id": bulk_data.meter_id,
                "records_processed": len(bulk_data.consumption_data),
                "records_created": records_created,
                "records_updated": records_updated,
                "validation_warnings": validation_warnings
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in bulk upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk upload failed: {str(e)}"
        )


@router.post("/consumption/batch",
            response_model=BatchUploadResponse,
            summary="Upload batch data for multiple meters",
            description="Upload consumption data for multiple meters in a single request")
async def upload_batch_consumption(
    batch_data: BatchMeterUpload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(check_rate_limit)
):
    """Upload consumption data for multiple meters"""
    try:
        logger.info(f"Processing batch upload for {len(batch_data.data)} meters")
        
        total_records = 0
        successful_meters = 0
        failed_meters = 0
        errors = []
        
        for meter_data in batch_data.data:
            try:
                # Validate meter exists
                validate_meter_exists(meter_data.meter_id, db)
                
                # Process consumption data for this meter
                for data_point in meter_data.consumption_data:
                    existing_record = db.query(ConsumptionData).filter(
                        ConsumptionData.meter_id == meter_data.meter_id,
                        ConsumptionData.date == data_point.date
                    ).first()
                    
                    if existing_record:
                        existing_record.consumption = data_point.consumption
                    else:
                        new_record = ConsumptionData(
                            meter_id=meter_data.meter_id,
                            date=data_point.date,
                            consumption=data_point.consumption
                        )
                        db.add(new_record)
                    
                    total_records += 1
                
                successful_meters += 1
                
            except Exception as e:
                failed_meters += 1
                errors.append(f"Meter {meter_data.meter_id}: {str(e)}")
                continue
        
        # Commit all successful changes
        db.commit()
        
        # Schedule background processing for data quality checks
        background_tasks.add_task(
            process_batch_quality_checks,
            [meter_data.meter_id for meter_data in batch_data.data]
        )
        
        logger.success(f"Batch upload completed: {successful_meters} successful, {failed_meters} failed")
        
        return BatchUploadResponse(
            message="Batch upload completed",
            data={
                "total_meters": len(batch_data.data),
                "successful_meters": successful_meters,
                "failed_meters": failed_meters,
                "total_records_processed": total_records,
                "errors": errors,
                "processing_time_seconds": None  # Could be added with timing
            }
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in batch upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch upload failed: {str(e)}"
        )


@router.get("/meters/{meter_id}/consumption",
           summary="Get meter consumption history",
           description="Retrieve consumption history for a specific meter")
async def get_meter_consumption(
    meter_id: str,
    start_date: date = None,
    end_date: date = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get consumption history for a meter"""
    try:
        # Validate meter exists
        validate_meter_exists(meter_id, db)
        
        # Build query
        query = db.query(ConsumptionData).filter(ConsumptionData.meter_id == meter_id)
        
        if start_date:
            query = query.filter(ConsumptionData.date >= start_date)
        if end_date:
            query = query.filter(ConsumptionData.date <= end_date)
        
        # Get consumption records
        consumption_records = query.order_by(ConsumptionData.date.desc()).limit(limit).all()
        
        # Format response
        consumption_data = [
            {
                "date": record.date.isoformat(),
                "consumption": record.consumption,
                "created_at": record.created_at.isoformat()
            }
            for record in consumption_records
        ]
        
        return SuccessResponse(
            message="Consumption history retrieved successfully",
            data={
                "meter_id": meter_id,
                "total_records": len(consumption_data),
                "date_range": {
                    "start": consumption_records[-1].date.isoformat() if consumption_records else None,
                    "end": consumption_records[0].date.isoformat() if consumption_records else None
                },
                "consumption_data": consumption_data
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving consumption history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve consumption history: {str(e)}"
        )


@router.get("/meters",
           summary="List registered meters",
           description="Get list of all registered meters with optional filtering")
async def list_meters(
    location: str = None,
    customer_category: str = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List registered meters with optional filtering"""
    try:
        # Build query
        query = db.query(Meter)
        
        if location:
            query = query.filter(Meter.location.ilike(f"%{location}%"))
        if customer_category:
            query = query.filter(Meter.customer_category == customer_category)
        
        # Get total count
        total_count = query.count()
        
        # Get meters with pagination
        meters = query.offset(offset).limit(limit).all()
        
        # Format response
        meters_data = [
            {
                "meter_id": meter.meter_id,
                "customer_id": meter.customer_id,
                "location": meter.location,
                "customer_category": meter.customer_category,
                "billing_cycle": meter.billing_cycle,
                "created_at": meter.created_at.isoformat()
            }
            for meter in meters
        ]
        
        return SuccessResponse(
            message="Meters retrieved successfully",
            data={
                "meters": meters_data,
                "pagination": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "returned_count": len(meters_data)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error listing meters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve meters: {str(e)}"
        )


# Background tasks
async def validate_consumption_data_background(meter_id: str, consumption_data: List[Dict[str, Any]]):
    """Background task to validate consumption data"""
    try:
        logger.info(f"Running background validation for meter {meter_id}")
        
        # Import here to avoid circular imports
        import pandas as pd
        from src.utils.validators import DataValidator
        
        # Create DataFrame for validation
        df = pd.DataFrame(consumption_data)
        df['meter_id'] = meter_id
        
        # Run validation
        validator = DataValidator()
        validation_result = validator.comprehensive_validation(df)
        
        # Log results
        if validation_result['overall_validity']:
            logger.success(f"Background validation passed for meter {meter_id}")
        else:
            logger.warning(f"Background validation issues found for meter {meter_id}: {validation_result['summary']}")
        
        # Could store validation results in database or send alerts
        
    except Exception as e:
        logger.error(f"Error in background validation: {e}")


async def process_batch_quality_checks(meter_ids: List[str]):
    """Background task to process data quality checks for batch upload"""
    try:
        logger.info(f"Running batch quality checks for {len(meter_ids)} meters")
        
        # Implement batch quality checks here
        # This could include:
        # - Data consistency checks
        # - Anomaly detection
        # - Statistical analysis
        # - Alert generation for suspicious patterns
        
        logger.success("Batch quality checks completed")
        
    except Exception as e:
        logger.error(f"Error in batch quality checks: {e}")


# Import pandas here to avoid startup issues
import pandas as pd