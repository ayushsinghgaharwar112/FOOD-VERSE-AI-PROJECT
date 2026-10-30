import pytest
from fastapi.testclient import TestClient
from backend.models.schemas import RecipeGenerateRequest, MealPlanGenerateRequest, MealPlanProfile

# ============================================================================
# PART 3 TESTS: SMART COOKING ASSISTANT
# ============================================================================

def test_generate_recipes_success(client: TestClient):
    payload = {
        "ingredients": ["salmon", "quinoa", "broccoli"],
        "preferences": "healthy Mediterranean style",
        "servings": 2
    }
    response = client.post("/api/recipes/generate", json=payload)
    assert response.status_code == 200
    recipes = response.json()
    assert isinstance(recipes, list)
    assert len(recipes) >= 1
    
    top = recipes[0]
    assert "Pan-Seared Salmon" in top["title"] or "Salmon" in top["title"]
    assert top["servings"] == 2
    assert len(top["ingredients"]) >= 3
    assert len(top["instructions"]) >= 3
    assert top["nutrition_per_serving"]["calories"] > 0
    assert top["nutrition_per_serving"]["protein"] > 0
    assert top["is_nutrition_calculated"] is True

def test_generate_recipes_empty_ingredients(client: TestClient):
    payload = {"ingredients": []}
    response = client.post("/api/recipes/generate", json=payload)
    assert response.status_code == 400
    assert "at least one ingredient" in response.json()["detail"].lower()

def test_generate_recipes_allergy_exclusion(client: TestClient):
    payload = {
        "ingredients": ["salmon", "tofu", "quinoa"],
        "allergies": ["fish"],
        "servings": 2
    }
    response = client.post("/api/recipes/generate", json=payload)
    assert response.status_code == 200
    recipes = response.json()
    # None of the recipes should contain fish as allergen
    for r in recipes:
        assert "fish" not in [a.lower() for a in r.get("allergens_present", [])]

def test_generate_recipes_dietary_vegan(client: TestClient):
    payload = {
        "ingredients": ["tofu", "broccoli", "bell pepper"],
        "dietary_preference": "vegan",
        "servings": 2
    }
    response = client.post("/api/recipes/generate", json=payload)
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) >= 1
    assert "Vegan" in recipes[0]["dietary_tags"]

def test_cooking_chat_substitution(client: TestClient):
    payload = {
        "messages": [
            {"role": "user", "content": "What can I substitute for buttermilk in pancakes?"}
        ]
    }
    response = client.post("/api/cooking/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "lemon juice" in data["reply"].lower() or "vinegar" in data["reply"].lower()
    assert len(data["recommended_followups"]) >= 1

def test_cooking_chat_air_fryer(client: TestClient):
    payload = {
        "messages": [
            {"role": "user", "content": "Can I make this in an air fryer instead?"}
        ]
    }
    response = client.post("/api/cooking/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "air fryer" in data["reply"].lower()
    assert "airflow" in data["reply"].lower() or "temperature" in data["reply"].lower() or "preheat" in data["reply"].lower()

def test_cooking_sample_prompts(client: TestClient):
    response = client.get("/api/cooking/sample-prompts")
    assert response.status_code == 200
    prompts = response.json()
    assert len(prompts) >= 3

def test_saved_recipes_crud(client: TestClient):
    # 1. Generate a recipe to save
    gen_payload = {"ingredients": ["avocado", "sourdough", "eggs"], "servings": 2}
    gen_res = client.post("/api/recipes/generate", json=gen_payload)
    recipe = gen_res.json()[0]
    
    # 2. Save recipe
    save_payload = {"recipe": recipe, "user_notes": "Favorite weekend breakfast."}
    save_res = client.post("/api/recipes/save", json=save_payload)
    assert save_res.status_code == 200
    saved_id = save_res.json()["recipe_id"]
    
    # 3. List saved recipes
    list_res = client.get("/api/recipes")
    assert list_res.status_code == 200
    saved_list = list_res.json()
    assert any(r["recipe_id"] == saved_id for r in saved_list)
    
    # 4. Delete saved recipe
    del_res = client.delete(f"/api/recipes/{saved_id}")
    assert del_res.status_code == 200


# ============================================================================
# PART 3 TESTS: PERSONALIZED MEAL PLANNER
# ============================================================================

def test_meal_plan_generation_7_day(client: TestClient):
    payload = {
        "profile": {
            "dietary_preference": "vegetarian",
            "allergies": [],
            "goal": "weight_loss",
            "age_range": "18-35",
            "activity_level": "moderate",
            "budget": "moderate",
            "meals_per_day": 3,
            "preferred_cuisines": ["Mediterranean", "Asian"]
        },
        "duration_days": 7
    }
    response = client.post("/api/meal-plans/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["plan_id"].startswith("plan-")
    assert data["duration_days"] == 7
    assert len(data["daily_plans"]) == 7
    
    # Check day 1 structure
    day1 = data["daily_plans"][0]
    assert len(day1["meals"]) == 3
    assert day1["daily_calories"] > 0
    assert day1["daily_protein"] > 0
    
    # Check grocery list
    assert len(data["consolidated_grocery_list"]) >= 5
    assert any(g["category"] in ["Produce", "Grains", "Proteins", "Pantry"] for g in data["consolidated_grocery_list"])
    
    # Medical nutrition disclaimer present
    assert "DISCLAIMER" in data["medical_disclaimer"].upper()

def test_meal_plan_strict_allergy_filtering(client: TestClient):
    payload = {
        "profile": {
            "dietary_preference": "non-vegetarian",
            "allergies": ["dairy", "gluten", "fish"],
            "goal": "balanced",
            "age_range": "18-35",
            "activity_level": "sedentary",
            "budget": "budget-friendly",
            "meals_per_day": 3,
            "preferred_cuisines": []
        },
        "duration_days": 3
    }
    response = client.post("/api/meal-plans/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Ensure zero planned meals contain dairy, gluten, or fish in allergens or ingredients
    for day in data["daily_plans"]:
        for meal in day["meals"]:
            assert "Salmon" not in meal["meal_name"]
            assert "Greek Yogurt" not in meal["meal_name"]

def test_meal_plans_list_and_get(client: TestClient):
    # List previously saved meal plans
    response = client.get("/api/meal-plans")
    assert response.status_code == 200
    plans = response.json()
    assert isinstance(plans, list)
    if plans:
        first_id = plans[0]["plan_id"]
        single_res = client.get(f"/api/meal-plans/{first_id}")
        assert single_res.status_code == 200
        assert single_res.json()["plan_id"] == first_id
