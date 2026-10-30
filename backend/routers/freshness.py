import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import settings, FRESHNESS_SAMPLES_DIR
from backend.models.schemas import FreshnessAssessmentResponse, FreshnessSampleInfo
from backend.utils.media_validator import validate_image_upload
from backend.services.freshness_service import freshness_service
from backend.auth import get_optional_user
from backend.database import get_db
from backend.models.db_models import FreshnessReport, User

router = APIRouter(prefix="/api/freshness", tags=["Food Freshness Intelligence"])

@router.post("/analyze", response_model=FreshnessAssessmentResponse)
async def analyze_food_freshness(
    image: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Evaluates visual quality indicators (browning, bruising, spots, shriveling)
    for supported fruits and vegetables. Returns quality grade, storage advice,
    and a prominent appearance-only safety limitation disclaimer.
    """
    file_bytes = await image.read()
    img, metadata = validate_image_upload(
        file_bytes=file_bytes,
        filename=image.filename or "produce_sample.jpg",
        content_type=image.content_type
    )

    try:
        assessment = freshness_service.analyze_freshness(img, filename=metadata["filename"])

        if current_user:
            try:
                report = FreshnessReport(
                    user_id=current_user.id,
                    image_filename=metadata["filename"],
                    item_name=assessment.item_name,
                    category=assessment.category,
                    quality_grade=assessment.quality_grade,
                    confidence=assessment.confidence,
                    overall_assessment=assessment.quality_grade,
                    full_result=assessment.model_dump(),
                )
                db.add(report)
                db.commit()
            except Exception:
                db.rollback()

        return assessment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Freshness analysis failure: {str(e)}"
        )

@router.get("/samples", response_model=list[FreshnessSampleInfo])
def get_freshness_samples():
    """Returns curated sample produce images for immediate 1-click testing."""
    samples = [
        {
            "id": "fresh-apple-1",
            "title": "Honeycrisp Apple",
            "subtitle": "Optimal firmness, smooth skin, zero surface browning",
            "filename": "fresh_apple.jpg",
            "image_url": "/api/freshness/samples/fresh_apple.jpg",
            "item_name": "Apple",
            "expected_grade": "Fresh / Optimal Quality"
        },
        {
            "id": "bruised-banana-1",
            "title": "Cavendish Banana",
            "subtitle": "Moderate sugar spots & superficial impact softening",
            "filename": "bruised_banana.jpg",
            "image_url": "/api/freshness/samples/bruised_banana.jpg",
            "item_name": "Banana",
            "expected_grade": "Moderately Fresh / Consume Soon"
        },
        {
            "id": "stale-tomato-1",
            "title": "Vine Tomato",
            "subtitle": "Severe surface wrinkling, browning lesions & loss of turgor",
            "filename": "stale_tomato.jpg",
            "image_url": "/api/freshness/samples/stale_tomato.jpg",
            "item_name": "Tomato",
            "expected_grade": "Visibly Degraded / Stale"
        },
        {
            "id": "uncertain-greens-1",
            "title": "Salad Greens (Blurred)",
            "subtitle": "Low-contrast/blurry capture triggering insufficient evidence",
            "filename": "uncertain_greens.jpg",
            "image_url": "/api/freshness/samples/uncertain_greens.jpg",
            "item_name": "Leafy Greens",
            "expected_grade": "Uncertain / Insufficient Evidence"
        }
    ]
    return samples

@router.get("/samples/{filename}")
def get_freshness_sample_file(filename: str):
    file_path = FRESHNESS_SAMPLES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Freshness sample file not found.")
    return FileResponse(file_path, media_type="image/jpeg")
