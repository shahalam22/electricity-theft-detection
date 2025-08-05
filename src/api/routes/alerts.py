from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from loguru import logger

from src.config.database import get_db
from src.database.models import TheftAlert, Meter, ConsumptionData
from src.api.models.request_models import AlertUpdate, AlertQuery
from src.api.models.response_models import (
    SuccessResponse, AlertListResponse, AlertUpdateResponse, 
    TheftAlert as TheftAlertResponse, RiskLevel, DashboardResponse,
    MetricCard, DashboardSummary, ChartData
)
from src.api.dependencies import (
    get_current_user, check_rate_limit, validate_alert_exists,
    require_admin, get_cache, CacheManager
)


router = APIRouter(prefix="/alerts", tags=["Alert Management"])


def format_alert_response(alert: TheftAlert, include_meter_info: bool = True) -> Dict[str, Any]:
    """Format alert for API response"""
    alert_data = {
        "id": alert.id,
        "meter_id": alert.meter_id,
        "prediction_date": alert.prediction_date,
        "theft_probability": alert.theft_probability,
        "risk_level": _classify_risk_level(alert.theft_probability),
        "status": alert.status,
        "priority": alert.priority,
        "created_at": alert.created_at,
        "reviewed_by": alert.reviewed_by,
        "review_date": alert.review_date,
        "estimated_loss_bdt": alert.estimated_loss_bdt
    }
    
    # Add meter information if requested
    if include_meter_info and alert.meter:
        alert_data.update({
            "customer_id": alert.meter.customer_id,
            "location": alert.meter.location,
            "customer_category": alert.meter.customer_category
        })
    
    # Add explanation summary
    if alert.features_explanation:
        try:
            # Extract key points from explanation
            explanation_summary = []
            if isinstance(alert.features_explanation, dict):
                top_features = alert.features_explanation.get('top_features', [])[:3]
                for feature in top_features:
                    feature_name = feature.get('feature_name', 'Unknown')
                    contribution = feature.get('shap_value', 0)
                    direction = "increases" if contribution > 0 else "decreases"
                    explanation_summary.append(f"{feature_name} {direction} theft risk")
            
            alert_data["explanation_summary"] = explanation_summary
        except:
            alert_data["explanation_summary"] = []
    
    return alert_data


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


@router.get("/",
           response_model=AlertListResponse,
           summary="List theft alerts",
           description="Retrieve theft alerts with filtering and pagination")
async def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status (pending, confirmed, rejected)"),
    priority: Optional[str] = Query(None, description="Filter by priority (high, medium, low)"),
    date_from: Optional[date] = Query(None, description="Filter alerts from date"),
    date_to: Optional[date] = Query(None, description="Filter alerts to date"),
    meter_id: Optional[str] = Query(None, description="Filter by meter ID"),
    location: Optional[str] = Query(None, description="Filter by location"),
    min_probability: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum theft probability"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db),
    cache: CacheManager = Depends(get_cache),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(check_rate_limit)
):
    """List theft alerts with filtering and pagination"""
    try:
        logger.info(f"Listing alerts with filters - status: {status}, priority: {priority}")
        
        # Build cache key
        cache_key = f"alerts_list_{status}_{priority}_{date_from}_{date_to}_{meter_id}_{location}_{min_probability}_{page}_{size}_{sort_by}_{sort_order}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return AlertListResponse(
                message="Alerts retrieved from cache",
                data=cached_result
            )
        
        # Build query
        query = db.query(TheftAlert).join(Meter, TheftAlert.meter_id == Meter.meter_id)
        
        # Apply filters
        if status:
            query = query.filter(TheftAlert.status == status)
        if priority:
            query = query.filter(TheftAlert.priority == priority)
        if date_from:
            query = query.filter(TheftAlert.prediction_date >= date_from)
        if date_to:
            query = query.filter(TheftAlert.prediction_date <= date_to)
        if meter_id:
            query = query.filter(TheftAlert.meter_id == meter_id)
        if location:
            query = query.filter(Meter.location.ilike(f"%{location}%"))
        if min_probability:
            query = query.filter(TheftAlert.theft_probability >= min_probability)
        
        # Apply sorting
        sort_column = getattr(TheftAlert, sort_by, TheftAlert.created_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        alerts = query.offset(offset).limit(size).all()
        
        # Format alerts
        alerts_data = [format_alert_response(alert) for alert in alerts]
        
        # Calculate pagination metadata
        total_pages = (total_count + size - 1) // size
        has_next = page < total_pages
        has_prev = page > 1
        
        # Get summary statistics
        summary_stats = db.query(
            TheftAlert.status,
            TheftAlert.priority
        ).all()
        
        status_counts = {}
        priority_counts = {}
        for stat in summary_stats:
            status_counts[stat.status] = status_counts.get(stat.status, 0) + 1
            priority_counts[stat.priority] = priority_counts.get(stat.priority, 0) + 1
        
        result_data = {
            "alerts": alerts_data,
            "pagination": {
                "total_count": total_count,
                "page": page,
                "page_size": size,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            },
            "summary": {
                "pending_alerts": status_counts.get("pending", 0),
                "confirmed_alerts": status_counts.get("confirmed", 0),
                "rejected_alerts": status_counts.get("rejected", 0),
                "high_priority": priority_counts.get("high", 0)
            }
        }
        
        # Cache result
        cache.set(cache_key, result_data, ttl=60)  # Cache for 1 minute
        
        logger.success(f"Retrieved {len(alerts_data)} alerts (total: {total_count})")
        
        return AlertListResponse(
            message="Alerts retrieved successfully",
            data=result_data
        )
        
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alerts: {str(e)}"
        )


