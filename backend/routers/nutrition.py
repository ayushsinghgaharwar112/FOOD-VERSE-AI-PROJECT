from fastapi import APIRouter, HTTPException, status
from backend.models.schemas import NutritionAnalyzeRequest, NutritionAnalyzeResponse
from backend.services.nutrition_service import nutrition_service
from backend.services.ai_insights import ai_insight_service

router = APIRouter(prefix="/api/nutrition", tags=["Nutrition Intelligence"])

@router.post("/analyze", response_model=NutritionAnalyzeResponse)
def analyze_nutrition(payload: NutritionAnalyzeRequest):
    if payload.serving_size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Serving size must be greater than 0."
        )

    try:
        response = nutrition_service.calculate_nutrition(payload)
        # Augment with dynamic AI insights
        contextual = ai_insight_service.generate_contextual_insights(response)
        response.portion_advice = contextual["dynamic_portion_tip"]
        return response
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Nutrition calculation failure: {str(e)}"
        )

@router.get("/foods")
def list_available_foods():
    """Lists all verified foods available in the local nutrition database."""
    items = []
    for food_id, data in nutrition_service.database.items():
        items.append({
            "id": food_id,
            "name": data.get("name"),
            "category": data.get("category"),
            "standard_serving_name": data.get("standard_serving_name"),
            "standard_serving_grams": data.get("standard_serving_grams"),
            "calories_per_100g": data.get("per_100g", {}).get("calories"),
            "health_score": data.get("health_score"),
            "nutri_grade": data.get("nutri_grade"),
            "dietary_tags": data.get("dietary_tags", [])
        })
    return items
