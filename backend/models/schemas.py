from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = "healthy"
    app_name: str
    version: str
    demo_mode: bool
    model_name: str
    foods_in_database: int
    vision_backend: str
    freshness_model: Optional[str] = "BioFresh-Net-v2.1"
    hygiene_model: Optional[str] = "KitchenGuard-CV-v3.0"
    cooking_llm_model: Optional[str] = "FoodVerse-Chef-v3.2"
    meal_planner_model: Optional[str] = "NutriPlanner-AI-v2.5"
    usda_live: bool = False
    usda_status: Optional[str] = "Bundled USDA Database"
    supported_modules: List[str] = [
        "Food Recognition & Nutrition (Part 1)",
        "Food Freshness & Quality Intelligence (Part 2)",
        "Restaurant Kitchen Hygiene Monitoring (Part 2)",
        "Smart Cooking Assistant (Part 3)",
        "Personalized Meal Planner (Part 3)"
    ]

class APIKeyConfigRequest(BaseModel):
    api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    usda_api_key: Optional[str] = None

class APIKeyConfigResponse(BaseModel):
    valid: bool
    model: Optional[str] = None
    message: str
    demo_mode: bool

class FoodAlternative(BaseModel):
    food_id: str
    name: str
    confidence: float
    category: str

class MultiItemComponent(BaseModel):
    name: str
    estimated_grams: float
    percentage: float
    confidence: float

class ImageMetadata(BaseModel):
    filename: str
    content_type: str
    size_bytes: int
    dimensions: str

class FoodRecognitionResponse(BaseModel):
    primary_prediction: str
    food_id: str
    confidence: float
    category: str
    standard_serving_name: str
    standard_serving_grams: float
    alternatives: List[FoodAlternative] = []
    is_composite: bool = False
    multi_item_components: List[MultiItemComponent] = []
    multi_item_note: str
    model_tier: str
    inference_time_ms: float
    image_metadata: ImageMetadata

class NutritionAnalyzeRequest(BaseModel):
    food_id_or_name: str = Field(..., description="Unique food ID or common food name")
    serving_size: float = Field(..., gt=0, description="Numeric serving quantity")
    unit: str = Field(default="grams", description="'grams' or 'servings'")

class MacroNutrients(BaseModel):
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    saturated_fat: float = 0.0
    fiber: float
    sugar: float

class MicroNutrients(BaseModel):
    sodium: float
    potassium: float
    calcium: float
    iron: float
    vitamin_c: float
    cholesterol: float

class DailyValuePercentage(BaseModel):
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    saturated_fat: float
    fiber: float
    sodium: float
    calcium: float
    iron: float
    vitamin_c: float

class CalorieDistribution(BaseModel):
    protein_kcal: float
    carbs_kcal: float
    fat_kcal: float
    protein_pct: float
    carbs_pct: float
    fat_pct: float

class HealthierAlternativeItem(BaseModel):
    name: str
    reason: str
    calorie_difference: int

class ServingComponent(BaseModel):
    name: str
    grams: float
    percentage: float

class NutritionAnalyzeResponse(BaseModel):
    food_id: str
    food_name: str
    category: str
    serving_size_grams: float
    serving_display: str
    macros: MacroNutrients
    micros: MicroNutrients
    daily_value_percentages: DailyValuePercentage
    calorie_distribution: CalorieDistribution
    health_score: int
    nutri_grade: str
    health_notes: str
    portion_advice: str
    healthier_alternatives: List[HealthierAlternativeItem]
    dietary_tags: List[str]
    components: List[ServingComponent]
    is_demo_data: bool = False

class SampleImageInfo(BaseModel):
    id: str
    title: str
    subtitle: str
    filename: str
    image_url: str
    food_id: str


# ============================================================================
# PART 2 SCHEMAS: FOOD FRESHNESS & RESTAURANT HYGIENE INTELLIGENCE
# ============================================================================

class VisualQualityIndicator(BaseModel):
    name: str = Field(..., description="Indicator e.g. Discoloration, Bruising, Shriveling, Surface Spots")
    severity: str = Field(..., description="'None', 'Minor', 'Moderate', 'Severe'")
    confidence: float
    description: str

