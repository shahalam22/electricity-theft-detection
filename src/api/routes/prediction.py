from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from loguru import logger
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

from src.config.database import get_db
from src.database.models import Meter, ConsumptionData, TheftAlert
from src.models.fa_xgboost import FAXGBoostModel
from src.models.explainer import ModelExplainer
from src.data.feature_engineer import ElectricityFeatureEngineer
from src.data.preprocessor import ElectricityDataPreprocessor
from src.api.models.request_models import PredictionRequest, BatchPredictionRequest
from src.api.models.response_models import (
    PredictionResponse, BatchPredictionResponse, TheftPrediction, 
    PredictionExplanation, BusinessExplanation, FeatureExplanation,
    RiskLevel, SuccessResponse
)
from src.api.dependencies import (
    get_model, get_explainer, get_current_user, check_rate_limit, 
    validate_meter_exists, get_cache, CacheManager
)


router = APIRouter(prefix="/predict", tags=["Prediction"])


def classify_risk_level(probability: float) -> RiskLevel:
    """Classify theft probability into risk levels"""
    if probability >= 0.8:
        return RiskLevel.CRITICAL
    elif probability >= 0.6:
        return RiskLevel.HIGH
    elif probability >= 0.4:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW


def prepare_meter_features(meter_id: str, db: Session, consumption_data: List[Dict] = None) -> pd.DataFrame:
    """Prepare features for a single meter prediction"""
    try:
        # Get consumption data from database or use provided data
        if consumption_data:
            # Use provided consumption data
            df = pd.DataFrame(consumption_data)
            df['meter_id'] = meter_id
        else:
            # Get recent consumption data from database (last 90 days minimum)
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=90)
            
            consumption_records = db.query(ConsumptionData).filter(
                ConsumptionData.meter_id == meter_id,
                ConsumptionData.date >= start_date,
                ConsumptionData.date <= end_date
            ).order_by(ConsumptionData.date).all()
            
            if len(consumption_records) < 30:
                raise ValueError(f"Insufficient data for prediction. Need at least 30 days, got {len(consumption_records)}")
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'meter_id': record.meter_id,
                    'date': record.date,
                    'consumption': record.consumption
                }
                for record in consumption_records
            ])
        
        # Preprocess data
        preprocessor = ElectricityDataPreprocessor()
        df_processed, _ = preprocessor.preprocess_pipeline(df)
        
        # Engineer features
        feature_engineer = ElectricityFeatureEngineer()
        features_df = feature_engineer.combine_all_features(df_processed)
        
        return features_df
        
    except Exception as e:
        logger.error(f"Error preparing features for meter {meter_id}: {e}")
        raise


