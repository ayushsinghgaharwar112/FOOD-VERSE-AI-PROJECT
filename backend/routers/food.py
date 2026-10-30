import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.config import settings, SAMPLE_IMAGES_DIR
from backend.models.schemas import FoodRecognitionResponse, SampleImageInfo
from backend.services.food_classifier import food_classifier_service
from backend.services.nutrition_service import nutrition_service
from backend.auth import get_optional_user
from backend.database import get_db
from backend.models.db_models import FoodAnalysisRecord, User

router = APIRouter(prefix="/api/food", tags=["Food Recognition"])

@router.post("/recognize", response_model=FoodRecognitionResponse)
async def recognize_food(
    image: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    # Validate content type
    content_type = image.content_type or ""
    if content_type.lower() not in settings.ALLOWED_IMAGE_TYPES:
        ext = os.path.splitext(image.filename or "")[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{content_type}'. Allowed formats are JPEG, PNG, and WebP."
            )

    # Read bytes and check size
    file_bytes = await image.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image file is empty."
        )

    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB."
        )

    try:
        recognition = food_classifier_service.classify_image(
            file_bytes=file_bytes,
            filename=image.filename or "uploaded_food.jpg",
            nutrition_db=nutrition_service.database
        )

        # If user is authenticated, save record to history database
        if current_user:
            try:
                record = FoodAnalysisRecord(
                    user_id=current_user.id,
                    image_filename=image.filename or "uploaded_food.jpg",
                    primary_prediction=recognition.primary_prediction,
                    food_id=recognition.food_id,
                    confidence=recognition.confidence,
                    model_tier=recognition.model_tier,
                    category=recognition.category,
                    is_composite=recognition.is_composite,
                    recognition_result=recognition.model_dump(),
                )
                db.add(record)
                db.commit()
            except Exception:
                db.rollback()

        return recognition
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal recognition error: {str(e)}"
        )

@router.get("/samples", response_model=list[SampleImageInfo])
def get_sample_images():
    """Provides curated sample test images that users can click to instantly test recognition."""
    samples = [
        {
            "id": "sample-1",
            "title": "Avocado Toast",
            "subtitle": "Whole wheat sourdough with smashed avocado",
            "filename": "avocado_toast.jpg",
            "image_url": "/api/food/samples/avocado_toast.jpg",
            "food_id": "avocado_toast"
        },
        {
            "id": "sample-2",
            "title": "Grilled Salmon Bowl",
            "subtitle": "Salmon fillet with brown rice and broccoli",
            "filename": "grilled_salmon.jpg",
            "image_url": "/api/food/samples/grilled_salmon.jpg",
            "food_id": "grilled_salmon"
        },
        {
            "id": "sample-3",
            "title": "Margherita Pizza",
            "subtitle": "Wood-fired crust with mozzarella and basil",
            "filename": "margherita_pizza.jpg",
            "image_url": "/api/food/samples/margherita_pizza.jpg",
            "food_id": "margherita_pizza"
        },
        {
            "id": "sample-4",
            "title": "Berry Oatmeal Bowl",
            "subtitle": "Rolled oats with fresh berries and seeds",
            "filename": "berry_oatmeal.jpg",
            "image_url": "/api/food/samples/berry_oatmeal.jpg",
            "food_id": "berry_oatmeal"
        },
        {
            "id": "sample-5",
            "title": "Chicken Caesar Salad",
            "subtitle": "Romaine lettuce, chicken breast and parmesan",
            "filename": "chicken_caesar_salad.jpg",
            "image_url": "/api/food/samples/chicken_caesar_salad.jpg",
            "food_id": "chicken_caesar_salad"
        },
        {
            "id": "sample-6",
            "title": "Chocolate Fudge Cake",
            "subtitle": "Decadent dark chocolate sponge with frosting",
            "filename": "chocolate_cake.jpg",
            "image_url": "/api/food/samples/chocolate_cake.jpg",
            "food_id": "chocolate_cake"
        }
    ]
    return samples

@router.get("/samples/{filename}")
def get_sample_image_file(filename: str):
    file_path = SAMPLE_IMAGES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sample image not found.")
    return FileResponse(file_path, media_type="image/jpeg")
