import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.gemini_service import gemini_service
from backend.services.usda_service import usda_service
from backend.services.food_classifier import food_classifier_service
from backend.services.nutrition_service import nutrition_service
from backend.services.cooking_chat_service import cooking_chat_service
from backend.services.recipe_service import recipe_service
from backend.services.meal_planner_service import meal_planner_service
from backend.models.schemas import (
    CookingChatRequest,
    ChatMessage,
    RecipeGenerateRequest,
    MealPlanGenerateRequest,
    MealPlanProfile,
    RecipeResponse,
    RecipeIngredient,
    RecipeStep,
    MacroNutrients,
    MealPlanResponse,
    DailyPlan,
    PlannedMeal,
    GroceryItem
)

client = TestClient(app)

def test_ai_status_endpoint():
    res = client.get("/api/config/ai-status")
    assert res.status_code == 200
    data = res.json()
    assert "demo_mode" in data
    assert "is_configured" in data
    assert "message" in data
    assert "usda_live" in data

def test_api_key_clear():
    with patch("builtins.open", MagicMock()):
        res = client.post("/api/config/api-key", json={"api_key": ""})
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is False
        assert data["demo_mode"] is True

def test_api_key_invalid_validation():
    with patch.object(gemini_service, "test_connection", return_value={"valid": False, "error": "API key not valid."}):
        res = client.post("/api/config/api-key", json={"gemini_api_key": "AIzaSyDummyInvalidKey"})
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is False
        assert data["demo_mode"] is True

def test_api_key_successful_validation():
    with patch.object(gemini_service, "test_connection", return_value={"valid": True, "model": "gemini-3.5-flash-lite", "reply": "CONNECTED"}), \
         patch("builtins.open", MagicMock()):
        res = client.post("/api/config/api-key", json={"gemini_api_key": "AIzaSyValidKeyMockForTesting123"})
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert data["demo_mode"] is False
        assert data["model"] == "gemini-3.5-flash-lite"

def test_usda_service_parse_item():
    mock_raw = {
        "fdcId": 171688,
        "description": "Chicken, breast, meat only, cooked, roasted",
        "dataType": "SR Legacy",
        "servingSize": 140.0,
        "servingSizeUnit": "g",
        "householdServingFullText": "1 breast",
        "foodNutrients": [
            {"nutrientId": 1008, "nutrientName": "Energy", "unitName": "KCAL", "value": 165.0},
            {"nutrientId": 1003, "nutrientName": "Protein", "value": 31.02},
            {"nutrientId": 1004, "nutrientName": "Total lipid (fat)", "value": 3.57},
            {"nutrientId": 1005, "nutrientName": "Carbohydrate, by difference", "value": 0.0},
            {"nutrientId": 1079, "nutrientName": "Fiber, total dietary", "value": 0.0},
            {"nutrientId": 1093, "nutrientName": "Sodium, Na", "value": 74.0}
        ]
    }
    parsed = usda_service.parse_usda_food_item(mock_raw)
    assert parsed is not None
    assert parsed["fdc_id"] == 171688
    assert parsed["name"] == "Chicken, Breast, Meat Only, Cooked, Roasted"
    assert parsed["per_100g"]["calories"] == 165.0
    assert parsed["per_100g"]["protein"] == 31.0
    assert parsed["per_100g"]["fat"] == 3.6
    assert parsed["per_100g"]["carbohydrates"] == 0.0
    assert parsed["standard_serving_grams"] == 140.0

def test_usda_service_search_timeout_fallback():
    with patch("httpx.Client.get", side_effect=Exception("ReadTimeout")):
        res = usda_service.search_foods("apple")
        # Should catch exception cleanly and return None (graceful fallback)
        assert res is None

def test_usda_service_rate_limit_handling():
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "Rate limit exceeded"
    with patch("httpx.Client.get", return_value=mock_resp):
        res = usda_service.search_foods("pizza")
        # Should handle 429 gracefully and return None
        assert res is None

def test_gemini_multimodal_food_classification_and_usda_connect():
    mock_gemini_result = {
        "primary_prediction": "Avocado Toast",
        "food_id": "avocado_toast_custom",
        "confidence": 0.95,
        "category": "Breakfast",
        "standard_serving_name": "1 slice (150g)",
        "standard_serving_grams": 150.0,
        "is_composite": True,
        "components": [
            {"name": "Sourdough Toast", "estimated_grams": 90.0, "percentage": 60.0},
            {"name": "Mashed Avocado", "estimated_grams": 60.0, "percentage": 40.0}
        ],
        "alternatives": [
            {"name": "Guacamole Toast", "confidence": 0.35, "category": "Breakfast"}
        ],
        "nutrition_per_100g": {
            "calories": 196.0, "protein": 4.5, "carbohydrates": 21.0, "fat": 11.2, "fiber": 5.8, "sugar": 1.2
        },
        "ai_insights": "Rich in healthy monounsaturated fats."
    }

    mock_usda_result = [{
        "food_id": "usda_2709223",
        "fdc_id": 2709223,
        "name": "Avocado, raw",
        "category": "SR Legacy",
        "standard_serving_name": "1 serving (150g)",
        "standard_serving_grams": 150.0,
        "is_composite": False,
        "source": "USDA FoodData Central API (Live)",
        "per_100g": {
            "calories": 160.0, "protein": 2.0, "carbohydrates": 8.5, "fat": 14.7,
            "saturated_fat": 2.1, "fiber": 6.7, "sugar": 0.7, "sodium": 7.0,
            "potassium": 485.0, "calcium": 12.0, "iron": 0.6, "vitamin_c": 10.0, "cholesterol": 0.0
        },
        "portion_advice": "USDA verified profile.",
        "components": [],
        "healthier_alternatives": []
    }]

    from PIL import Image
    import io
    img = Image.new("RGB", (100, 100), color=(120, 180, 70))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    with patch.object(gemini_service, "is_configured", return_value=True), \
         patch.object(gemini_service, "classify_food_image", return_value=mock_gemini_result), \
         patch.object(usda_service, "is_configured", return_value=True), \
         patch.object(usda_service, "search_foods", return_value=mock_usda_result):
        resp = food_classifier_service.classify_image(img_bytes, "avocado_test.jpg", {})
        assert resp.primary_prediction == "Avocado Toast"
        assert resp.confidence == 0.95
        assert "USDA FoodData Central" in resp.model_tier
        assert len(resp.multi_item_components) == 2