class StorageSuggestion(BaseModel):
    ideal_temperature: str
    humidity: str
    ethylene_sensitivity: str
    shelf_life_estimate: str
    actionable_tips: List[str]

class FreshnessAssessmentResponse(BaseModel):
    assessment_id: str
    timestamp: str
    item_name: str
    category: str
    quality_grade: str = Field(..., description="Prediction category e.g. 'Fresh / Optimal Quality', 'Moderately Fresh', 'Visibly Degraded', 'Uncertain'")
    confidence: float
    is_uncertain: bool = False
    uncertainty_reason: Optional[str] = None
    visual_indicators: List[VisualQualityIndicator] = []
    storage_guide: StorageSuggestion
    safety_disclaimer: str
    history_record: Dict[str, Any]
    model_tier: str
    processing_time_ms: float

class FreshnessSampleInfo(BaseModel):
    id: str
    title: str
    subtitle: str
    filename: str
    image_url: str
    item_name: str
    expected_grade: str


# Hygiene Monitoring Schemas

class HygieneFindingCondition(BaseModel):
    finding_id: str
    condition_type: str = Field(..., description="e.g. Uncovered Food, Visible Clutter, Food/Waste Proximity, PPE Compliance")
    severity: str = Field(..., description="'High', 'Medium', 'Low', 'Compliant'")
    confidence: float
    timestamp_formatted: Optional[str] = None
    timestamp_seconds: Optional[float] = None
    frame_index: Optional[int] = None
    description: str
    bounding_box: Optional[Dict[str, float]] = None

class ReviewChecklistItem(BaseModel):
    item_id: str
    category: str
    title: str
    status: str = Field(..., description="'Pass', 'Action Required', 'Uncertain / Needs Verification'")
    severity: str = Field(..., description="'None', 'Low', 'Medium', 'High'")
    details: str
    recommended_action: str
    reviewer_status: str = Field(default="Pending", description="'Pending', 'Approved', 'Flagged'")
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[str] = None

class VideoFrameSample(BaseModel):
    frame_index: int
    timestamp_seconds: float
    timestamp_formatted: str
    preview_base64: Optional[str] = None
    findings_count: int
    frame_findings: List[HygieneFindingCondition] = []

class HygieneAuditResponse(BaseModel):
    audit_id: str
    media_type: str = Field(..., description="'image' or 'video'")
    timestamp: str
    overall_score: int = Field(..., description="Sanitation Compliance Score (0-100)")
    compliance_grade: str
    total_findings: int
    action_required_count: int
    findings: List[HygieneFindingCondition]
    checklist: List[ReviewChecklistItem]
    frames_timeline: List[VideoFrameSample] = []
    metadata: Dict[str, Any]
    model_tier: str
    processing_time_ms: float
    is_demo_mode: bool = True

class ReviewUpdateRequest(BaseModel):
    reviewer_status: str = Field(..., description="'Approved' or 'Flagged'")
    reviewer_notes: Optional[str] = None
    reviewer_name: Optional[str] = "Quality Auditor"

class HygieneSampleInfo(BaseModel):
    id: str
    title: str
    subtitle: str
    filename: str
    media_url: str
    media_type: str = Field(..., description="'image' or 'video'")
    expected_rating: str



# ============================================================================
# PART 3 SCHEMAS: SMART COOKING ASSISTANT & PERSONALIZED MEAL PLANNER
# ============================================================================

class RecipeIngredient(BaseModel):
    name: str
    amount: float
    unit: str
    notes: Optional[str] = None
    category: str = "Pantry"

class RecipeStep(BaseModel):
    step_number: int
    instruction: str
    timer_minutes: Optional[int] = None
    tip: Optional[str] = None

class IngredientSubstitution(BaseModel):
    original: str
    substitute: str
    ratio: str
    notes: str

