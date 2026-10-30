import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_IMAGES_DIR = DATA_DIR / "sample_images"
FRESHNESS_SAMPLES_DIR = DATA_DIR / "freshness_samples"
HYGIENE_SAMPLES_DIR = DATA_DIR / "hygiene_samples"
SAVED_RECIPES_PATH = DATA_DIR / "saved_recipes.json"
SAVED_MEALPLANS_PATH = DATA_DIR / "saved_mealplans.json"

class Settings(BaseSettings):
    APP_NAME: str = "Food Verse AI"
    APP_VERSION: str = "4.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Part 4 — Auth & DB
    SECRET_KEY: str = "food-verse-ai-super-secret-key-change-in-production-32chars!!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    DATABASE_URL: str = ""  # blank = SQLite default in database.py
    
    # Allowed CORS Origins
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # Upload Validation (Part 1 & Part 2)
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB for images
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp"]
    
    MAX_VIDEO_SIZE_BYTES: int = 25 * 1024 * 1024   # 25MB for videos
    ALLOWED_VIDEO_TYPES: list[str] = ["video/mp4", "video/webm", "video/quicktime", "video/x-matroska"]
    MAX_VIDEO_DURATION_SECONDS: float = 30.0
    VIDEO_FRAME_INTERVAL_SECONDS: float = 1.0      # Sample 1 frame per second
    
    # AI Models & External API Keys (Parts 1, 2, 3)
    GEMINI_API_KEY: str = ""
    USDA_API_KEY: str = ""
    AI_VISION_MODEL: str = "gemini-3.5-flash-lite"
    FRESHNESS_MODEL_NAME: str = "gemini-3.5-flash-lite"
    HYGIENE_MODEL_NAME: str = "gemini-3.5-flash-lite"
    COOKING_LLM_MODEL: str = "gemini-3.5-flash-lite"
    MEAL_PLANNER_MODEL: str = "gemini-3.5-flash-lite"
    MIN_CONFIDENCE_THRESHOLD: float = 0.60
    DEMO_MODE_DEFAULT: bool = True

    model_config = SettingsConfigDict(env_file=str(PROJECT_ROOT / ".env"), env_file_encoding="utf-8", extra="allow")

settings = Settings()
