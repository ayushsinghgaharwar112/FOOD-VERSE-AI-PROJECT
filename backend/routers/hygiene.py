import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import settings, HYGIENE_SAMPLES_DIR
from backend.models.schemas import (
    HygieneAuditResponse,
    HygieneSampleInfo,
    ReviewChecklistItem,
    ReviewUpdateRequest
)
from backend.utils.media_validator import validate_image_upload, validate_video_upload
from backend.services.hygiene_service import hygiene_service
from backend.auth import get_optional_user
from backend.database import get_db
from backend.models.db_models import HygieneAuditRecord, User

router = APIRouter(prefix="/api/hygiene", tags=["Restaurant Hygiene & Sanitation Monitoring"])

@router.post("/analyze-image", response_model=HygieneAuditResponse)
async def analyze_kitchen_image(
    image: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Evaluates restaurant kitchen image for visible hygiene conditions:
    uncovered food, clutter, food/waste proximity, and protective gear.
    """
    file_bytes = await image.read()
    img, metadata = validate_image_upload(
        file_bytes=file_bytes,
        filename=image.filename or "kitchen_scene.jpg",
        content_type=image.content_type
    )

    try:
        audit = hygiene_service.analyze_image(img, filename=metadata["filename"])

        if current_user:
            try:
                record = HygieneAuditRecord(
                    user_id=current_user.id,
                    media_filename=metadata["filename"],
                    media_type="image",
                    overall_score=audit.overall_score,
                    compliance_grade=audit.compliance_grade,
                    reviewed=False,
                    full_result=audit.model_dump(),
                )
                db.add(record)
                db.commit()
            except Exception:
                db.rollback()

        return audit
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hygiene image analysis failed: {str(e)}"
        )

@router.post("/analyze-video", response_model=HygieneAuditResponse)
async def analyze_kitchen_video(
    video: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Extracts frames at configured intervals from short kitchen clips (<=30s),
    running multi-frame temporal sanitation audit. Safely deletes temporary
    video files upon completion.
    """
    file_bytes = await video.read()
    tmp_path, metadata = validate_video_upload(
        file_bytes=file_bytes,
        filename=video.filename or "kitchen_clip.mp4",
        content_type=video.content_type
    )

    try:
        audit = hygiene_service.analyze_video(
            tmp_video_path=tmp_path,
            filename=metadata["filename"],
            duration_sec=metadata["duration_seconds"]
        )

        if current_user:
            try:
                record = HygieneAuditRecord(
                    user_id=current_user.id,
                    media_filename=metadata["filename"],
                    media_type="video",
                    overall_score=audit.overall_score,
                    compliance_grade=audit.compliance_grade,
                    reviewed=False,
                    full_result=audit.model_dump(),
                )
                db.add(record)
                db.commit()
            except Exception:
                db.rollback()

        return audit
    except Exception as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hygiene video processing failed: {str(e)}"
        )

@router.get("/jobs/{job_id}", response_model=HygieneAuditResponse)
def get_hygiene_job_status(job_id: str):
    """Retrieves results of a previously processed kitchen audit."""
    audit = hygiene_service._audit_registry.get(job_id)
    if not audit:
        raise HTTPException(status_code=404, detail=f"Audit job '{job_id}' not found.")
    return audit

@router.post("/reviews/{item_id}", response_model=ReviewChecklistItem)
def update_checklist_item_review(
    item_id: str,
    payload: ReviewUpdateRequest,
    audit_id: Optional[str] = Query(default="")
):
    """
    Allows an authorized sanitation reviewer to mark findings as
    'Approved' or 'Flagged' with persistent audit tracking.
    """
    try:
        updated_item = hygiene_service.update_checklist_review(
            audit_id=audit_id or "",
            item_id=item_id,
            req=payload
        )
        return updated_item
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/samples", response_model=list[HygieneSampleInfo])
def get_hygiene_samples():
    """Provides sample kitchen images and video for immediate 1-click testing."""
    samples = [
        {
            "id": "hygiene-clean-1",
            "title": "Compliant Kitchen Line",
            "subtitle": "Sealed pans, organized boards, distant waste disposal, protective gloves",
            "filename": "clean_kitchen.jpg",
            "media_url": "/api/hygiene/samples/clean_kitchen.jpg",
            "media_type": "image",
            "expected_rating": "Grade A (Compliant)"
        },
        {
            "id": "hygiene-violation-1",
            "title": "Violations Observed Station",
            "subtitle": "Uncovered ingredients, counter spill, open waste bin adjacent to board",
            "filename": "violation_kitchen.jpg",
            "media_url": "/api/hygiene/samples/violation_kitchen.jpg",
            "media_type": "image",
            "expected_rating": "Grade C / Action Required"
        },
        {
            "id": "hygiene-video-clip-1",
            "title": "Active Prep Station Clip",
            "subtitle": "3-second multi-frame video stream with dynamic timeline frame extraction",
            "filename": "kitchen_prep_clip.mp4",
            "media_url": "/api/hygiene/samples/kitchen_prep_clip.mp4",
            "media_type": "video",
            "expected_rating": "Temporal Video Audit"
        }
    ]
    return samples

@router.get("/samples/{filename}")
def get_hygiene_sample_file(filename: str):
    file_path = HYGIENE_SAMPLES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Hygiene sample file not found.")
    
    media_type = "video/mp4" if filename.endswith(".mp4") else "image/jpeg"
    return FileResponse(file_path, media_type=media_type)
