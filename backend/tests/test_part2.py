import io
import os
from pathlib import Path
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from backend.config import FRESHNESS_SAMPLES_DIR, HYGIENE_SAMPLES_DIR

def create_dummy_image(format="JPEG", size=(120, 120), color=(220, 50, 50)) -> io.BytesIO:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf

# ============================================================================
# FRESHNESS MODULE TESTS
# ============================================================================

def test_freshness_samples_endpoint(client: TestClient):
    response = client.get("/api/freshness/samples")
    assert response.status_code == 200
    samples = response.json()
    assert isinstance(samples, list)
    assert len(samples) >= 4
    assert any(s["item_name"] == "Apple" for s in samples)

def test_freshness_sample_file(client: TestClient):
    response = client.get("/api/freshness/samples/fresh_apple.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 100

def test_freshness_analyze_fresh_apple(client: TestClient):
    sample_path = FRESHNESS_SAMPLES_DIR / "fresh_apple.jpg"
    with open(sample_path, "rb") as f:
        files = {"image": ("fresh_apple.jpg", f, "image/jpeg")}
        response = client.post("/api/freshness/analyze", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["item_name"] == "Fresh Apple"
    assert "Optimal Quality" in data["quality_grade"]
    assert data["confidence"] >= 0.70
    assert len(data["visual_indicators"]) >= 4
    assert "ideal_temperature" in data["storage_guide"]
    assert "SAFETY DISCLAIMER" in data["safety_disclaimer"].upper()
    assert "history_record" in data
    assert data["history_record"]["assessment_id"] == data["assessment_id"]

def test_freshness_analyze_stale_tomato(client: TestClient):
    sample_path = FRESHNESS_SAMPLES_DIR / "stale_tomato.jpg"
    with open(sample_path, "rb") as f:
        files = {"image": ("stale_tomato.jpg", f, "image/jpeg")}
        response = client.post("/api/freshness/analyze", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "Visibly Degraded" in data["quality_grade"] or "Stale" in data["quality_grade"]
    assert any(ind["severity"] in ["Moderate", "Severe"] for ind in data["visual_indicators"])

def test_freshness_analyze_uncertain_greens(client: TestClient):
    sample_path = FRESHNESS_SAMPLES_DIR / "uncertain_greens.jpg"
    with open(sample_path, "rb") as f:
        files = {"image": ("uncertain_greens.jpg", f, "image/jpeg")}
        response = client.post("/api/freshness/analyze", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_uncertain"] is True
    assert "Uncertain / Insufficient Evidence" in data["quality_grade"]
    assert data["uncertainty_reason"] is not None

def test_freshness_invalid_mime(client: TestClient):
    files = {"image": ("readme.txt", io.BytesIO(b"Non-image text file"), "text/plain")}
    response = client.post("/api/freshness/analyze", files=files)
    assert response.status_code == 400
    assert "Unsupported image format" in response.json()["detail"]

def test_freshness_empty_file(client: TestClient):
    files = {"image": ("empty.jpg", io.BytesIO(b""), "image/jpeg")}
    response = client.post("/api/freshness/analyze", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


# ============================================================================
# RESTAURANT HYGIENE MODULE TESTS
# ============================================================================

def test_hygiene_samples_endpoint(client: TestClient):
    response = client.get("/api/hygiene/samples")
    assert response.status_code == 200
    samples = response.json()
    assert isinstance(samples, list)
    assert len(samples) >= 3
    assert any(s["media_type"] == "video" for s in samples)

def test_hygiene_sample_file(client: TestClient):
    response = client.get("/api/hygiene/samples/clean_kitchen.jpg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"

def test_hygiene_analyze_clean_image(client: TestClient):
    sample_path = HYGIENE_SAMPLES_DIR / "clean_kitchen.jpg"
    with open(sample_path, "rb") as f:
        files = {"image": ("clean_kitchen.jpg", f, "image/jpeg")}
        response = client.post("/api/hygiene/analyze-image", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["overall_score"] >= 80
    assert "Grade A" in data["compliance_grade"] or "Grade B" in data["compliance_grade"]
    assert len(data["checklist"]) >= 4
    assert len(data["frames_timeline"]) == 1

def test_hygiene_analyze_violation_image(client: TestClient):
    sample_path = HYGIENE_SAMPLES_DIR / "violation_kitchen.jpg"
    with open(sample_path, "rb") as f:
        files = {"image": ("violation_kitchen.jpg", f, "image/jpeg")}
        response = client.post("/api/hygiene/analyze-image", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["action_required_count"] > 0
    assert any(f["condition_type"] == "Uncovered Food Container" for f in data["findings"])
    assert any("Waste" in f["condition_type"] for f in data["findings"])

def test_hygiene_analyze_video(client: TestClient):
    sample_path = HYGIENE_SAMPLES_DIR / "kitchen_prep_clip.mp4"
    assert sample_path.exists(), "Sample video must exist"
    
    with open(sample_path, "rb") as f:
        files = {"video": ("kitchen_prep_clip.mp4", f, "video/mp4")}
        response = client.post("/api/hygiene/analyze-video", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["media_type"] == "video"
    assert data["audit_id"].startswith("audit-")
    assert len(data["frames_timeline"]) >= 2
    assert "preview_base64" in data["frames_timeline"][0]
    assert data["frames_timeline"][0]["preview_base64"].startswith("data:image/jpeg;base64,")

def test_hygiene_reviewer_checklist_update(client: TestClient):
    # First analyze an image to register an audit
    sample_path = HYGIENE_SAMPLES_DIR / "violation_kitchen.jpg"
    with open(sample_path, "rb") as f:
        files = {"image": ("violation_kitchen.jpg", f, "image/jpeg")}
        audit_res = client.post("/api/hygiene/analyze-image", files=files)
    
    audit_id = audit_res.json()["audit_id"]
    
    # Reviewer marks the uncovered food item as Reviewed / Approved
    payload = {
        "reviewer_status": "Approved",
        "reviewer_notes": "Chef placed stainless lids over pans upon auditor request.",
        "reviewer_name": "Sanitation Officer Sarah"
    }
    update_res = client.post(
        f"/api/hygiene/reviews/chk-food-storage?audit_id={audit_id}",
        json=payload
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["reviewer_status"] == "Approved"
    assert updated["reviewed_by"] == "Sanitation Officer Sarah"

def test_hygiene_invalid_video_format(client: TestClient):
    files = {"video": ("fake_video.txt", io.BytesIO(b"Not a video file"), "text/plain")}
    response = client.post("/api/hygiene/analyze-video", files=files)
    assert response.status_code == 400
    assert "Unsupported video format" in response.json()["detail"]
