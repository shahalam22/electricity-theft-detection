from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

from src.config.database import get_db
from src.database.models import Meter, ConsumptionData, TheftAlert
from src.models.fa_xgboost import FAXGBoostModel
from src.models.explainer import ModelExplainer
from src.data.feature_engineer import ElectricityFeatureEngineer
from src.data.preprocessor import ElectricityDataPreprocessor
from src.api.models.request_models import ExplanationRequest
from src.api.models.response_models import (
    ExplanationResponse, SuccessResponse
)
from src.api.dependencies import (
    get_model, get_explainer, get_current_user, check_rate_limit,
    validate_meter_exists, get_cache, CacheManager
)


router = APIRouter(prefix="/explain", tags=["Model Explanations"])


@router.post("/prediction",
            response_model=ExplanationResponse,
            summary="Explain prediction for meter",
            description="Generate detailed explanation for theft prediction")
async def explain_prediction(
    request: ExplanationRequest,
    db: Session = Depends(get_db),
    model: FAXGBoostModel = Depends(get_model),
    explainer: ModelExplainer = Depends(get_explainer),
    cache: CacheManager = Depends(get_cache),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(check_rate_limit)
):
    """Generate detailed explanation for a meter's theft prediction"""
    try:
        logger.info(f"Generating explanation for meter {request.meter_id}")
        
        # Check cache first
        cache_key = f"explanation_{request.meter_id}_{request.method}_{request.top_features}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return ExplanationResponse(
                message="Explanation retrieved from cache",
                data=cached_result
            )
        
        # Validate meter exists
        validate_meter_exists(request.meter_id, db)
        
        # Prepare features for explanation
        features_df = await prepare_meter_features_for_explanation(request.meter_id, db)
        
        if features_df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient data for explanation generation"
            )
        
        # Get prediction first
        X = features_df.drop(['meter_id'], axis=1)
        theft_probability = float(model.predict_proba(X)[0])
        prediction = int(model.predict(X)[0])
        
        # Initialize explainer if needed
        if not explainer.shap_explainer and request.method == 'shap':
            sample_data = X.sample(n=min(100, len(X)), random_state=42)
            explainer.initialize_shap_explainer(model, sample_data, explainer_type='tree')
        elif not explainer.lime_explainer and request.method == 'lime':
            sample_data = X.sample(n=min(200, len(X)), random_state=42)
            explainer.initialize_lime_explainer(sample_data)
        
        # Generate explanation
        X_instance = X.iloc[[0]]  # First (and only) row
        
        if request.method == 'shap':
            explanation_result = explainer.explain_prediction_shap(
                X_instance, model, top_n=request.top_features
            )
        elif request.method == 'lime':
            explanation_result = explainer.explain_prediction_lime(
                X_instance, model, num_features=request.top_features
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported explanation method: {request.method}"
            )
        
        if 'error' in explanation_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Explanation generation failed: {explanation_result['error']}"
            )
        
        # Generate business-friendly explanation if requested
        business_explanation = None
        if request.business_friendly:
            business_result = explainer.generate_business_explanation(explanation_result)
            if 'error' not in business_result:
                business_explanation = business_result
        
        # Get additional context
        meter_context = await get_meter_context(request.meter_id, db)
        
        # Format final response
        explanation_data = {
            "meter_id": request.meter_id,
            "prediction_info": {
                "theft_probability": theft_probability,
                "prediction": prediction,
                "risk_level": _classify_risk_level(theft_probability),
                "prediction_date": datetime.now().isoformat()
            },
            "technical_explanation": explanation_result,
            "business_explanation": business_explanation,
            "meter_context": meter_context,
            "explanation_metadata": {
                "method": request.method,
                "features_analyzed": request.top_features,
                "model_type": "FA-XGBoost",
                "explanation_confidence": explanation_result.get('confidence_score', 0.9)
            }
        }
        
        # Cache result
        cache.set(cache_key, explanation_data, ttl=600)  # Cache for 10 minutes
        
        logger.success(f"Explanation generated for meter {request.meter_id}")
        
        return ExplanationResponse(
            message="Explanation generated successfully",
            data=explanation_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation generation failed: {str(e)}"
        )


@router.get("/global-importance",
           response_model=SuccessResponse,
           summary="Get global feature importance",
           description="Get global feature importance across all predictions")