def test_gemini_cooking_chat():
    mock_reply = {
        "reply": "Here is how to cook salmon with lemon herb quinoa!",
        "suggested_followups": ["What can I substitute for quinoa?", "How to cook in air fryer?"],
        "extracted_ingredients": ["Salmon", "Quinoa", "Lemon"]
    }

    req = CookingChatRequest(
        messages=[ChatMessage(role="user", content="How do I cook salmon with quinoa?")],
        available_ingredients=["Salmon", "Quinoa"]
    )

    with patch.object(gemini_service, "is_configured", return_value=True), \
         patch.object(gemini_service, "chat_cooking", return_value=mock_reply):
        res = cooking_chat_service.process_chat(req)
        assert "salmon with lemon herb quinoa" in res.reply
        assert res.is_demo_mode is False
        assert len(res.recommended_followups) == 2

def test_gemini_recipe_generation():
    mock_recipe = RecipeResponse(
        recipe_id="ai-recipe-1",
        title="Spiced Pan-Seared Salmon & Asparagus",
        description="Fresh Atlantic salmon with crisp lemon asparagus.",
        cuisine="Mediterranean",
        prep_time_minutes=8,
        cook_time_minutes=12,
        total_time_minutes=20,
        servings=2,
        base_servings=2,
        ingredients=[
            RecipeIngredient(name="Salmon Fillet", amount=300.0, unit="g", category="Proteins"),
            RecipeIngredient(name="Asparagus", amount=150.0, unit="g", category="Produce")
        ],
        instructions=[
            RecipeStep(step_number=1, instruction="Season salmon with lemon zest and pepper.", timer_minutes=2),
            RecipeStep(step_number=2, instruction="Pan-sear for 4 mins per side.", timer_minutes=8)
        ],
        substitutions=[],
        nutrition_per_serving=MacroNutrients(
            calories=380.0, protein=34.0, carbohydrates=6.0, fat=18.0, saturated_fat=2.5, fiber=3.0, sugar=2.0
        ),
        is_nutrition_calculated=True,
        dietary_tags=["High Protein", "Pescatarian"],
        equipment_needed=["skillet"],
        allergens_present=["fish"]
    )

    req = RecipeGenerateRequest(
        ingredients=["Salmon", "Asparagus"],
        servings=2,
        dietary_preference="pescatarian"
    )

    with patch.object(gemini_service, "is_configured", return_value=True), \
         patch.object(gemini_service, "generate_recipes_ai", return_value=[mock_recipe]):
        recipes = recipe_service.generate_recipes(req)
        assert len(recipes) >= 1
        assert recipes[0].title == "Spiced Pan-Seared Salmon & Asparagus"
        assert recipes[0].nutrition_per_serving.protein == 34.0

def test_gemini_meal_plan_generation():
    profile = MealPlanProfile(
        dietary_preference="pescatarian",
        goal="muscle_gain",
        age_range="18-35",
        activity_level="moderate",
        meals_per_day=3
    )
    req = MealPlanGenerateRequest(profile=profile, duration_days=1)

    mock_meal = PlannedMeal(
        meal_id="meal-1",
        meal_type="Lunch",
        meal_name="Grilled Salmon & Brown Rice Bowl",
        description="Omega-3 rich bowl with greens.",
        servings=1,
        ingredients=[
            RecipeIngredient(name="Salmon", amount=150.0, unit="g", category="Proteins"),
            RecipeIngredient(name="Brown Rice", amount=100.0, unit="g", category="Grains")
        ],
        nutrition=MacroNutrients(calories=550.0, protein=42.0, carbohydrates=50.0, fat=18.0, saturated_fat=2.5, fiber=5.0, sugar=2.0),
        prep_instructions=["Grill salmon and assemble with warm rice."]
    )

    mock_daily = DailyPlan(
        day_number=1,
        day_name="Day 1",
        meals=[mock_meal],
        daily_calories=550.0,
        daily_protein=42.0,
        daily_carbs=50.0,
        daily_fat=18.0
    )

    mock_plan = MealPlanResponse(
        plan_id="plan-test-123",
        created_at="2026-10-30T00:00:00Z",
        duration_days=1,
        profile=profile,
        target_daily_calories=2400.0,
        target_protein_grams=160.0,
        target_carbs_grams=260.0,
        target_fat_grams=75.0,
        daily_plans=[mock_daily],
        consolidated_grocery_list=[
            GroceryItem(name="Salmon", quantity_str="150g", category="Proteins")
        ],
        medical_disclaimer="Informational notice.",
        is_demo_mode=False
    )

    with patch.object(gemini_service, "is_configured", return_value=True), \
         patch.object(gemini_service, "generate_meal_plan_ai", return_value=mock_plan):
        plan = meal_planner_service.generate_meal_plan(req)
        assert plan.plan_id == "plan-test-123"
        assert plan.target_daily_calories == 2400.0
        assert len(plan.daily_plans) == 1
        assert plan.daily_plans[0].meals[0].meal_name == "Grilled Salmon & Brown Rice Bowl"
