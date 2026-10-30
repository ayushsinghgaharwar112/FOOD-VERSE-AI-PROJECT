"""
Food Verse AI — Auth Router (Part 4)
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
PUT  /api/auth/profile
POST /api/auth/logout   (client-side, stateless JWT)
"""
from __future__ import annotations

from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.orm import Session

from backend.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.database import get_db
from backend.models.db_models import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    name: str = Field(default="Food Verse User", max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    dietary_preference: Optional[str] = None
    allergies: Optional[List[str]] = None
    goal: Optional[str] = None
    preferred_cuisines: Optional[List[str]] = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    dietary_preference: str
    allergies: List[str]
    goal: str
    preferred_cuisines: List[str]
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        dietary_preference=user.dietary_preference or "any",
        allergies=user.allergies or [],
        goal=user.goal or "balanced",
        preferred_cuisines=user.preferred_cuisines or [],
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new account and return a JWT."""
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        name=req.name,
        dietary_preference="any",
        allergies=[],
        goal="balanced",
        preferred_cuisines=[],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_response(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return a JWT."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_response(user),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return _user_response(current_user)


@router.put("/profile", response_model=UserResponse)
def update_profile(
    body: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update editable profile fields."""
    if body.name is not None:
        current_user.name = body.name
    if body.dietary_preference is not None:
        current_user.dietary_preference = body.dietary_preference
    if body.allergies is not None:
        current_user.allergies = body.allergies
    if body.goal is not None:
        current_user.goal = body.goal
    if body.preferred_cuisines is not None:
        current_user.preferred_cuisines = body.preferred_cuisines
    db.commit()
    db.refresh(current_user)
    return _user_response(current_user)


@router.post("/logout")
def logout():
    """Logout is handled client-side by deleting the stored JWT."""
    return {"message": "Logged out. Please delete your local token."}
