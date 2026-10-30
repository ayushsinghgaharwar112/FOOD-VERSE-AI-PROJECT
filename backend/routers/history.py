"""
Food Verse AI — History Router (Part 4)
User-scoped paginated access to all analysis records, with delete.

GET  /api/history/food             — food analysis records
GET  /api/history/freshness        — freshness reports
GET  /api/history/hygiene          — hygiene audits
GET  /api/history/recipes          — saved recipes
GET  /api/history/meal-plans       — saved meal plans
GET  /api/history/chat/{session}   — chat history by session
GET  /api/history/dashboard        — summary stats

DELETE /api/history/{record_type}/{id}
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models.db_models import (
    ChatHistoryRecord,
    FoodAnalysisRecord,
    FreshnessReport,
    HygieneAuditRecord,
    SavedMealPlan,
    SavedRecipe,
    User,
)

router = APIRouter(prefix="/api/history", tags=["History"])

# ── helpers ───────────────────────────────────────────────────────────────────
RECORD_TYPE_MAP = {
    "food": FoodAnalysisRecord,
    "freshness": FreshnessReport,
    "hygiene": HygieneAuditRecord,
    "recipes": SavedRecipe,
    "meal-plans": SavedMealPlan,
    "chat": ChatHistoryRecord,
}


class PaginatedResponse(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


def _paginate(query, page: int, page_size: int) -> tuple:
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = max(1, (total + page_size - 1) // page_size)
    return items, total, total_pages


# ── Food analysis history ─────────────────────────────────────────────────────
@router.get("/food", response_model=PaginatedResponse)
def food_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(FoodAnalysisRecord)
        .filter(FoodAnalysisRecord.user_id == current_user.id)
        .order_by(FoodAnalysisRecord.created_at.desc())
    )
    rows, total, total_pages = _paginate(q, page, page_size)
    items = [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "primary_prediction": r.primary_prediction,
            "food_id": r.food_id,
            "confidence": r.confidence,
            "model_tier": r.model_tier,
            "category": r.category,
            "is_composite": r.is_composite,
            "recognition_result": r.recognition_result,
            "nutrition_result": r.nutrition_result,
            "insights": r.insights,
        }
        for r in rows
    ]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


# ── Freshness history ─────────────────────────────────────────────────────────
@router.get("/freshness", response_model=PaginatedResponse)
def freshness_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(FreshnessReport)
        .filter(FreshnessReport.user_id == current_user.id)
        .order_by(FreshnessReport.created_at.desc())
    )
    rows, total, total_pages = _paginate(q, page, page_size)
    items = [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "item_name": r.item_name,
            "category": r.category,
            "quality_grade": r.quality_grade,
            "confidence": r.confidence,
            "overall_assessment": r.overall_assessment,
            "full_result": r.full_result,
        }
        for r in rows
    ]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


# ── Hygiene history ───────────────────────────────────────────────────────────
@router.get("/hygiene", response_model=PaginatedResponse)
def hygiene_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(HygieneAuditRecord)
        .filter(HygieneAuditRecord.user_id == current_user.id)
        .order_by(HygieneAuditRecord.created_at.desc())
    )
    rows, total, total_pages = _paginate(q, page, page_size)
    items = [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "media_filename": r.media_filename,
            "media_type": r.media_type,
            "overall_score": r.overall_score,
            "compliance_grade": r.compliance_grade,
            "reviewed": r.reviewed,
            "full_result": r.full_result,
        }
        for r in rows
    ]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


# ── Recipes history ────────────────────────────────────────────────────────────
@router.get("/recipes", response_model=PaginatedResponse)
def recipes_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(SavedRecipe)
        .filter(SavedRecipe.user_id == current_user.id)
        .order_by(SavedRecipe.created_at.desc())
    )
    rows, total, total_pages = _paginate(q, page, page_size)
    items = [
        {
            "id": r.id,
            "recipe_id": r.recipe_id,
            "title": r.title,
            "cuisine": r.cuisine,
            "prep_time_minutes": r.prep_time_minutes,
            "cook_time_minutes": r.cook_time_minutes,
            "servings": r.servings,
            "user_notes": r.user_notes,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "recipe_data": r.recipe_data,
        }
        for r in rows
    ]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


# ── Meal plans history ────────────────────────────────────────────────────────
@router.get("/meal-plans", response_model=PaginatedResponse)
def meal_plans_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(SavedMealPlan)
        .filter(SavedMealPlan.user_id == current_user.id)
        .order_by(SavedMealPlan.created_at.desc())
    )
    rows, total, total_pages = _paginate(q, page, page_size)
    items = [
        {
            "id": r.id,
            "plan_id": r.plan_id,
            "duration_days": r.duration_days,
            "dietary_preference": r.dietary_preference,
            "goal": r.goal,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "plan_data": r.plan_data,
        }
        for r in rows
    ]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


# ── Chat history ──────────────────────────────────────────────────────────────
@router.get("/chat/{session_id}")
def chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ChatHistoryRecord)
        .filter(
            ChatHistoryRecord.user_id == current_user.id,
            ChatHistoryRecord.session_id == session_id,
        )
        .order_by(ChatHistoryRecord.created_at.asc())
        .all()
    )
    return {
        "session_id": session_id,
        "messages": [
            {
                "id": r.id,
                "role": r.role,
                "content": r.content,
                "recipe_id": r.recipe_id,
                "created_at": r.created_at.isoformat() if r.created_at else "",
            }
            for r in rows
        ],
    }


# ── Dashboard summary ─────────────────────────────────────────────────────────
@router.get("/dashboard")
def history_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    food_count = db.query(FoodAnalysisRecord).filter(FoodAnalysisRecord.user_id == current_user.id).count()
    freshness_count = db.query(FreshnessReport).filter(FreshnessReport.user_id == current_user.id).count()
    hygiene_count = db.query(HygieneAuditRecord).filter(HygieneAuditRecord.user_id == current_user.id).count()
    recipe_count = db.query(SavedRecipe).filter(SavedRecipe.user_id == current_user.id).count()
    plan_count = db.query(SavedMealPlan).filter(SavedMealPlan.user_id == current_user.id).count()

    # Most recent food analysis
    last_food = (
        db.query(FoodAnalysisRecord)
        .filter(FoodAnalysisRecord.user_id == current_user.id)
        .order_by(FoodAnalysisRecord.created_at.desc())
        .first()
    )
    last_food_data = None
    if last_food:
        last_food_data = {
            "prediction": last_food.primary_prediction,
            "confidence": last_food.confidence,
            "created_at": last_food.created_at.isoformat() if last_food.created_at else "",
        }

    return {
        "user_name": current_user.name,
        "total_food_analyses": food_count,
        "total_freshness_checks": freshness_count,
        "total_hygiene_audits": hygiene_count,
        "total_saved_recipes": recipe_count,
        "total_meal_plans": plan_count,
        "last_food_analysis": last_food_data,
    }


# ── Delete record ─────────────────────────────────────────────────────────────
@router.delete("/{record_type}/{record_id}")
def delete_record(
    record_type: str,
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    model = RECORD_TYPE_MAP.get(record_type)
    if not model:
        raise HTTPException(status_code=404, detail=f"Unknown record type: {record_type}")

    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    if getattr(record, "user_id", None) != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this record.")

    db.delete(record)
    db.commit()
    return {"deleted": True, "record_type": record_type, "id": record_id}
