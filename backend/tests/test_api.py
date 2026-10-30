import io
from PIL import Image
import pytest
from fastapi.testclient import TestClient

def create_test_image(format="JPEG", size=(100, 100), color=(200, 100, 50)) -> io.BytesIO:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf

def test_health_endpoint(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert data["foods_in_database"] > 0
    assert "model_name" in data

def test_get_samples_endpoint(client: TestClient):
    response = client.get("/api/food/samples")
    assert response.status_code == 200
    samples = response.json()
    assert isinstance(samples, list)
    assert len(samples) >= 6
    assert any(s["food_id"] == "avocado_toast" for s in samples)

def test_get_sample_file(client: TestClient):
    response = client.get("/api/food/samples/avocado_toast.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 100

def test_recognize_valid_image(client: TestClient):
    img_buf = create_test_image("JPEG")
    files = {"image": ("test_food.jpg", img_buf, "image/jpeg")}
    response = client.post("/api/food/recognize", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "primary_prediction" in data
    assert "confidence" in data
    assert 0.0 <= data["confidence"] <= 1.0
    assert "alternatives" in data
    assert "multi_item_components" in data
    assert "multi_item_note" in data
    assert data["image_metadata"]["dimensions"] == "100x100 px"

def test_recognize_invalid_mime(client: TestClient):
    files = {"image": ("test.txt", io.BytesIO(b"Hello world food text"), "text/plain")}
    response = client.post("/api/food/recognize", files=files)
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

def test_recognize_empty_file(client: TestClient):
    files = {"image": ("empty.jpg", io.BytesIO(b""), "image/jpeg")}
    response = client.post("/api/food/recognize", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

def test_nutrition_analyze_grams(client: TestClient):
    payload = {
        "food_id_or_name": "avocado_toast",
        "serving_size": 200.0,
        "unit": "grams"
    }
    response = client.post("/api/nutrition/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["food_id"] == "avocado_toast"
    assert data["serving_size_grams"] == 200.0
    
    # 100g avocado toast is 196 kcal -> 200g should be 392 kcal
    assert data["macros"]["calories"] == 392.0
    assert data["macros"]["protein"] == 9.0  # 4.5 * 2
    assert data["macros"]["carbohydrates"] == 42.0  # 21.0 * 2
    assert "daily_value_percentages" in data
    assert "calorie_distribution" in data
    assert data["calorie_distribution"]["protein_pct"] > 0
    assert len(data["healthier_alternatives"]) > 0

def test_nutrition_analyze_servings(client: TestClient):
    payload = {
        "food_id_or_name": "grilled_salmon",
        "serving_size": 1.0,
        "unit": "servings"
    }
    response = client.post("/api/nutrition/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["food_id"] == "grilled_salmon"
    # standard serving for grilled salmon bowl is 320g
    assert data["serving_size_grams"] == 320.0
    assert data["health_score"] >= 90
    assert len(data["components"]) == 3

def test_nutrition_analyze_invalid_serving_size(client: TestClient):
    payload = {
        "food_id_or_name": "margherita_pizza",
        "serving_size": -50.0,
        "unit": "grams"
    }
    response = client.post("/api/nutrition/analyze", json=payload)
    assert response.status_code in [400, 422]

def test_nutrition_analyze_unknown_food(client: TestClient):
    payload = {
        "food_id_or_name": "space_extraterrestrial_nutrient_x99",
        "serving_size": 100.0,
        "unit": "grams"
    }
    response = client.post("/api/nutrition/analyze", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_nutrition_catalog_list(client: TestClient):
    response = client.get("/api/nutrition/foods")
    assert response.status_code == 200
    foods = response.json()
    assert len(foods) >= 10
