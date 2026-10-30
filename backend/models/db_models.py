"""
Food Verse AI — SQLAlchemy ORM Models (Part 4)
All tables stored in food_verse.db (SQLite) or PostgreSQL.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, func,
)
from sqlalchemy.types import TypeDecorator, Text
from sqlalchemy.orm import relationship

from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ── JSON helper TypeDecorator for SQLite and PostgreSQL ──────────────────────
class JsonColumn(TypeDecorator):
    """Store Python dict/list as JSON serialized text in SQLite / Postgres."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        try:
            return json.loads(value)
        except Exception:
            return value


# ── Users ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False, default="Food Verse User")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Dietary profile (stored as JSON text)
    dietary_preference = Column(String(50), default="any")
    allergies = Column(JsonColumn, default=list)
    goal = Column(String(50), default="balanced")
    preferred_cuisines = Column(JsonColumn, default=list)

    # Relationships
    food_analyses = relationship("FoodAnalysisRecord", back_populates="user", cascade="all, delete-orphan")
    freshness_reports = relationship("FreshnessReport", back_populates="user", cascade="all, delete-orphan")
    hygiene_audits = relationship("HygieneAuditRecord", back_populates="user", cascade="all, delete-orphan")
    saved_recipes = relationship("SavedRecipe", back_populates="user", cascade="all, delete-orphan")
    meal_plans = relationship("SavedMealPlan", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistoryRecord", back_populates="user", cascade="all, delete-orphan")


# ── Food Analysis Records (Part 1) ────────────────────────────────────────────
class FoodAnalysisRecord(Base):
    __tablename__ = "food_analysis_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)

    # Recognition result
    image_filename = Column(String(255), default="")
    primary_prediction = Column(String(255), nullable=False)
    food_id = Column(String(100), nullable=False)
    confidence = Column(Float, default=0.0)
    model_tier = Column(String(100), default="")
    category = Column(String(100), default="")
    is_composite = Column(Boolean, default=False)

    # Full JSON blobs
    recognition_result = Column(JsonColumn, nullable=True)
    nutrition_result = Column(JsonColumn, nullable=True)
    insights = Column(JsonColumn, nullable=True)

    user = relationship("User", back_populates="food_analyses")


# ── Freshness Reports (Part 2) ────────────────────────────────────────────────
class FreshnessReport(Base):
    __tablename__ = "freshness_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)

    image_filename = Column(String(255), default="")
    item_name = Column(String(255), nullable=False)
    category = Column(String(100), default="")
    quality_grade = Column(String(100), nullable=False)
    confidence = Column(Float, default=0.0)
    overall_assessment = Column(String(50), default="")

    full_result = Column(JsonColumn, nullable=True)

    user = relationship("User", back_populates="freshness_reports")


# ── Hygiene Audit Records (Part 2) ────────────────────────────────────────────
class HygieneAuditRecord(Base):
    __tablename__ = "hygiene_audit_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)

    media_filename = Column(String(255), default="")
    media_type = Column(String(20), default="image")  # "image" or "video"
    overall_score = Column(Float, default=0.0)
    compliance_grade = Column(String(10), default="")
    reviewed = Column(Boolean, default=False)

    full_result = Column(JsonColumn, nullable=True)

    user = relationship("User", back_populates="hygiene_audits")


# ── Saved Recipes (Part 3) ────────────────────────────────────────────────────
class SavedRecipe(Base):
    __tablename__ = "saved_recipes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)

    recipe_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    cuisine = Column(String(100), default="")
    prep_time_minutes = Column(Integer, default=0)
    cook_time_minutes = Column(Integer, default=0)
    servings = Column(Integer, default=2)
    user_notes = Column(Text, default="")

    recipe_data = Column(JsonColumn, nullable=False)

    user = relationship("User", back_populates="saved_recipes")


# ── Saved Meal Plans (Part 3) ─────────────────────────────────────────────────
class SavedMealPlan(Base):
    __tablename__ = "saved_meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)

    plan_id = Column(String(100), nullable=False, index=True)
    duration_days = Column(Integer, default=7)
    dietary_preference = Column(String(50), default="any")
    goal = Column(String(50), default="balanced")

    plan_data = Column(JsonColumn, nullable=False)

    user = relationship("User", back_populates="meal_plans")


# ── Chat History (Part 3) ─────────────────────────────────────────────────────
class ChatHistoryRecord(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)

    role = Column(String(20), nullable=False)   # "user" | "assistant"
    content = Column(Text, nullable=False)
    recipe_id = Column(String(100), nullable=True)

    user = relationship("User", back_populates="chat_history")