@router.get("/{alert_id}",
           response_model=SuccessResponse,
           summary="Get alert details",
           description="Get detailed information about a specific alert")
async def get_alert_details(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed information about a specific alert"""
    try:
        # Validate alert exists
        alert = validate_alert_exists(alert_id, db)
        
        # Get detailed alert information
        alert_data = format_alert_response(alert, include_meter_info=True)
        
        # Get recent consumption data for context
        recent_consumption = db.query(ConsumptionData).filter(
            ConsumptionData.meter_id == alert.meter_id,
            ConsumptionData.date >= alert.prediction_date - timedelta(days=30),
            ConsumptionData.date <= alert.prediction_date
        ).order_by(ConsumptionData.date.desc()).limit(30).all()
        
        consumption_data = [
            {
                "date": record.date.isoformat(),
                "consumption": record.consumption
            }
            for record in recent_consumption
        ]
        
        # Add consumption context
        alert_data["recent_consumption"] = consumption_data
        alert_data["consumption_stats"] = {
            "avg_consumption": sum(r.consumption for r in recent_consumption) / len(recent_consumption) if recent_consumption else 0,
            "max_consumption": max(r.consumption for r in recent_consumption) if recent_consumption else 0,
            "min_consumption": min(r.consumption for r in recent_consumption) if recent_consumption else 0,
            "days_of_data": len(recent_consumption)
        }
        
        return SuccessResponse(
            message="Alert details retrieved successfully",
            data=alert_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert details: {str(e)}"
        )


@router.put("/{alert_id}",
           response_model=AlertUpdateResponse,
           summary="Update alert status",
           description="Update the status of a theft alert (confirm, reject, etc.)")
async def update_alert_status(
    alert_id: int,
    update_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(check_rate_limit)
):
    """Update alert status"""
    try:
        logger.info(f"Updating alert {alert_id} to status {update_data.status}")
        
        # Validate alert exists
        alert = validate_alert_exists(alert_id, db)
        
        # Update alert
        alert.status = update_data.status
        alert.reviewed_by = update_data.reviewed_by or current_user.get('user_id')
        alert.review_date = datetime.now()
        
        # Add notes if provided (would need to add notes field to model)
        # alert.notes = update_data.notes
        
        db.commit()
        db.refresh(alert)
        
        # Format response
        alert_data = format_alert_response(alert)
        
        logger.success(f"Alert {alert_id} updated to status {update_data.status}")
        
        return AlertUpdateResponse(
            message="Alert updated successfully",
            data=TheftAlertResponse(**alert_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update alert: {str(e)}"
        )


@router.post("/{alert_id}/confirm",
            response_model=AlertUpdateResponse,
            summary="Confirm theft alert",
            description="Confirm that an alert represents actual theft")
async def confirm_alert(
    alert_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(check_rate_limit)
):
    """Confirm theft alert"""
    try:
        logger.info(f"Confirming alert {alert_id}")
        
        # Validate alert exists
        alert = validate_alert_exists(alert_id, db)
        
        # Update alert status
        alert.status = "confirmed"
        alert.reviewed_by = current_user.get('user_id')
        alert.review_date = datetime.now()
        
        db.commit()
        db.refresh(alert)
        
        # Format response
        alert_data = format_alert_response(alert)
        
        logger.success(f"Alert {alert_id} confirmed")
        
        return AlertUpdateResponse(
            message="Alert confirmed successfully",
            data=TheftAlertResponse(**alert_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error confirming alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to confirm alert: {str(e)}"
        )


@router.post("/{alert_id}/reject",
            response_model=AlertUpdateResponse,
            summary="Reject theft alert",
            description="Reject an alert as false positive")
async def reject_alert(
    alert_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    _: bool = Depends(check_rate_limit)
):
    """Reject theft alert as false positive"""
    try:
        logger.info(f"Rejecting alert {alert_id}")
        
        # Validate alert exists
        alert = validate_alert_exists(alert_id, db)
        
        # Update alert status
        alert.status = "rejected"
        alert.reviewed_by = current_user.get('user_id')
        alert.review_date = datetime.now()
        
        db.commit()
        db.refresh(alert)
        
        # Format response
        alert_data = format_alert_response(alert)
        
        logger.success(f"Alert {alert_id} rejected")
        
        return AlertUpdateResponse(
            message="Alert rejected successfully",
            data=TheftAlertResponse(**alert_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject alert: {str(e)}"
        )


@router.get("/dashboard/summary",
           response_model=DashboardResponse,
           summary="Get dashboard summary",
           description="Get summary statistics for alerts dashboard")
async def get_dashboard_summary(
    date_from: Optional[date] = Query(None, description="Start date for metrics"),
    date_to: Optional[date] = Query(None, description="End date for metrics"),
    location_filter: Optional[str] = Query(None, description="Filter by location"),
    db: Session = Depends(get_db),
    cache: CacheManager = Depends(get_cache),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get dashboard summary statistics"""
    try:
        logger.info("Generating dashboard summary")
        
        # Set default date range if not provided
        if not date_to:
            date_to = datetime.now().date()
        if not date_from:
            date_from = date_to - timedelta(days=30)
        
        # Check cache
        cache_key = f"dashboard_summary_{date_from}_{date_to}_{location_filter}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return DashboardResponse(
                message="Dashboard summary retrieved from cache",
                data=cached_result
            )
        
        # Build base queries
        alerts_query = db.query(TheftAlert).join(Meter, TheftAlert.meter_id == Meter.meter_id)
        if location_filter:
            alerts_query = alerts_query.filter(Meter.location.ilike(f"%{location_filter}%"))
        
        # Get total counts
        total_meters = db.query(Meter).count()
        total_alerts = alerts_query.count()
        
        # Get alerts in date range
        date_filtered_alerts = alerts_query.filter(
            TheftAlert.prediction_date >= date_from,
            TheftAlert.prediction_date <= date_to
        )
        
        # Status counts
        pending_alerts = date_filtered_alerts.filter(TheftAlert.status == 'pending').count()
        confirmed_alerts = date_filtered_alerts.filter(TheftAlert.status == 'confirmed').count()
        rejected_alerts = date_filtered_alerts.filter(TheftAlert.status == 'rejected').count()
        
        # Calculate metrics
        total_reviewed = confirmed_alerts + rejected_alerts
        detection_rate = confirmed_alerts / total_reviewed if total_reviewed > 0 else 0
        false_positive_rate = rejected_alerts / total_reviewed if total_reviewed > 0 else 0
        
        # Estimated savings calculation
        confirmed_alerts_data = date_filtered_alerts.filter(TheftAlert.status == 'confirmed').all()
        estimated_savings = sum(alert.estimated_loss_bdt or 0 for alert in confirmed_alerts_data)
        
        # Time-based metrics
        today = datetime.now().date()
        alerts_today = alerts_query.filter(TheftAlert.prediction_date == today).count()
        
        week_ago = today - timedelta(days=7)
        alerts_this_week = alerts_query.filter(TheftAlert.prediction_date >= week_ago).count()
        
        month_ago = today - timedelta(days=30)
        alerts_this_month = alerts_query.filter(TheftAlert.prediction_date >= month_ago).count()
        
        # Create summary
        summary = DashboardSummary(
            total_meters=total_meters,
            total_alerts=total_alerts,
            pending_alerts=pending_alerts,
            confirmed_thefts=confirmed_alerts,
            false_positives=rejected_alerts,
            detection_rate=detection_rate,
            false_positive_rate=false_positive_rate,
            estimated_savings_bdt=estimated_savings,
            alerts_today=alerts_today,
            alerts_this_week=alerts_this_week,
            alerts_this_month=alerts_this_month
        )
        
        # Create metric cards
        metric_cards = [
            MetricCard(
                title="Active Alerts",
                value=pending_alerts,
                change=None,
                change_type="neutral",
                format_type="number",
                description="Alerts awaiting review"
            ),
            MetricCard(
                title="Detection Rate",
                value=f"{detection_rate:.1%}",
                change=None,
                change_type="positive" if detection_rate > 0.7 else "negative",
                format_type="percentage",
                description="Confirmed thefts / Total reviewed"
            ),
            MetricCard(
                title="Estimated Savings",
                value=f"{estimated_savings:,.0f}",
                change=None,
                change_type="positive",
                format_type="currency",
                description="BDT saved from prevented theft"
            ),
            MetricCard(
                title="False Positive Rate",
                value=f"{false_positive_rate:.1%}",
                change=None,
                change_type="negative" if false_positive_rate > 0.2 else "positive",
                format_type="percentage",
                description="Rejected alerts / Total reviewed"
            )
        ]
        
        # Create charts data (simplified)
        # Alert trend chart
        alert_trend_chart = ChartData(
            chart_type="line",
            title="Alert Trend (Last 7 Days)",
            labels=[],
            datasets=[],
            options={}
        )
        
        # Status distribution chart
        status_chart = ChartData(
            chart_type="pie",
            title="Alert Status Distribution",
            labels=["Pending", "Confirmed", "Rejected"],
            datasets=[{
                "data": [pending_alerts, confirmed_alerts, rejected_alerts],
                "backgroundColor": ["#fbbf24", "#10b981", "#ef4444"]
            }]
        )
        
        dashboard_data = {
            "summary": summary.dict(),
            "metric_cards": [card.dict() for card in metric_cards],
            "charts": [status_chart.dict()],
            "date_range": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            }
        }
        
        # Cache result
        cache.set(cache_key, dashboard_data, ttl=300)  # Cache for 5 minutes
        
        logger.success("Dashboard summary generated successfully")
        
        return DashboardResponse(
            message="Dashboard summary retrieved successfully",
            data=dashboard_data
        )
        
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard summary: {str(e)}"
        )


@router.delete("/{alert_id}",
              summary="Delete alert",
              description="Delete a theft alert (admin only)")
async def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_admin),
    _: bool = Depends(check_rate_limit)
):
    """Delete a theft alert (admin only)"""
    try:
        logger.info(f"Deleting alert {alert_id}")
        
        # Validate alert exists
        alert = validate_alert_exists(alert_id, db)
        
        # Delete alert
        db.delete(alert)
        db.commit()
        
        logger.success(f"Alert {alert_id} deleted successfully")
        
        return SuccessResponse(
            message="Alert deleted successfully",
            data={"alert_id": alert_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete alert: {str(e)}"
        )