async def create_theft_alert(
    meter_id: str, 
    prediction: Dict[str, Any], 
    explanation: Dict[str, Any],
    db: Session
) -> Optional[int]:
    """Create theft alert if prediction is above threshold"""
    try:
        # Only create alert for high-risk predictions
        if prediction['risk_level'] not in ['HIGH', 'CRITICAL']:
            return None
        
        # Check if recent alert already exists (within 7 days)
        recent_date = datetime.now().date() - timedelta(days=7)
        existing_alert = db.query(TheftAlert).filter(
            TheftAlert.meter_id == meter_id,
            TheftAlert.prediction_date >= recent_date,
            TheftAlert.status == 'pending'
        ).first()
        
        if existing_alert:
            logger.info(f"Recent alert already exists for meter {meter_id}")
            return existing_alert.id
        
        # Get meter info for additional context
        meter = db.query(Meter).filter(Meter.meter_id == meter_id).first()
        
        # Estimate potential loss (simplified calculation)
        estimated_loss = prediction['theft_probability'] * 50000  # 50k BDT average loss
        
        # Determine priority
        priority = 'high' if prediction['risk_level'] == 'CRITICAL' else 'medium'
        
        # Create alert
        alert = TheftAlert(
            meter_id=meter_id,
            prediction_date=datetime.now().date(),
            theft_probability=prediction['theft_probability'],
            anomaly_score=prediction['theft_probability'],  # Using same value for now
            features_explanation=explanation.get('shap_analysis', {}),
            estimated_loss_bdt=estimated_loss,
            priority=priority
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        logger.success(f"Theft alert created for meter {meter_id} (ID: {alert.id})")
        return alert.id
        
    except Exception as e:
        logger.error(f"Error creating theft alert: {e}")
        return None


@router.post("/single",
            response_model=PredictionResponse,
            summary="Predict theft for single meter",
            description="Generate theft prediction for a single electricity meter")
async def predict_single_meter(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    model: FAXGBoostModel = Depends(get_model),
    explainer: ModelExplainer = Depends(get_explainer),
    cache: CacheManager = Depends(get_cache),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(check_rate_limit)
):
    """Generate theft prediction for a single meter"""
    try:
        start_time = time.time()
        logger.info(f"Processing prediction request for meter {request.meter_id}")
        
        # Check cache first
        cache_key = f"prediction_{request.meter_id}_{request.threshold}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"Returning cached prediction for meter {request.meter_id}")
            return PredictionResponse(
                message="Prediction retrieved from cache",
                data=cached_result
            )
        
        # Validate meter exists
        validate_meter_exists(request.meter_id, db)
        
        # Prepare consumption data
        consumption_data = None
        if request.consumption_data:
            consumption_data = [
                {
                    'date': dp.date,
                    'consumption': dp.consumption
                }
                for dp in request.consumption_data
            ]
        
        # Prepare features
        try:
            features_df = prepare_meter_features(request.meter_id, db, consumption_data)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Make prediction
        X = features_df.drop(['meter_id'], axis=1)
        theft_probability = float(model.predict_proba(X)[0])
        is_theft_predicted = theft_probability >= request.threshold
        risk_level = classify_risk_level(theft_probability)
        
        # Prepare prediction result
        prediction_result = {
            'meter_id': request.meter_id,
            'prediction_date': datetime.now().date(),
            'theft_probability': theft_probability,
            'risk_level': risk_level,
            'confidence': min(max(abs(theft_probability - 0.5) * 2, 0.5), 1.0),  # Simple confidence calculation
            'threshold_used': request.threshold,
            'is_theft_predicted': is_theft_predicted,
            'alert_created': False,
            'alert_id': None
        }
        
        # Generate explanation if requested
        explanation_data = None
        business_explanation_data = None
        
        if request.include_explanation:
            try:
                # Initialize explainer with sample data if needed
                if not explainer.shap_explainer:
                    sample_data = X.sample(n=min(100, len(X)), random_state=42)
                    explainer.initialize_shap_explainer(model, sample_data, explainer_type='tree')
                
                # Generate explanation
                X_instance = X.iloc[[0]]  # First (and only) row
                if request.explanation_method == 'shap':
                    explanation_result = explainer.explain_prediction_shap(X_instance, model, top_n=10)
                else:
                    explanation_result = explainer.explain_prediction_lime(X_instance, model, num_features=10)
                
                if 'error' not in explanation_result:
                    # Format technical explanation
                    if 'shap_analysis' in explanation_result:
                        top_features = explanation_result['shap_analysis']['top_features']
                    else:
                        top_features = explanation_result['lime_analysis']['feature_explanations']
                    
                    feature_explanations = []
                    for feature in top_features[:10]:
                        feature_explanations.append(FeatureExplanation(
                            feature_name=feature.get('feature_name', feature.get('feature_condition', 'unknown')),
                            feature_value=feature.get('feature_value', 0.0),
                            contribution=feature.get('shap_value', feature.get('importance', 0.0)),
                            importance=feature.get('contribution_magnitude', feature.get('importance_magnitude', 0.0)),
                            description=feature.get('feature_name', '').replace('_', ' ').title()
                        ))
                    
                    explanation_data = PredictionExplanation(
                        method=request.explanation_method,
                        top_features=feature_explanations,
                        base_probability=explanation_result.get('shap_analysis', {}).get('expected_value', 0.5),
                        prediction_difference=theft_probability - 0.5,
                        confidence_score=0.9  # Placeholder
                    )
                    
                    # Generate business explanation
                    business_result = explainer.generate_business_explanation(explanation_result)
                    if 'error' not in business_result:
                        business_explanation_data = BusinessExplanation(
                            key_indicators=business_result.get('key_indicators', [])[:5],
                            investigation_priorities=business_result.get('investigation_priorities', [])[:3],
                            risk_factors=business_result.get('key_indicators', [])[:3],
                            recommended_actions=business_result.get('next_steps', [])[:3]
                        )
                
            except Exception as e:
                logger.warning(f"Error generating explanation: {e}")
                # Continue without explanation rather than failing the prediction
        
        # Add explanations to prediction result
        prediction_result['explanation'] = explanation_data
        prediction_result['business_explanation'] = business_explanation_data
        
        # Create alert if high risk
        if is_theft_predicted and risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            background_tasks.add_task(
                create_theft_alert,
                request.meter_id,
                prediction_result,
                explanation_result if 'explanation_result' in locals() else {},
                db
            )
            prediction_result['alert_created'] = True
        
        # Cache result
        cache.set(cache_key, prediction_result, ttl=300)  # Cache for 5 minutes
        
        processing_time = time.time() - start_time
        logger.success(f"Prediction completed for meter {request.meter_id} in {processing_time:.2f}s (probability: {theft_probability:.4f})")
        
        return PredictionResponse(
            message="Prediction completed successfully",
            data=TheftPrediction(**prediction_result)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in single meter prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.post("/batch",
            response_model=BatchPredictionResponse,
            summary="Predict theft for multiple meters",
            description="Generate theft predictions for multiple electricity meters")
async def predict_batch_meters(
    request: BatchPredictionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    model: FAXGBoostModel = Depends(get_model),
    explainer: ModelExplainer = Depends(get_explainer),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(check_rate_limit)
):
    """Generate theft predictions for multiple meters"""
    try:
        start_time = time.time()
        logger.info(f"Processing batch prediction for {len(request.meter_ids)} meters")
        
        # Validate all meters exist
        existing_meters = db.query(Meter.meter_id).filter(
            Meter.meter_id.in_(request.meter_ids)
        ).all()
        existing_meter_ids = {meter.meter_id for meter in existing_meters}
        
        missing_meters = set(request.meter_ids) - existing_meter_ids
        if missing_meters:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meters not found: {list(missing_meters)}"
            )
        
        # Process predictions in parallel
        predictions = []
        successful_predictions = 0
        failed_predictions = 0
        high_risk_detections = 0
        alerts_to_create = []
        
        # Use ThreadPoolExecutor for CPU-bound tasks
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit all prediction tasks
            future_to_meter = {
                executor.submit(process_single_prediction, meter_id, db, model, request.threshold): meter_id
                for meter_id in request.meter_ids
            }
            
            # Collect results
            for future in future_to_meter:
                meter_id = future_to_meter[future]
                try:
                    result = future.result(timeout=30)  # 30 second timeout per prediction
                    if result:
                        predictions.append(result)
                        successful_predictions += 1
                        
                        if result['risk_level'] in ['HIGH', 'CRITICAL']:
                            high_risk_detections += 1
                            if result['is_theft_predicted']:
                                alerts_to_create.append(result)
                    else:
                        failed_predictions += 1
                        
                except Exception as e:
                    logger.error(f"Prediction failed for meter {meter_id}: {e}")
                    failed_predictions += 1
        
        # Create alerts in background
        if alerts_to_create:
            background_tasks.add_task(
                create_batch_alerts,
                alerts_to_create,
                db
            )
        
        processing_time = time.time() - start_time
        
        batch_result = {
            "total_meters": len(request.meter_ids),
            "successful_predictions": successful_predictions,
            "failed_predictions": failed_predictions,
            "high_risk_detections": high_risk_detections,
            "alerts_created": len(alerts_to_create),
            "processing_time_seconds": round(processing_time, 2),
            "predictions": predictions[:100]  # Limit response size
        }
        
        logger.success(f"Batch prediction completed: {successful_predictions}/{len(request.meter_ids)} successful in {processing_time:.2f}s")
        
        return BatchPredictionResponse(
            message="Batch predictions completed",
            data=batch_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {str(e)}"
        )


def process_single_prediction(meter_id: str, db: Session, model: FAXGBoostModel, threshold: float) -> Optional[Dict[str, Any]]:
    """Process prediction for a single meter (for parallel execution)"""
    try:
        # Prepare features
        features_df = prepare_meter_features(meter_id, db)
        
        # Make prediction
        X = features_df.drop(['meter_id'], axis=1)
        theft_probability = float(model.predict_proba(X)[0])
        is_theft_predicted = theft_probability >= threshold
        risk_level = classify_risk_level(theft_probability)
        
        return {
            'meter_id': meter_id,
            'theft_probability': theft_probability,
            'risk_level': risk_level.value,
            'is_theft_predicted': is_theft_predicted,
            'confidence': min(max(abs(theft_probability - 0.5) * 2, 0.5), 1.0)
        }
        
    except Exception as e:
        logger.error(f"Error processing prediction for meter {meter_id}: {e}")
        return None


async def create_batch_alerts(predictions: List[Dict[str, Any]], db: Session):
    """Background task to create alerts for batch predictions"""
    try:
        alerts_created = 0
        
        for prediction in predictions:
            try:
                alert_id = await create_theft_alert(
                    prediction['meter_id'],
                    prediction,
                    {},  # Empty explanation for batch
                    db
                )
                if alert_id:
                    alerts_created += 1
                    
            except Exception as e:
                logger.error(f"Error creating alert for meter {prediction['meter_id']}: {e}")
                continue
        
        logger.success(f"Created {alerts_created} alerts from batch predictions")
        
    except Exception as e:
        logger.error(f"Error in batch alert creation: {e}")


@router.get("/status/{meter_id}",
           summary="Get prediction status for meter",
           description="Get the latest prediction status and history for a meter")
async def get_prediction_status(
    meter_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get prediction status and history for a meter"""
    try:
        # Validate meter exists
        validate_meter_exists(meter_id, db)
        
        # Get recent alerts/predictions
        recent_alerts = db.query(TheftAlert).filter(
            TheftAlert.meter_id == meter_id
        ).order_by(TheftAlert.prediction_date.desc()).limit(limit).all()
        
        # Format alerts
        alerts_data = [
            {
                "alert_id": alert.id,
                "prediction_date": alert.prediction_date.isoformat(),
                "theft_probability": alert.theft_probability,
                "status": alert.status,
                "priority": alert.priority,
                "created_at": alert.created_at.isoformat()
            }
            for alert in recent_alerts
        ]
        
        # Get latest prediction summary
        latest_alert = recent_alerts[0] if recent_alerts else None
        prediction_summary = {
            "meter_id": meter_id,
            "latest_prediction": {
                "date": latest_alert.prediction_date.isoformat() if latest_alert else None,
                "theft_probability": latest_alert.theft_probability if latest_alert else None,
                "risk_level": classify_risk_level(latest_alert.theft_probability).value if latest_alert else "UNKNOWN",
                "status": latest_alert.status if latest_alert else None
            },
            "prediction_history": alerts_data,
            "total_predictions": len(alerts_data),
            "confirmed_thefts": len([a for a in recent_alerts if a.status == 'confirmed']),
            "false_positives": len([a for a in recent_alerts if a.status == 'rejected'])
        }
        
        return SuccessResponse(
            message="Prediction status retrieved successfully",
            data=prediction_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prediction status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prediction status: {str(e)}"
        )