from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from backend.models.schemas import (
    MealPlanGenerateRequest,
    MealPlanResponse
)
from backend.services.meal_planner_service import meal_planner_service
from backend.auth import get_optional_user
from backend.database import get_db
from backend.models.db_models import SavedMealPlan, User

router = APIRouter(prefix="/api/meal-plans", tags=["Personalized Meal Planner"])

@router.post("/generate", response_model=MealPlanResponse)
def generate_meal_plan(payload: MealPlanGenerateRequest):
    """
    Generates a personalized daily or 7-day meal plan based on profile
    goals, dietary preferences, and allergies. Compiles consolidated grocery list.
    """
    try:
        plan = meal_planner_service.generate_meal_plan(payload)
        return plan
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Meal plan generation error: {str(e)}"
        )

@router.get("", response_model=List[Dict[str, Any]])
def list_saved_meal_plans(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Returns previously generated or saved meal plans."""
    if current_user:
        db_plans = (
            db.query(SavedMealPlan)
            .filter(SavedMealPlan.user_id == current_user.id)
            .order_by(SavedMealPlan.created_at.desc())
            .all()
        )
        if db_plans:
            return [
                {
                    "plan_id": p.plan_id,
                    "duration_days": p.duration_days,
                    "dietary_preference": p.dietary_preference,
                    "goal": p.goal,
                    "created_at": p.created_at.isoformat() if p.created_at else "",
                    "plan_data": p.plan_data,
                }
                for p in db_plans
            ]
    return meal_planner_service.get_saved_mealplans()

@router.get("/{plan_id}", response_model=Dict[str, Any])
def get_meal_plan(
    plan_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Fetches a specific meal plan by its unique identifier."""
    if current_user:
        db_plan = (
            db.query(SavedMealPlan)
            .filter(SavedMealPlan.user_id == current_user.id, SavedMealPlan.plan_id == plan_id)
            .first()
        )
        if db_plan:
            return db_plan.plan_data

    plans = meal_planner_service.get_saved_mealplans()
    for p in plans:
        if p.get("plan_id") == plan_id:
            return p
    raise HTTPException(status_code=404, detail=f"Meal plan '{plan_id}' not found.")

@router.post("/save")
def save_meal_plan(
    payload: MealPlanResponse,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Persists a modified or reviewed meal plan."""
    try:
        if current_user:
            rec = SavedMealPlan(
                user_id=current_user.id,
                plan_id=payload.plan_id,
                duration_days=payload.duration_days,
                dietary_preference=payload.profile.dietary_preference,
                goal=payload.profile.goal,
                plan_data=payload.model_dump(),
            )
            db.add(rec)
            db.commit()
            return {"status": "saved", "plan_id": payload.plan_id}

        saved = meal_planner_service.save_mealplan(payload)
        return {"status": "saved", "plan_id": saved["plan_id"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save meal plan: {str(e)}"
        )
