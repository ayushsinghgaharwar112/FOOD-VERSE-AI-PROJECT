import os
import json
import uuid
import base64
import logging
import datetime
from typing import Dict, Any, List, Optional
import httpx

from backend.config import settings
from backend.models.schemas import (
    RecipeResponse,
    RecipeIngredient,
    RecipeStep,
    IngredientSubstitution,
    MacroNutrients,
    RecipeGenerateRequest,
    MealPlanProfile,
    MealPlanResponse,
    DailyPlan,
    PlannedMeal,
    GroceryItem
)

logger = logging.getLogger("food_verse.gemini")

class GeminiService:
    """
    Direct REST integration for Google Gemini multimodal vision and generative AI models.
    Supports gemini-3.5-flash-lite, gemini-3.5-flash, and fallback candidates.
    Uses httpx without requiring external heavy SDKs.
    """
    def __init__(self):
        self._api_key = settings.GEMINI_API_KEY.strip()
        # Active candidate models in preference order
        self.candidate_models = [
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash",
            "gemini-flash-latest",
            "gemini-1.5-flash"
        ]
        self.active_model = "gemini-3.5-flash-lite"
        self.timeout = 25.0

    @property
    def api_key(self) -> str:
        return self._api_key or settings.GEMINI_API_KEY.strip()

    def set_api_key(self, key: str):
        self._api_key = key.strip()
        settings.GEMINI_API_KEY = self._api_key

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def test_connection(self) -> Dict[str, Any]:
        """Test API key validity with a lightweight ping to Gemini."""
        if not self.is_configured():
            return {
                "valid": False,
                "error": "No Gemini API key provided. Add GEMINI_API_KEY in .env."
            }

        headers = {"x-goog-api-key": self.api_key}
        for model in self.candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": "Reply in one word: CONNECTED"}]}
                ],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 30}
            }

            try:
                with httpx.Client(timeout=10.0) as client:
                    res = client.post(url, headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        cand = data.get("candidates", [{}])[0]
                        parts = cand.get("content", {}).get("parts", [])
                        reply = ""
                        for p in parts:
                            if "text" in p:
                                reply = p["text"]
                        self.active_model = model
                        return {
                            "valid": True,
                            "model": model,
                            "reply": reply.strip(),
                            "message": f"Successfully connected to Google Gemini AI ({model})!"
                        }
                    elif res.status_code in (404, 400):
                        continue
                    else:
                        err_msg = res.text
                        try:
                            err_json = res.json()
                            err_msg = err_json.get("error", {}).get("message", res.text)
                        except Exception:
                            pass
                        return {
                            "valid": False,
                            "status_code": res.status_code,
                            "error": f"Gemini API returned error: {err_msg}"
                        }
            except Exception as e:
                logger.warning(f"Error testing Gemini model {model}: {e}")
                continue

        return {
            "valid": False,
            "error": "Failed to connect to Google Gemini models. Check your API key and network."
        }

    def _call_gemini_api(self, contents: List[Dict[str, Any]], system_instruction: Optional[str] = None, json_mode: bool = False, max_tokens: int = 1500) -> Optional[str]:
        """Send a request to Gemini REST endpoint across candidate models."""
        if not self.is_configured():
            return None

        headers = {"x-goog-api-key": self.api_key}

        for model in self.candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            body: Dict[str, Any] = {"contents": contents}
            
            gen_config: Dict[str, Any] = {
                "temperature": 0.2 if json_mode else 0.7,
                "maxOutputTokens": max_tokens
            }
            if json_mode:
                gen_config["response_mime_type"] = "application/json"
            body["generationConfig"] = gen_config

            if system_instruction:
                body["systemInstruction"] = {
                    "parts": [{"text": system_instruction}]
                }

            try:
                with httpx.Client(timeout=self.timeout) as client:
                    res = client.post(url, headers=headers, json=body)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for p in parts:
                                if "text" in p and p["text"]:
                                    self.active_model = model
                                    return p["text"]
                    elif res.status_code in (404, 400):
                        continue
                    else:
                        logger.warning(f"Gemini API error ({res.status_code}): {res.text[:150]}")
                        break
            except Exception as e:
                logger.error(f"Error calling Gemini model {model}: {e}")
                continue

        return None

    def classify_food_image(self, image_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """Multimodal image recognition of any food using Gemini Vision."""
        if not self.is_configured():
            return None

        mime_type = "image/jpeg"
        lower_fn = filename.lower()
        if lower_fn.endswith(".png"):
            mime_type = "image/png"
        elif lower_fn.endswith(".webp"):
            mime_type = "image/webp"

        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        
        prompt = (
            "Analyze this food image in detail. Identify the dish accurately. "
            "Return a strictly valid JSON object conforming to this format:\n"
            "{\n"
            '  "primary_prediction": "Name of Dish",\n'
            '  "food_id": "dish_name_in_snake_case",\n'
            '  "category": "Main Course / Salad / Breakfast / Dessert / etc",\n'
            '  "confidence": 0.95,\n'
            '  "standard_serving_name": "1 serving (200g)",\n'
            '  "standard_serving_grams": 200.0,\n'
            '  "is_composite": true,\n'
            '  "components": [\n'
            '    {"name": "Ingredient 1", "estimated_grams": 80.0, "percentage": 40.0},\n'
            '    {"name": "Ingredient 2", "estimated_grams": 60.0, "percentage": 30.0}\n'
            '  ],\n'
            '  "alternatives": [\n'
            '    {"name": "Alternative Dish 1", "confidence": 0.40, "category": "Category"},\n'
            '    {"name": "Alternative Dish 2", "confidence": 0.25, "category": "Category"}\n'
            '  ],\n'
            '  "nutrition_per_100g": {\n'
            '    "calories": 180.0,\n'
            '    "protein": 12.0,\n'
            '    "carbohydrates": 20.0,\n'
            '    "fat": 6.0,\n'
            '    "saturated_fat": 1.5,\n'
            '    "fiber": 2.5,\n'
            '    "sugar": 1.0,\n'
            '    "sodium": 320.0,\n'
            '    "potassium": 280.0,\n'
            '    "vitamin_c": 12.0,\n'
            '    "iron": 1.8\n'
            '  },\n'
            '  "ai_insights": "Nutritional takeaway about this food and portion recommendations."\n'
            "}"
        )

        contents = [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_image
                        }
                    }
                ]
            }
        ]

        raw_response = self._call_gemini_api(contents, json_mode=True, max_tokens=1500)
        if not raw_response:
            return None

        try:
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Failed to parse Gemini classification JSON: {e}")
            return None

    def generate_recipes_ai(self, req: RecipeGenerateRequest) -> Optional[List[RecipeResponse]]:
        """Generates custom culinary recipes using Gemini LLM tailored to user pantry & allergies."""
        if not self.is_configured():
            return None

        system_instruction = (
            "You are Food Verse AI Chef, an expert Michelin-trained executive chef and registered dietitian. "
            "You create appetizing, wholesome recipes maximizing the user's available pantry ingredients while "
            "strictly obeying allergy exclusions and dietary preferences. "
            "Always return strictly valid JSON matching the requested structure."
        )

        ing_list = ", ".join(req.ingredients) if req.ingredients else "Any balanced pantry staple"
        allergies_str = ", ".join(req.allergies) if req.allergies else "None"
        equipment_str = ", ".join(req.equipment) if req.equipment else "Standard stovetop & oven"

        prompt = (
            f"Generate 2 tailored recipes based on:\n"
            f"- Available ingredients: {ing_list}\n"
            f"- Dietary preference: {req.dietary_preference}\n"
            f"- Strict allergen exclusions (DO NOT USE ANY OF THESE): {allergies_str}\n"
            f"- Cooking equipment: {equipment_str}\n"
            f"- Desired servings: {req.servings}\n"
            f"- Style / preference: {req.preferences or 'balanced & delicious'}\n\n"
            "Return a JSON array containing 2 recipe objects matching this schema:\n"
            "[\n"
            "  {\n"
            '    "recipe_id": "unique-slug-id",\n'
            '    "title": "Recipe Title",\n'
            '    "description": "Appetizing 1-sentence description",\n'
            '    "cuisine": "Cuisine type",\n'
            '    "prep_time_minutes": 10,\n'
            '    "cook_time_minutes": 15,\n'
            '    "total_time_minutes": 25,\n'
            '    "servings": 2,\n'
            '    "base_servings": 2,\n'
            '    "ingredients": [\n'
            '      {"name": "Ingredient Name", "amount": 150.0, "unit": "g", "category": "Proteins/Produce/Pantry", "notes": "prep note"}\n'
            '    ],\n'
            '    "instructions": [\n'
            '      {"step_number": 1, "instruction": "Step instruction...", "timer_minutes": 5, "tip": "Chef tip..."}\n'
            '    ],\n'
            '    "substitutions": [\n'
            '      {"original": "Ingredient", "substitute": "Alternative", "ratio": "1:1", "notes": "Why this works"}\n'
            '    ],\n'
            '    "nutrition_per_serving": {\n'
            '      "calories": 420.0, "protein": 32.0, "carbohydrates": 35.0, "fat": 14.0, "saturated_fat": 2.5, "fiber": 5.0, "sugar": 3.0\n'
            '    },\n'
            '    "dietary_tags": ["High Protein", "Quick"],\n'
            '    "equipment_needed": ["skillet"],\n'
            '    "allergens_present": []\n'
            "  }\n"
            "]"
        )

        contents = [{"parts": [{"text": prompt}]}]
        raw = self._call_gemini_api(contents, system_instruction=system_instruction, json_mode=True, max_tokens=2500)
        if not raw:
            return None

        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            items = json.loads(cleaned)
            if not isinstance(items, list):
                items = [items]

            recipes: List[RecipeResponse] = []
            for item in items:
                rec_id = item.get("recipe_id", f"gemini-rec-{uuid.uuid4().hex[:8]}")
                ings = [
                    RecipeIngredient(
                        name=i.get("name", "Ingredient"),
                        amount=float(i.get("amount", 100.0)),
                        unit=i.get("unit", "g"),
                        notes=i.get("notes"),
                        category=i.get("category", "Pantry")
                    )
                    for i in item.get("ingredients", [])
                ]
                steps = [
                    RecipeStep(
                        step_number=int(s.get("step_number", idx + 1)),
                        instruction=s.get("instruction", ""),
                        timer_minutes=s.get("timer_minutes"),
                        tip=s.get("tip")
                    )
                    for idx, s in enumerate(item.get("instructions", []))
                ]
                subs = [
                    IngredientSubstitution(
                        original=sub.get("original", ""),
                        substitute=sub.get("substitute", ""),
                        ratio=sub.get("ratio", "1:1"),
                        notes=sub.get("notes", "")
                    )
                    for sub in item.get("substitutions", [])
                ]
                nutri_raw = item.get("nutrition_per_serving", {})
                macros = MacroNutrients(
                    calories=float(nutri_raw.get("calories", 350.0)),
                    protein=float(nutri_raw.get("protein", 20.0)),
                    carbohydrates=float(nutri_raw.get("carbohydrates", 35.0)),
                    fat=float(nutri_raw.get("fat", 12.0)),
                    saturated_fat=float(nutri_raw.get("saturated_fat", 2.0)),
                    fiber=float(nutri_raw.get("fiber", 4.0)),
                    sugar=float(nutri_raw.get("sugar", 2.0))
                )

                recipes.append(RecipeResponse(
                    recipe_id=rec_id,
                    title=item.get("title", "AI Crafted Dish"),
                    description=item.get("description", "A custom recipe generated by Food Verse AI Chef."),
                    cuisine=item.get("cuisine", "Contemporary"),
                    prep_time_minutes=int(item.get("prep_time_minutes", 10)),
                    cook_time_minutes=int(item.get("cook_time_minutes", 15)),
                    total_time_minutes=int(item.get("total_time_minutes", 25)),
                    servings=req.servings or int(item.get("servings", 2)),
                    base_servings=req.servings or int(item.get("servings", 2)),
                    ingredients=ings,
                    instructions=steps,
                    substitutions=subs,
                    nutrition_per_serving=macros,
                    is_nutrition_calculated=True,
                    dietary_tags=item.get("dietary_tags", []),
                    equipment_needed=item.get("equipment_needed", []),
                    allergens_present=item.get("allergens_present", []),
                    safety_warning="Recipe dynamically synthesized by Gemini AI Chef based on your selected ingredients."
                ))

            return recipes if recipes else None
        except Exception as e:
            logger.error(f"Failed to parse Gemini generated recipes JSON: {e}")
            return None

    def generate_meal_plan_ai(self, profile: MealPlanProfile, duration_days: int = 7) -> Optional[MealPlanResponse]:
        """Synthesizes a tailored daily or 7-day nutritional meal plan with Gemini AI."""
        if not self.is_configured():
            return None

        system_instruction = (
            "You are Food Verse AI Nutritionist, a certified clinical dietitian and meal planner. "
            "You synthesize realistic, delicious, nutritionally balanced meal plans matching the user's specific "
            "dietary preferences, caloric targets, activity levels, and strict allergy exclusions. "
            "Return strictly valid JSON conforming to the requested schema."
        )

        prompt = (
            f"Generate a {duration_days}-day meal plan for a person with:\n"
            f"- Dietary preference: {profile.dietary_preference}\n"
            f"- Health goal: {profile.goal} (e.g. balanced eating, weight loss, muscle gain)\n"
            f"- Strict allergy exclusions (MUST AVOID COMPLETELY): {', '.join(profile.allergies) if profile.allergies else 'None'}\n"
            f"- Age range: {profile.age_range}, Activity level: {profile.activity_level}\n"
            f"- Preferred meals per day: {profile.meals_per_day}\n"
            f"- Preferred cuisines: {', '.join(profile.preferred_cuisines) if profile.preferred_cuisines else 'Any'}\n\n"
            "Return a strictly valid JSON object matching this structure:\n"
            "{\n"
            '  "target_daily_calories": 2000,\n'
            '  "target_protein_grams": 130,\n'
            '  "target_carbs_grams": 220,\n'
            '  "target_fat_grams": 65,\n'
            '  "daily_plans": [\n'
            '    {\n'
            '      "day_number": 1,\n'
            '      "day_name": "Day 1 (Monday)",\n'
            '      "meals": [\n'
            '        {\n'
            '          "meal_id": "m1-d1",\n'
            '          "meal_type": "Breakfast",\n'
            '          "meal_name": "Meal Name",\n'
            '          "description": "Short description",\n'
            '          "ingredients": [\n'
            '            {"name": "Ingredient", "amount": 100.0, "unit": "g", "category": "Produce"}\n'
            '          ],\n'
            '          "nutrition": {"calories": 450, "protein": 28, "carbohydrates": 45, "fat": 15, "fiber": 6, "sugar": 4},\n'
            '          "prep_instructions": ["Step 1", "Step 2"],\n'
            '          "substitutions": [\n'
            '            {"original": "Item", "substitute": "Alternative", "ratio": "1:1", "notes": "note"}\n'
            '          ]\n'
            '        }\n'
            '      ]\n'
            '    }\n'
            '  ],\n'
            '  "consolidated_grocery_list": [\n'
            '    {"name": "Rolled Oats", "quantity_str": "500g", "category": "Grains"},\n'
            '    {"name": "Eggs", "quantity_str": "12 count", "category": "Dairy & Eggs"}\n'
            '  ]\n'
            "}"
        )

        contents = [{"parts": [{"text": prompt}]}]
        raw = self._call_gemini_api(contents, system_instruction=system_instruction, json_mode=True, max_tokens=3500)
        if not raw:
            return None

        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            data = json.loads(cleaned)

            daily_plans: List[DailyPlan] = []
            for d in data.get("daily_plans", []):
                meals: List[PlannedMeal] = []
                day_cals = 0.0
                day_prot = 0.0
                day_carbs = 0.0
                day_fat = 0.0

                for m in d.get("meals", []):
                    n_raw = m.get("nutrition", {})
                    macros = MacroNutrients(
                        calories=float(n_raw.get("calories", 400.0)),
                        protein=float(n_raw.get("protein", 25.0)),
                        carbohydrates=float(n_raw.get("carbohydrates", 40.0)),
                        fat=float(n_raw.get("fat", 14.0)),
                        saturated_fat=float(n_raw.get("saturated_fat", round(float(n_raw.get("fat", 14.0)) * 0.25, 1))),
                        fiber=float(n_raw.get("fiber", 5.0)),
                        sugar=float(n_raw.get("sugar", 3.0))
                    )
                    day_cals += macros.calories
                    day_prot += macros.protein
                    day_carbs += macros.carbohydrates
                    day_fat += macros.fat

                    ings = [
                        RecipeIngredient(
                            name=i.get("name", "Ingredient"),
                            amount=float(i.get("amount", 100.0)),
                            unit=i.get("unit", "g"),
                            category=i.get("category", "Pantry")
                        )
                        for i in m.get("ingredients", [])
                    ]
                    subs = [
                        IngredientSubstitution(
                            original=s.get("original", ""),
                            substitute=s.get("substitute", ""),
                            ratio=s.get("ratio", "1:1"),
                            notes=s.get("notes", "")
                        )
                        for s in m.get("substitutions", [])
                    ]

                    meals.append(PlannedMeal(
                        meal_id=m.get("meal_id", f"meal-{uuid.uuid4().hex[:6]}"),
                        meal_type=m.get("meal_type", "Meal"),
                        meal_name=m.get("meal_name", "Balanced Dish"),
                        description=m.get("description", ""),
                        servings=1,
                        ingredients=ings,
                        nutrition=macros,
                        is_calculated_nutrition=True,
                        prep_instructions=m.get("prep_instructions", ["Assemble fresh ingredients and serve."]),
                        substitutions=subs
                    ))

                daily_plans.append(DailyPlan(
                    day_number=int(d.get("day_number", len(daily_plans) + 1)),
                    day_name=d.get("day_name", f"Day {len(daily_plans) + 1}"),
                    meals=meals,
                    daily_calories=round(day_cals, 1),
                    daily_protein=round(day_prot, 1),
                    daily_carbs=round(day_carbs, 1),
                    daily_fat=round(day_fat, 1)
                ))

            grocery_items = [
                GroceryItem(
                    name=g.get("name", "Item"),
                    quantity_str=g.get("quantity_str", "1 unit"),
                    category=g.get("category", "Pantry"),
                    checked=False
                )
                for g in data.get("consolidated_grocery_list", [])
            ]

            plan_id = f"plan-{uuid.uuid4().hex[:10]}"
            timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            return MealPlanResponse(
                plan_id=plan_id,
                created_at=timestamp_iso,
                duration_days=duration_days,
                profile=profile,
                target_daily_calories=float(data.get("target_daily_calories", 2000)),
                target_protein_grams=float(data.get("target_protein_grams", 120)),
                target_carbs_grams=float(data.get("target_carbs_grams", 220)),
                target_fat_grams=float(data.get("target_fat_grams", 65)),
                daily_plans=daily_plans,
                consolidated_grocery_list=grocery_items,
                medical_disclaimer=(
                    "Informational AI Nutrition Notice: This meal plan is synthesized by Google Gemini AI "
                    "for wellness and informational planning. It does not constitute individualized medical nutrition therapy."
                ),
                is_demo_mode=False
            )
        except Exception as e:
            logger.error(f"Failed to parse Gemini generated meal plan JSON: {e}")
            return None

    def chat_cooking(
        self,
        messages: List[Dict[str, str]],
        available_ingredients: List[str],
        dietary_preference: str = "any",
        allergies: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Conversational culinary AI assistant powered by Gemini."""
        if not self.is_configured():
            return None

        system_instruction = (
            "You are Food Verse AI Chef, an expert Michelin-trained culinary consultant and registered dietitian. "
            "You help users craft appetizing recipes from their pantry ingredients, advise on precise substitutions, "
            "and adjust recipes for cooking equipment (air fryers, cast iron, ovens, instant pots). "
            "Always be practical, engaging, safety-conscious with allergies, and format markdown cleanly with bold headings."
        )

        context_note = f"\nUser's available ingredients: {', '.join(available_ingredients) if available_ingredients else 'None specified'}\n"
        if dietary_preference and dietary_preference != "any":
            context_note += f"Dietary preference: {dietary_preference}\n"
        if allergies:
            context_note += f"Strict allergy exclusions: {', '.join(allergies)}\n"

        prompt_text = (
            f"{context_note}\n"
            "Respond to the user's latest query in helpful culinary detail. "
            "If they ask for a recipe or what to cook with their ingredients, include: "
            "1. Recipe Name\n2. Prep & Cook time\n3. Ingredient list with exact amounts\n"
            "4. Numbered step-by-step instructions\n5. Handy chef tips.\n\n"
            "Also return a JSON block at the very end with format:\n"
            '```json\n{"suggested_followups": ["Question 1?", "Question 2?", "Question 3?"], "extracted_ingredients": [...]}\n```'
        )

        contents = []
        for m in messages[:-1]:
            role = "user" if m.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

        last_msg = messages[-1].get("content", "") if messages else "Hello chef!"
        contents.append({
            "role": "user",
            "parts": [{"text": f"{last_msg}\n\n[Instruction: {prompt_text}]"}]
        })

        raw_response = self._call_gemini_api(contents, system_instruction=system_instruction, json_mode=False, max_tokens=1500)
        if not raw_response:
            return None

        reply = raw_response
        followups = [
            "What can I substitute for the main ingredient?",
            "Can I make this in an air fryer?",
            "How do I scale this recipe for 4 people?"
        ]
        extracted = []

        if "```json" in raw_response:
            try:
                parts = raw_response.split("```json")
                reply_part = parts[0].strip()
                json_part = parts[1].split("```")[0].strip()
                meta = json.loads(json_part)
                if "suggested_followups" in meta and isinstance(meta["suggested_followups"], list):
                    followups = meta["suggested_followups"][:3]
                if "extracted_ingredients" in meta and isinstance(meta["extracted_ingredients"], list):
                    extracted = meta["extracted_ingredients"]
                reply = reply_part
            except Exception:
                pass

        return {
            "reply": reply,
            "suggested_followups": followups,
            "extracted_ingredients": extracted
        }

    def analyze_produce_freshness(self, image_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """Multimodal freshness and decay assessment with Gemini Vision."""
        if not self.is_configured():
            return None

        mime_type = "image/jpeg"
        lower_fn = filename.lower()
        if lower_fn.endswith(".png"):
            mime_type = "image/png"
        elif lower_fn.endswith(".webp"):
            mime_type = "image/webp"

        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        prompt = (
            "Analyze this produce image (fruit or vegetable) for freshness and visual quality. "
            "Return a strictly valid JSON object matching this structure:\n"
            "{\n"
            '  "item_name": "Identified Produce Name",\n'
            '  "produce_category": "Fruit / Vegetable / Leafy Greens / etc",\n'
            '  "freshness_status": "Fresh / Prime" | "Moderate / Consumable Soon" | "Stale / Overripe" | "Spoiled / Discard",\n'
            '  "overall_freshness_score": 85.0,\n'
            '  "model_confidence": 0.94,\n'
            '  "estimated_shelf_life_days": "4 - 6 days refrigerated",\n'
            '  "observations": ["Visible observation 1", "Observation 2"],\n'
            '  "quality_indicators": [\n'
            '    {"feature": "Color & Pigmentation", "observed_value": "Vibrant uniform red", "status": "Good" | "Warning" | "Bad"},\n'
            '    {"feature": "Surface Texture", "observed_value": "Smooth, taut skin", "status": "Good" | "Warning" | "Bad"},\n'
            '    {"feature": "Blemishes / Decay", "observed_value": "No mold or fungal spots", "status": "Good" | "Warning" | "Bad"}\n'
            '  ],\n'
            '  "storage_suggestion": {\n'
            '    "ideal_temperature": "1°C - 4°C",\n'
            '    "ideal_humidity": "90% - 95% RH",\n'
            '    "ethylene_sensitivity": "High or Low ethylene producer details",\n'
            '    "practical_tips": ["Tip 1", "Tip 2"]\n'
            '  }\n'
            "}"
        )

        contents = [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_image
                        }
                    }
                ]
            }
        ]

        raw_response = self._call_gemini_api(contents, json_mode=True, max_tokens=1500)
        if not raw_response:
            return None

        try:
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Failed to parse Gemini Freshness JSON: {e}")
            return None

    def analyze_kitchen_hygiene(self, image_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
        """Multimodal kitchen sanitation & compliance audit with Gemini Vision."""
        if not self.is_configured():
            return None

        mime_type = "image/jpeg"
        lower_fn = filename.lower()
        if lower_fn.endswith(".png"):
            mime_type = "image/png"
        elif lower_fn.endswith(".webp"):
            mime_type = "image/webp"

        b64_image = base64.b64encode(image_bytes).decode("utf-8")

        prompt = (
            "Inspect this commercial/restaurant kitchen image for sanitation and hygiene compliance. "
            "Check for: PPE compliance (hairnets, gloves, clean aprons), food safety (covered food, temperature cues), "
            "cross-contamination risks, floor/counter cleanliness, waste disposal bins. "
            "Return a strictly valid JSON object conforming to:\n"
            "{\n"
            '  "compliance_score": 88.0,\n'
            '  "severity_level": "Compliant" | "Low Risk" | "Moderate Risk" | "High Risk" | "Critical Violation",\n'
            '  "confidence": 0.92,\n'
            '  "summary": "2-sentence audit summary",\n'
            '  "checklist_items": [\n'
            '    {"rule": "Food Storage Protection", "status": "Pass" | "Review" | "Fail", "notes": "Details..."},\n'
            '    {"rule": "Sanitation & Surface Cleanliness", "status": "Pass" | "Review" | "Fail", "notes": "Details..."},\n'
            '    {"rule": "Staff PPE (Gloves & Hairnet)", "status": "Pass" | "Review" | "Fail", "notes": "Details..."},\n'
            '    {"rule": "Waste & Contaminant Separation", "status": "Pass" | "Review" | "Fail", "notes": "Details..."}\n'
            '  ],\n'
            '  "detected_violations": ["Violation 1 if any", "Violation 2 if any"],\n'
            '  "recommended_actions": ["Immediate correction step 1", "Correction step 2"]\n'
            "}"
        )

        contents = [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64_image
                        }
                    }
                ]
            }
        ]

        raw_response = self._call_gemini_api(contents, json_mode=True, max_tokens=1500)
        if not raw_response:
            return None

        try:
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Failed to parse Gemini Hygiene JSON: {e}")
            return None

gemini_service = GeminiService()