class RecipeResponse(BaseModel):
    recipe_id: str
    title: str
    description: str
    cuisine: str
    prep_time_minutes: int
    cook_time_minutes: int
    total_time_minutes: int
    servings: int
    base_servings: int = 2
    ingredients: List[RecipeIngredient]
    instructions: List[RecipeStep]
    substitutions: List[IngredientSubstitution] = []
    nutrition_per_serving: MacroNutrients
    is_nutrition_calculated: bool = True
    dietary_tags: List[str] = []
    equipment_needed: List[str] = []
    allergens_present: List[str] = []
    safety_warning: Optional[str] = None

class RecipeGenerateRequest(BaseModel):
    ingredients: List[str] = Field(..., description="List of user-provided ingredients")
    preferences: Optional[str] = Field(default="", description="e.g. quick, spicy, comfort food")
    dietary_preference: Optional[str] = Field(default="any", description="'vegetarian', 'vegan', 'non-vegetarian', or 'any'")
    allergies: Optional[List[str]] = Field(default=[], description="Allergies to strictly exclude")
    equipment: Optional[List[str]] = Field(default=[], description="Available equipment e.g. air fryer, oven, skillet")
    servings: Optional[int] = Field(default=2, ge=1, le=12)
    cuisine: Optional[str] = Field(default="any")
    max_cooking_time: Optional[int] = None
    image_base64: Optional[str] = None

class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str
    timestamp: str = ""
    recipe_id: Optional[str] = None

class CookingChatRequest(BaseModel):
    messages: List[ChatMessage]
    current_recipe: Optional[RecipeResponse] = None
    available_ingredients: Optional[List[str]] = []
    dietary_preference: Optional[str] = "any"
    allergies: Optional[List[str]] = []

class CookingChatResponse(BaseModel):
    reply: str
    suggested_recipes: List[RecipeResponse] = []
    recommended_followups: List[str] = []
    extracted_ingredients: List[str] = []
    is_demo_mode: bool = True

class RecipeSaveRequest(BaseModel):
    recipe: RecipeResponse
    user_notes: Optional[str] = None


# Meal Planner Schemas

class MealPlanProfile(BaseModel):
    dietary_preference: str = Field(default="non-vegetarian", description="'vegetarian', 'vegan', 'non-vegetarian'")
    allergies: List[str] = Field(default=[], description="Strict allergen exclusions")
    goal: str = Field(default="balanced", description="'balanced', 'weight_loss', 'muscle_gain'")
    age_range: str = Field(default="18-35", description="'18-35', '36-50', '51+'")
    activity_level: str = Field(default="moderate", description="'sedentary', 'light', 'moderate', 'very_active'")
    budget: str = Field(default="moderate", description="'budget-friendly', 'moderate', 'premium'")
    available_ingredients: List[str] = Field(default=[])
    meals_per_day: int = Field(default=3, ge=2, le=5)
    preferred_cuisines: List[str] = Field(default=[])

class PlannedMeal(BaseModel):
    meal_id: str
    meal_type: str = Field(..., description="'Breakfast', 'Lunch', 'Dinner', 'Snack'")
    meal_name: str
    description: str
    servings: int = 1
    ingredients: List[RecipeIngredient]
    nutrition: MacroNutrients
    is_calculated_nutrition: bool = True
    prep_instructions: List[str]
    substitutions: List[IngredientSubstitution] = []

class DailyPlan(BaseModel):
    day_number: int
    day_name: str
    meals: List[PlannedMeal]
    daily_calories: float
    daily_protein: float
    daily_carbs: float
    daily_fat: float

class GroceryItem(BaseModel):
    name: str
    quantity_str: str
    category: str
    meals_used_in: List[str] = []
    checked: bool = False

class MealPlanGenerateRequest(BaseModel):
    profile: MealPlanProfile
    duration_days: int = Field(default=7, ge=1, le=7)

class MealPlanResponse(BaseModel):
    plan_id: str
    created_at: str
    duration_days: int
    profile: MealPlanProfile
    target_daily_calories: float
    target_protein_grams: float
    target_carbs_grams: float
    target_fat_grams: float
    daily_plans: List[DailyPlan]
    consolidated_grocery_list: List[GroceryItem]
    medical_disclaimer: str
    is_demo_mode: bool = True
