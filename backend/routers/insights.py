"""
Food Verse AI — Insights Router (Part 4)
GET /api/insights/dashboard
Provides cross-module insights combining user's history and dietary profile.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth import get_optional_user
from backend.database import get_db
from backend.models.db_models import (
    FoodAnalysisRecord,
    FreshnessReport,
    HygieneAuditRecord,
    SavedMealPlan,
    SavedRecipe,
    User,
)
from backend.services.insights_service import (
    DashboardInsightsSummary,
    unified_insights_service,
)

router = APIRouter(prefix="/api/insights", tags=["Actionable AI Insights"])


@router.get("/dashboard", response_model=DashboardInsightsSummary)
def get_dashboard_insights(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Returns an aggregated intelligence overview for the dashboard:
    combines recent scans, saved recipes, meal plans, and personalized guidance.
    Works for both authenticated users and guests.
    """
    if current_user:
        user_name = current_user.name
        user_goal = current_user.goal or "balanced"
        dietary_pref = current_user.dietary_preference or "any"

        food_count = db.query(FoodAnalysisRecord).filter(FoodAnalysisRecord.user_id == current_user.id).count()
        freshness_count = db.query(FreshnessReport).filter(FreshnessReport.user_id == current_user.id).count()
        hygiene_count = db.query(HygieneAuditRecord).filter(HygieneAuditRecord.user_id == current_user.id).count()
        recipe_count = db.query(SavedRecipe).filter(SavedRecipe.user_id == current_user.id).count()

        latest_plan = (
            db.query(SavedMealPlan)
            .filter(SavedMealPlan.user_id == current_user.id)
            .order_by(SavedMealPlan.created_at.desc())
            .first()
        )
        active_plan_name = f"{latest_plan.dietary_preference.title()} {latest_plan.duration_days}-Day Plan" if latest_plan else None
    else:
        user_name = "Guest Explorer"
        user_goal = "balanced"
        dietary_pref = "any"
        food_count = 0
        freshness_count = 0
        hygiene_count = 0
        recipe_count = 0
        active_plan_name = None

    summary = unified_insights_service.generate_dashboard_summary(
        user_name=user_name,
        user_goal=user_goal,
        dietary_pref=dietary_pref,
        recent_food_count=food_count,
        recent_freshness_count=freshness_count,
        recent_hygiene_count=hygiene_count,
        recent_recipes_count=recipe_count,
        active_plan_name=active_plan_name,
    )
    return summary