async def get_global_feature_importance(
    sample_size: int = 1000,
    method: str = "shap",
    db: Session = Depends(get_db),
    model: FAXGBoostModel = Depends(get_model),
    explainer: ModelExplainer = Depends(get_explainer),
    cache: CacheManager = Depends(get_cache),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get global feature importance analysis"""
    try:
        logger.info(f"Generating global feature importance using {method}")
        
        # Check cache
        cache_key = f"global_importance_{method}_{sample_size}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return SuccessResponse(
                message="Global importance retrieved from cache",
                data=cached_result
            )
        
        # Get sample of recent consumption data
        recent_date = datetime.now().date() - timedelta(days=30)
        
        # Get sample meters with recent data
        sample_meters = db.query(Meter.meter_id).join(ConsumptionData).filter(
            ConsumptionData.date >= recent_date
        ).distinct().limit(sample_size).all()
        
        if len(sample_meters) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient data for global importance analysis"
            )
        
        # Prepare features for sample meters
        sample_features_list = []
        successful_meters = 0
        
        for meter_row in sample_meters[:min(100, sample_size)]:  # Limit for performance
            try:
                meter_id = meter_row.meter_id
                features_df = await prepare_meter_features_for_explanation(meter_id, db)
                if not features_df.empty:
                    sample_features_list.append(features_df)
                    successful_meters += 1
            except Exception as e:
                logger.warning(f"Failed to prepare features for meter {meter_id}: {e}")
                continue
        
        if successful_meters < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too few meters with sufficient data for analysis"
            )
        
        # Combine all features
        combined_features = pd.concat(sample_features_list, ignore_index=True)
        X_sample = combined_features.drop(['meter_id'], axis=1)
        
        # Generate global importance
        global_importance = explainer.explain_global_feature_importance(
            model, X_sample, method=method
        )
        
        if 'error' in global_importance:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Global importance analysis failed: {global_importance['error']}"
            )
        
        # Add metadata
        analysis_data = {
            "global_importance": global_importance,
            "analysis_metadata": {
                "sample_size": successful_meters,
                "total_features": len(X_sample.columns),
                "method": method,
                "analysis_date": datetime.now().isoformat()
            },
            "feature_insights": _generate_feature_insights(global_importance)
        }
        
        # Cache result
        cache.set(cache_key, analysis_data, ttl=3600)  # Cache for 1 hour
        
        logger.success(f"Global importance analysis completed ({successful_meters} meters)")
        
        return SuccessResponse(
            message="Global feature importance retrieved successfully",
            data=analysis_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in global importance analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Global importance analysis failed: {str(e)}"
        )


@router.get("/alert/{alert_id}",
           response_model=ExplanationResponse,
           summary="Explain alert prediction",
           description="Get explanation for a specific theft alert")
async def explain_alert(
    alert_id: int,
    method: str = "shap",
    top_features: int = 10,
    db: Session = Depends(get_db),
    model: FAXGBoostModel = Depends(get_model),
    explainer: ModelExplainer = Depends(get_explainer),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get explanation for a specific theft alert"""
    try:
        logger.info(f"Generating explanation for alert {alert_id}")
        
        # Get alert
        alert = db.query(TheftAlert).filter(TheftAlert.id == alert_id).first()
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )
        
        # Check if explanation already exists in alert
        if alert.features_explanation and isinstance(alert.features_explanation, dict):
            stored_explanation = alert.features_explanation
            
            # Format stored explanation
            explanation_data = {
                "alert_id": alert_id,
                "meter_id": alert.meter_id,
                "prediction_info": {
                    "theft_probability": alert.theft_probability,
                    "prediction_date": alert.prediction_date.isoformat(),
                    "risk_level": _classify_risk_level(alert.theft_probability),
                    "alert_status": alert.status
                },
                "technical_explanation": stored_explanation,
                "business_explanation": _generate_business_explanation_from_stored(stored_explanation),
                "alert_context": {
                    "created_at": alert.created_at.isoformat(),
                    "reviewed_by": alert.reviewed_by,
                    "review_date": alert.review_date.isoformat() if alert.review_date else None,
                    "estimated_loss_bdt": alert.estimated_loss_bdt,
                    "priority": alert.priority
                }
            }
            
            return ExplanationResponse(
                message="Alert explanation retrieved from stored data",
                data=explanation_data
            )
        
        # Generate fresh explanation
        explanation_request = ExplanationRequest(
            meter_id=alert.meter_id,
            method=method,
            top_features=top_features,
            business_friendly=True
        )
        
        # Use the regular explanation endpoint
        explanation_response = await explain_prediction(
            explanation_request, db, model, explainer, get_cache(), current_user, True
        )
        
        # Add alert-specific context
        explanation_data = explanation_response.data
        explanation_data["alert_id"] = alert_id
        explanation_data["alert_context"] = {
            "created_at": alert.created_at.isoformat(),
            "reviewed_by": alert.reviewed_by,
            "review_date": alert.review_date.isoformat() if alert.review_date else None,
            "estimated_loss_bdt": alert.estimated_loss_bdt,
            "priority": alert.priority,
            "status": alert.status
        }
        
        return ExplanationResponse(
            message="Alert explanation generated successfully",
            data=explanation_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Alert explanation failed: {str(e)}"
        )


