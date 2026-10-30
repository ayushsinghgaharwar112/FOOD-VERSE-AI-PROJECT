from fastapi import APIRouter
from typing import Dict, Any, Optional
from backend.config import settings, PROJECT_ROOT
from backend.models.schemas import HealthResponse, APIKeyConfigRequest, APIKeyConfigResponse
from backend.services.nutrition_service import nutrition_service
from backend.services.gemini_service import gemini_service
from backend.services.usda_service import usda_service

router = APIRouter(prefix="/api", tags=["System Health & Config"])

@router.get("/health", response_model=HealthResponse)
def get_health():
    is_live = gemini_service.is_configured()
    is_usda_live = usda_service.is_configured()
    vision_backend = f"Google Gemini Multimodal Vision ({gemini_service.active_model})" if is_live else "Heuristic Feature Classifier (Part 1 Demo Mode)"
    usda_status = "USDA FoodData Central API (Live Online)" if is_usda_live else "Bundled USDA Verified Database"

    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        demo_mode=not is_live,
        model_name=gemini_service.active_model if is_live else settings.AI_VISION_MODEL,
        foods_in_database=len(nutrition_service.database),
        vision_backend=vision_backend,
        freshness_model=f"Google Gemini Vision ({gemini_service.active_model})" if is_live else settings.FRESHNESS_MODEL_NAME,
        hygiene_model=f"Google Gemini Vision ({gemini_service.active_model})" if is_live else settings.HYGIENE_MODEL_NAME,
        cooking_llm_model=f"Google Gemini LLM ({gemini_service.active_model})" if is_live else settings.COOKING_LLM_MODEL,
        meal_planner_model=f"Google Gemini AI ({gemini_service.active_model})" if is_live else settings.MEAL_PLANNER_MODEL,
        usda_live=is_usda_live,
        usda_status=usda_status,
        supported_modules=[
            "Food Recognition & Nutrition (Part 1)",
            "Food Freshness & Quality Intelligence (Part 2)",
            "Restaurant Kitchen Hygiene Monitoring (Part 2)",
            "Smart Cooking Assistant (Part 3)",
            "Personalized Meal Planner (Part 3)"
        ]
    )

@router.get("/config/ai-status")
def get_ai_status():
    is_live = gemini_service.is_configured()
    is_usda_live = usda_service.is_configured()
    return {
        "demo_mode": not is_live,
        "is_configured": is_live,
        "active_model": gemini_service.active_model if is_live else "None (Offline Heuristics)",
        "message": "Live Google Gemini Multimodal AI is active." if is_live else "Running in Offline Heuristic Demo Mode.",
        "api_key_masked": f"{gemini_service.api_key[:6]}...{gemini_service.api_key[-4:]}" if is_live and len(gemini_service.api_key) > 10 else None,
        "usda_live": is_usda_live,
        "usda_key_masked": f"{usda_service.api_key[:4]}...{usda_service.api_key[-4:]}" if is_usda_live and len(usda_service.api_key) > 8 else None
    }

def _persist_env_key(key_name: str, value: str):
    """Safely updates or appends key in the root .env file."""
    env_file = PROJECT_ROOT / ".env"
    try:
        lines = []
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith(f"{key_name}="):
                        continue
                    lines.append(line)
        lines.append(f"{key_name}={value}\n")
        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception:
        pass

@router.post("/config/api-key", response_model=APIKeyConfigResponse)
def configure_api_key(req: APIKeyConfigRequest):
    key = (req.gemini_api_key or req.api_key or "").strip()
    usda_key = (req.usda_api_key or "").strip()

    messages = []

    # Handle USDA Key update if provided
    if usda_key:
        usda_service.set_api_key(usda_key)
        _persist_env_key("USDA_API_KEY", usda_key)
        test_u = usda_service.test_connection()
        if test_u.get("valid"):
            messages.append("USDA FoodData Central connected successfully!")
        else:
            messages.append(f"USDA Key warning: {test_u.get('error')}")

    # Handle Gemini Key update if provided
    if req.api_key is not None or req.gemini_api_key is not None:
        if not key:
            gemini_service.set_api_key("")
            _persist_env_key("GEMINI_API_KEY", "")
            return APIKeyConfigResponse(
                valid=False,
                model=None,
                message="Gemini API Key cleared. Switched to Offline Heuristic Demo Mode.",
                demo_mode=True
            )

        gemini_service.set_api_key(key)
        test_res = gemini_service.test_connection()
        if test_res.get("valid"):
            _persist_env_key("GEMINI_API_KEY", key)
            messages.append(f"Google Gemini connected ({gemini_service.active_model})!")
            return APIKeyConfigResponse(
                valid=True,
                model=gemini_service.active_model,
                message=" | ".join(messages),
                demo_mode=False
            )
        else:
            err = test_res.get("error", "Failed to connect to Google Gemini API.")
            return APIKeyConfigResponse(
                valid=False,
                model=None,
                message=f"Gemini Key validation failed: {err}",
                demo_mode=True
            )

    return APIKeyConfigResponse(
        valid=gemini_service.is_configured(),
        model=gemini_service.active_model if gemini_service.is_configured() else None,
        message=" | ".join(messages) if messages else "Configuration updated.",
        demo_mode=not gemini_service.is_configured()
    )

@router.post("/config/test-usda")
def test_usda_connection():
    return usda_service.test_connection()
