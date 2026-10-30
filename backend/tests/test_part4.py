"""
Food Verse AI — Part 4 Test Suite
Comprehensive integration tests covering:
Journey 1: User registration, login, profile setup
Journey 2: Food recognition -> nutrition analysis -> insight generation
Journey 3: Produce freshness check -> storage recommendations -> history review
Journey 4: Restaurant hygiene image/video upload -> compliance report -> audit review
Journey 5: Ingredient-based recipe generation -> interactive cooking chat -> recipe saving
Journey 6: Personalized meal plan generation -> grocery list compile -> meal plan saving
Journey 7: Multi-user isolation verification (User A cannot access User B's history/data)
"""
import io
from PIL import Image
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def create_test_image(format="JPEG", size=(100, 100), color=(200, 100, 50)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


@pytest.fixture
def sample_food_image_bytes():
    return create_test_image(color=(210, 80, 50))


@pytest.fixture
def sample_freshness_image_bytes():
    return create_test_image(color=(100, 200, 50))


@pytest.fixture
def sample_hygiene_image_bytes():
    return create_test_image(color=(150, 150, 200))


# ── Fixtures ──────────────────────────────────────────────────────────────────
@pytest.fixture
def auth_headers_user_a():
    """Register and authenticate User A."""
    email = "user_a@foodverse.ai"
    pwd = "password123!"
    # Try register; if exists, just login
    reg_resp = client.post("/api/auth/register", json={
        "email": email,
        "password": pwd,
        "name": "Chef Alice"
    })
    if reg_resp.status_code == 201:
        token = reg_resp.json()["access_token"]
    else:
        login_resp = client.post("/api/auth/login", json={"email": email, "password": pwd})
        token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user_b():
    """Register and authenticate User B."""
    email = "user_b@foodverse.ai"
    pwd = "password456!"
    reg_resp = client.post("/api/auth/register", json={
        "email": email,
        "password": pwd,
        "name": "Baker Bob"
    })
    if reg_resp.status_code == 201:
        token = reg_resp.json()["access_token"]
    else:
        login_resp = client.post("/api/auth/login", json={"email": email, "password": pwd})
        token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Journey 1: Auth & Profile Setup ──────────────────────────────────────────
def test_journey_1_auth_and_profile_flow():
    # 1. Register a new user
    import uuid
    uniq = uuid.uuid4().hex[:6]
    email = f"tester_{uniq}@example.com"
    reg = client.post("/api/auth/register", json={
        "email": email,
        "password": "securepassword123",
        "name": "Jane Tester"
    })
    assert reg.status_code == 201
    data = reg.json()
    assert "access_token" in data
    assert data["user"]["email"] == email
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get profile /me
    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["name"] == "Jane Tester"

    # 3. Update profile
    updated = client.put("/api/auth/profile", headers=headers, json={
        "name": "Jane Pro Chef",
        "dietary_preference": "vegetarian",
        "goal": "muscle_gain",
        "allergies": ["peanuts", "shellfish"]
    })
    assert updated.status_code == 200
    assert updated.json()["name"] == "Jane Pro Chef"
    assert updated.json()["dietary_preference"] == "vegetarian"
    assert "peanuts" in updated.json()["allergies"]

    # 4. Invalid credentials rejected
    bad_login = client.post("/api/auth/login", json={
        "email": email,
        "password": "wrongpassword"
    })
    assert bad_login.status_code == 401


# ── Journey 2: Food Recognition -> Nutrition Analysis -> Insights ────────────
def test_journey_2_food_recognition_to_nutrition_insights(auth_headers_user_a, sample_food_image_bytes):
    # 1. Food recognition with user auth header
    resp = client.post(
        "/api/food/recognize",
        files={"image": ("test_pizza.jpg", sample_food_image_bytes, "image/jpeg")},
        headers=auth_headers_user_a
    )
    assert resp.status_code == 200
    rec_data = resp.json()
    assert "primary_prediction" in rec_data
    food_id = rec_data.get("food_id") or "margherita_pizza"

    # 2. Analyze nutrition
    nutri_resp = client.post("/api/nutrition/analyze", json={
        "food_id_or_name": food_id,
        "serving_size": 200,
        "unit": "grams"
    })
    assert nutri_resp.status_code == 200
    nutri_data = nutri_resp.json()
    assert nutri_data["macros"]["calories"] > 0
    assert "daily_value_percentages" in nutri_data

    # 3. Check Dashboard Insights endpoint
    insights_resp = client.get("/api/insights/dashboard", headers=auth_headers_user_a)
    assert insights_resp.status_code == 200
    insights = insights_resp.json()
    assert "user_greeting" in insights
    assert len(insights["personalized_recommendations"]) > 0


# ── Journey 3: Produce Freshness -> Storage Advice -> History ─────────────────
def test_journey_3_freshness_check_and_history(auth_headers_user_a, sample_freshness_image_bytes):
    # 1. Analyze freshness with user auth
    resp = client.post(
        "/api/freshness/analyze",
        files={"image": ("apple.jpg", sample_freshness_image_bytes, "image/jpeg")},
        headers=auth_headers_user_a
    )
    assert resp.status_code == 200
    freshness = resp.json()
    assert "quality_grade" in freshness
    assert "storage_guide" in freshness
    assert "safety_disclaimer" in freshness

    # 2. Review freshness history
    hist = client.get("/api/history/freshness", headers=auth_headers_user_a)
    assert hist.status_code == 200
    data = hist.json()
    assert data["total"] >= 1
    assert any(item["item_name"] == freshness["item_name"] for item in data["items"])


# ── Journey 4: Kitchen Hygiene Image Upload -> Report -> Checklist Review ─────
def test_journey_4_hygiene_audit_and_review(auth_headers_user_a, sample_hygiene_image_bytes):
    # 1. Image audit with user auth
    resp = client.post(
        "/api/hygiene/analyze-image",
        files={"image": ("kitchen.jpg", sample_hygiene_image_bytes, "image/jpeg")},
        headers=auth_headers_user_a
    )
    assert resp.status_code == 200
    audit = resp.json()
    assert "overall_score" in audit
    assert "compliance_grade" in audit
    assert len(audit["checklist"]) > 0

    # 2. Update a checklist review item
    item_id = audit["checklist"][0]["item_id"]
    rev_resp = client.post(
        f"/api/hygiene/reviews/{item_id}?audit_id={audit['audit_id']}",
        json={"reviewer_status": "Approved", "reviewer_notes": "Clean surfaces verified"}
    )
    assert rev_resp.status_code == 200
    assert rev_resp.json()["status"] in ["Pass", "Approved"]
    assert rev_resp.json()["reviewer_notes"] == "Clean surfaces verified"

    # 3. Check hygiene history
    hist = client.get("/api/history/hygiene", headers=auth_headers_user_a)
    assert hist.status_code == 200
    assert hist.json()["total"] >= 1


# ── Journey 5: Recipe Generation -> Chat -> Recipe Saving ────────────────────
def test_journey_5_recipe_generation_chat_and_saving(auth_headers_user_a):
    # 1. Generate recipes
    gen_resp = client.post("/api/recipes/generate", json={
        "ingredients": ["salmon", "quinoa", "lemon"],
        "servings": 2,
        "dietary_preference": "non-vegetarian"
    })
    assert gen_resp.status_code == 200
    recipes = gen_resp.json()
    assert len(recipes) >= 1
    target_recipe = recipes[0]

    # 2. Chat about recipe
    chat_resp = client.post("/api/cooking/chat", json={
        "messages": [{"role": "user", "content": "How do I make the salmon skin extra crispy?"}],
        "current_recipe": target_recipe
    }, headers=auth_headers_user_a)
    assert chat_resp.status_code == 200
    assert len(chat_resp.json()["reply"]) > 10

    # 3. Save recipe to user's favorites
    save_resp = client.post("/api/recipes/save", json={
        "recipe": target_recipe,
        "user_notes": "Perfect for Sunday meal prep"
    }, headers=auth_headers_user_a)
    assert save_resp.status_code == 200
    assert save_resp.json()["status"] == "saved"

    # 4. Verify listed in recipes
    list_resp = client.get("/api/recipes", headers=auth_headers_user_a)
    assert list_resp.status_code == 200
    assert any(r["recipe_id"] == target_recipe["recipe_id"] for r in list_resp.json())


# ── Journey 6: Meal Plan Generation -> Grocery List -> Save ──────────────────
def test_journey_6_meal_plan_generation_and_saving(auth_headers_user_a):
    # 1. Generate meal plan
    plan_resp = client.post("/api/meal-plans/generate", json={
        "profile": {
            "dietary_preference": "vegetarian",
            "goal": "balanced",
            "meals_per_day": 3
        },
        "duration_days": 3
    })
    assert plan_resp.status_code == 200
    plan = plan_resp.json()
    assert len(plan["daily_plans"]) == 3
    assert len(plan["consolidated_grocery_list"]) > 0

    # 2. Save meal plan
    save_resp = client.post("/api/meal-plans/save", json=plan, headers=auth_headers_user_a)
    assert save_resp.status_code == 200
    assert save_resp.json()["status"] == "saved"

    # 3. Fetch meal plan by id
    get_resp = client.get(f"/api/meal-plans/{plan['plan_id']}", headers=auth_headers_user_a)
    assert get_resp.status_code == 200
    assert get_resp.json()["plan_id"] == plan["plan_id"]


# ── Journey 7: Multi-User Isolation Verification ──────────────────────────────
def test_journey_7_multi_user_isolation(auth_headers_user_a, auth_headers_user_b):
    # Save a recipe specifically as User A
    dummy_recipe = {
        "recipe_id": "user-a-secret-sauce-recipe",
        "title": "Alice's Secret Sauce",
        "description": "Family secret recipe",
        "cuisine": "French",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "total_time_minutes": 25,
        "servings": 4,
        "base_servings": 4,
        "ingredients": [{"name": "Butter", "amount": 50, "unit": "g"}],
        "instructions": [{"step_number": 1, "instruction": "Melt butter"}],
        "nutrition_per_serving": {
            "calories": 200, "protein": 1, "carbohydrates": 0,
            "fat": 22, "saturated_fat": 14, "fiber": 0, "sugar": 0
        }
    }
    client.post("/api/recipes/save", json={"recipe": dummy_recipe}, headers=auth_headers_user_a)

    # 1. User A sees their own recipe in recipes list
    user_a_recipes = client.get("/api/recipes", headers=auth_headers_user_a).json()
    assert any(r["recipe_id"] == "user-a-secret-sauce-recipe" for r in user_a_recipes)

    # 2. User B CANNOT see User A's recipe in their recipes list
    user_b_recipes = client.get("/api/recipes", headers=auth_headers_user_b).json()
    assert not any(r["recipe_id"] == "user-a-secret-sauce-recipe" for r in user_b_recipes)

    # 3. Check history endpoint isolation
    user_a_hist = client.get("/api/history/recipes", headers=auth_headers_user_a).json()
    assert any(r["recipe_id"] == "user-a-secret-sauce-recipe" for r in user_a_hist["items"])

    user_b_hist = client.get("/api/history/recipes", headers=auth_headers_user_b).json()
    assert not any(r["recipe_id"] == "user-a-secret-sauce-recipe" for r in user_b_hist["items"])

    # 4. User B cannot delete User A's record
    user_a_record_id = [r["id"] for r in user_a_hist["items"] if r["recipe_id"] == "user-a-secret-sauce-recipe"][0]
    unauthorized_delete = client.delete(f"/api/history/recipes/{user_a_record_id}", headers=auth_headers_user_b)
    assert unauthorized_delete.status_code in [403, 404]