@router.get("/compare/{meter_id}",
           response_model=SuccessResponse,
           summary="Compare meter with similar meters",
           description="Compare meter's consumption patterns with similar meters")
async def compare_meter_patterns(
    meter_id: str,
    comparison_count: int = 10,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Compare meter consumption patterns with similar meters"""
    try:
        logger.info(f"Comparing meter {meter_id} with similar meters")
        
        # Validate meter exists
        validate_meter_exists(meter_id, db)
        
        # Get meter information
        target_meter = db.query(Meter).filter(Meter.meter_id == meter_id).first()
        
        # Find similar meters (same category and location area)
        similar_meters_query = db.query(Meter).filter(
            Meter.meter_id != meter_id,
            Meter.customer_category == target_meter.customer_category
        )
        
        if target_meter.location:
            # Find meters in similar location (first word of location)
            location_prefix = target_meter.location.split()[0] if target_meter.location else None
            if location_prefix:
                similar_meters_query = similar_meters_query.filter(
                    Meter.location.ilike(f"{location_prefix}%")
                )
        
        similar_meters = similar_meters_query.limit(comparison_count).all()
        
        if len(similar_meters) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough similar meters found for comparison"
            )
        
        # Get consumption statistics for target meter
        target_stats = await get_meter_consumption_stats(meter_id, db)
        
        # Get consumption statistics for similar meters
        comparison_stats = []
        for meter in similar_meters:
            try:
                stats = await get_meter_consumption_stats(meter.meter_id, db)
                if stats:
                    comparison_stats.append({
                        "meter_id": meter.meter_id,
                        "location": meter.location,
                        "stats": stats
                    })
            except Exception as e:
                logger.warning(f"Failed to get stats for meter {meter.meter_id}: {e}")
                continue
        
        # Calculate comparison metrics
        if comparison_stats:
            avg_consumption = sum(s["stats"]["avg_consumption"] for s in comparison_stats) / len(comparison_stats)
            avg_variance = sum(s["stats"]["consumption_variance"] for s in comparison_stats) / len(comparison_stats)
            
            # Calculate deviations
            consumption_deviation = (target_stats["avg_consumption"] - avg_consumption) / avg_consumption * 100
            variance_deviation = (target_stats["consumption_variance"] - avg_variance) / avg_variance * 100
            
            # Determine anomaly indicators
            anomaly_indicators = []
            if abs(consumption_deviation) > 30:
                anomaly_indicators.append(f"Consumption {consumption_deviation:+.1f}% from similar meters")
            if abs(variance_deviation) > 50:
                anomaly_indicators.append(f"Consumption variability {variance_deviation:+.1f}% from similar meters")
            
            comparison_data = {
                "target_meter": {
                    "meter_id": meter_id,
                    "location": target_meter.location,
                    "category": target_meter.customer_category,
                    "stats": target_stats
                },
                "similar_meters": comparison_stats,
                "comparison_summary": {
                    "similar_meters_count": len(comparison_stats),
                    "avg_consumption_similar": avg_consumption,
                    "avg_variance_similar": avg_variance,
                    "consumption_deviation_percent": consumption_deviation,
                    "variance_deviation_percent": variance_deviation,
                    "anomaly_score": min(abs(consumption_deviation) + abs(variance_deviation), 100) / 100,
                    "anomaly_indicators": anomaly_indicators
                },
                "insights": _generate_comparison_insights(target_stats, comparison_stats, consumption_deviation, variance_deviation)
            }
        else:
            comparison_data = {
                "error": "No valid comparison data available",
                "target_meter": {
                    "meter_id": meter_id,
                    "stats": target_stats
                }
            }
        
        logger.success(f"Meter comparison completed for {meter_id}")
        
        return SuccessResponse(
            message="Meter comparison completed successfully",
            data=comparison_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in meter comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Meter comparison failed: {str(e)}"
        )


# Helper functions
async def prepare_meter_features_for_explanation(meter_id: str, db: Session) -> pd.DataFrame:
    """Prepare features for a single meter explanation"""
    try:
        # Get recent consumption data (last 90 days)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=90)
        
        consumption_records = db.query(ConsumptionData).filter(
            ConsumptionData.meter_id == meter_id,
            ConsumptionData.date >= start_date,
            ConsumptionData.date <= end_date
        ).order_by(ConsumptionData.date).all()
        
        if len(consumption_records) < 30:
            return pd.DataFrame()
        
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
        logger.error(f"Error preparing features for explanation: {e}")
        return pd.DataFrame()


async def get_meter_context(meter_id: str, db: Session) -> Dict[str, Any]:
    """Get additional context for meter explanation"""
    try:
        # Get meter info
        meter = db.query(Meter).filter(Meter.meter_id == meter_id).first()
        
        # Get recent consumption stats
        recent_date = datetime.now().date() - timedelta(days=30)
        recent_consumption = db.query(ConsumptionData).filter(
            ConsumptionData.meter_id == meter_id,
            ConsumptionData.date >= recent_date
        ).all()
        
        # Get alert history
        recent_alerts = db.query(TheftAlert).filter(
            TheftAlert.meter_id == meter_id
        ).order_by(TheftAlert.prediction_date.desc()).limit(5).all()
        
        context = {
            "meter_info": {
                "customer_id": meter.customer_id,
                "location": meter.location,
                "customer_category": meter.customer_category,
                "billing_cycle": meter.billing_cycle
            },
            "recent_consumption": {
                "days_of_data": len(recent_consumption),
                "avg_consumption": sum(r.consumption for r in recent_consumption) / len(recent_consumption) if recent_consumption else 0,
                "min_consumption": min(r.consumption for r in recent_consumption) if recent_consumption else 0,
                "max_consumption": max(r.consumption for r in recent_consumption) if recent_consumption else 0
            },
            "alert_history": {
                "total_alerts": len(recent_alerts),
                "confirmed_alerts": len([a for a in recent_alerts if a.status == 'confirmed']),
                "pending_alerts": len([a for a in recent_alerts if a.status == 'pending']),
                "latest_alert_date": recent_alerts[0].prediction_date.isoformat() if recent_alerts else None
            }
        }
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting meter context: {e}")
        return {}


async def get_meter_consumption_stats(meter_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Get consumption statistics for a meter"""
    try:
        # Get last 60 days of data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=60)
        
        consumption_records = db.query(ConsumptionData).filter(
            ConsumptionData.meter_id == meter_id,
            ConsumptionData.date >= start_date,
            ConsumptionData.date <= end_date
        ).all()
        
        if not consumption_records:
            return None
        
        consumptions = [r.consumption for r in consumption_records]
        
        return {
            "avg_consumption": sum(consumptions) / len(consumptions),
            "min_consumption": min(consumptions),
            "max_consumption": max(consumptions),
            "consumption_variance": pd.Series(consumptions).var(),
            "zero_days": len([c for c in consumptions if c == 0]),
            "days_of_data": len(consumptions)
        }
        
    except Exception as e:
        logger.error(f"Error getting consumption stats: {e}")
        return None


def _classify_risk_level(probability: float) -> str:
    """Classify theft probability into risk levels"""
    if probability >= 0.8:
        return "CRITICAL"
    elif probability >= 0.6:
        return "HIGH"
    elif probability >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"


def _generate_feature_insights(global_importance: Dict[str, Any]) -> List[str]:
    """Generate insights from global feature importance"""
    insights = []
    
    try:
        if 'feature_importance' in global_importance:
            model_based = global_importance['feature_importance'].get('model_based', {})
            if 'top_features' in model_based:
                top_features = model_based['top_features'][:5]
                insights.append(f"Top predictive features: {', '.join([f[0] for f in top_features])}")
            
            # Add category insights
            categories = global_importance.get('feature_categories', {})
            for category, features in categories.items():
                if features:
                    insights.append(f"{category.title()} features: {len(features)} features analyzed")
        
    except Exception as e:
        logger.warning(f"Error generating insights: {e}")
    
    return insights


def _generate_business_explanation_from_stored(stored_explanation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Generate business explanation from stored technical explanation"""
    try:
        # Extract key information from stored explanation
        if 'top_features' in stored_explanation:
            top_features = stored_explanation['top_features'][:3]
            key_indicators = [f"{feature.get('feature_name', 'Unknown')} affects theft risk" for feature in top_features]
            
            return {
                "key_indicators": key_indicators,
                "investigation_priorities": ["Verify meter readings", "Check for physical tampering"],
                "risk_factors": key_indicators[:2],
                "recommended_actions": ["Schedule field inspection", "Review consumption history"]
            }
    except Exception as e:
        logger.warning(f"Error generating business explanation: {e}")
    
    return None


def _generate_comparison_insights(target_stats: Dict, comparison_stats: List[Dict], consumption_dev: float, variance_dev: float) -> List[str]:
    """Generate insights from meter comparison"""
    insights = []
    
    if abs(consumption_dev) > 50:
        direction = "significantly higher" if consumption_dev > 0 else "significantly lower"
        insights.append(f"Consumption is {direction} than similar meters")
    
    if abs(variance_dev) > 100:
        direction = "much more variable" if variance_dev > 0 else "much more consistent"
        insights.append(f"Consumption pattern is {direction} than similar meters")
    
    if target_stats.get("zero_days", 0) > 5:
        insights.append("High number of zero consumption days detected")
    
    return insights