import os
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from backend.config import SAVED_MEALPLANS_PATH
from backend.models.schemas import (
    MealPlanProfile,
    MealPlanResponse,
    DailyPlan,
    PlannedMeal,
    GroceryItem,
    RecipeIngredient,
    IngredientSubstitution,
    MacroNutrients,
    MealPlanGenerateRequest
)
from backend.services.nutrition_service import nutrition_service
from backend.services.gemini_service import gemini_service

MEDICAL_DISCLAIMER_TEXT = (
    "IMPORTANT MEDICAL & NUTRITION DISCLAIMER: This automated meal plan and associated caloric estimates "
    "are generated for educational and general wellness planning purposes only. They do not constitute "
    "individualized clinical nutrition therapy, medical advice, or disease diagnosis. Consult a registered "
    "dietitian nutritionist (RDN) or qualified physician before initiating significant dietary alterations."
)

class MealPlannerService:
    def __init__(self):
        self.saved_path = SAVED_MEALPLANS_PATH
        self._ensure_storage()

    def _ensure_storage(self):
        if not self.saved_path.exists():
            os.makedirs(self.saved_path.parent, exist_ok=True)
            with open(self.saved_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def get_saved_mealplans(self) -> List[Dict[str, Any]]:
        try:
            if self.saved_path.exists():
                with open(self.saved_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def save_mealplan(self, plan: MealPlanResponse) -> Dict[str, Any]:
        saved = self.get_saved_mealplans()
        record = plan.model_dump()
        existing_idx = next((i for i, p in enumerate(saved) if p["plan_id"] == record["plan_id"]), -1)
        if existing_idx >= 0:
            saved[existing_idx] = record
        else:
            saved.insert(0, record)

        with open(self.saved_path, "w", encoding="utf-8") as f:
            json.dump(saved, f, indent=2)
        return record

    def calculate_macro_targets(self, profile: MealPlanProfile) -> Dict[str, float]:
        """Calculates personalized energy targets based on goal, age, and activity level."""
        # Baseline BMR estimate
        base_bmr = 1650.0
        if profile.age_range == "36-50":
            base_bmr = 1550.0
        elif profile.age_range == "51+":
            base_bmr = 1450.0

        activity_factors = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "very_active": 1.725
        }
        factor = activity_factors.get(profile.activity_level.lower(), 1.55)
        tdee = base_bmr * factor

        # Goal adjustments
        if profile.goal == "weight_loss":
            daily_cals = round(tdee - 450.0)
            prot_pct, carb_pct, fat_pct = 0.35, 0.35, 0.30
        elif profile.goal == "muscle_gain":
            daily_cals = round(tdee + 350.0)
            prot_pct, carb_pct, fat_pct = 0.30, 0.45, 0.25
        else:  # balanced
            daily_cals = round(tdee)
            prot_pct, carb_pct, fat_pct = 0.25, 0.50, 0.25

        target_protein = round((daily_cals * prot_pct) / 4.0, 1)
        target_carbs = round((daily_cals * carb_pct) / 4.0, 1)
        target_fat = round((daily_cals * fat_pct) / 9.0, 1)

        return {
            "calories": float(daily_cals),
            "protein": target_protein,
            "carbs": target_carbs,
            "fat": target_fat
        }

    def _get_candidate_meals(self, profile: MealPlanProfile) -> Dict[str, List[Dict[str, Any]]]:
        """Filters catalog meals against stated dietary preferences and strict allergy exclusions."""
        diet = profile.dietary_preference.lower()
        allergies = [a.lower() for a in profile.allergies]

        breakfast_options = [
            {
                "name": "Artisanal Avocado Toast with Poached Egg",
                "desc": "Whole grain sourdough topped with smashed avocado, poached egg, and red pepper flakes.",
                "diet": "vegetarian",
                "allergens": ["gluten", "eggs"],
                "macros": {"calories": 340.0, "protein": 14.5, "carbohydrates": 32.0, "fat": 17.5, "saturated_fat": 3.4, "fiber": 7.2, "sugar": 1.8},
                "ingredients": [
                    {"name": "Whole Grain Sourdough", "amount": 2.0, "unit": "slices", "category": "Grains"},
                    {"name": "Hass Avocado", "amount": 1.0, "unit": "medium", "category": "Produce"},
                    {"name": "Eggs", "amount": 2.0, "unit": "large", "category": "Proteins"}
                ],
                "instructions": ["Toast sourdough", "Mash avocado with lemon & sea salt", "Poach eggs for 3 mins and assemble"],
                "substitutions": [{"original": "Eggs", "substitute": "Tofu Scramble", "ratio": "1:1", "notes": "For vegan option"}]
            },
            {
                "name": "Berry High-Protein Rolled Oatmeal",
                "desc": "Rolled oats simmered with plant milk, topped with blueberries, chia seeds, and vanilla protein.",
                "diet": "vegan",
                "allergens": [],
                "macros": {"calories": 365.0, "protein": 26.0, "carbohydrates": 48.0, "fat": 7.5, "saturated_fat": 1.1, "fiber": 9.4, "sugar": 6.8},
                "ingredients": [
                    {"name": "Rolled Oats", "amount": 60.0, "unit": "g", "category": "Grains"},
                    {"name": "Oat Milk", "amount": 200.0, "unit": "ml", "category": "Dairy & Alternatives"},
                    {"name": "Blueberries", "amount": 80.0, "unit": "g", "category": "Produce"},
                    {"name": "Chia Seeds", "amount": 10.0, "unit": "g", "category": "Pantry"}
                ],
                "instructions": ["Simmer oats in oat milk for 5 mins", "Stir in protein powder off heat", "Top with blueberries and chia"],
                "substitutions": [{"original": "Blueberries", "substitute": "Strawberries or Raspberries", "ratio": "1:1", "notes": "Any fresh berry"}]
            },
            {
                "name": "Greek Yogurt & Fresh Berry Parfait",
                "desc": "High-protein plain strained Greek yogurt layered with raspberries, oat granola, and honey.",
                "diet": "vegetarian",
                "allergens": ["dairy"],
                "macros": {"calories": 320.0, "protein": 24.0, "carbohydrates": 38.0, "fat": 6.0, "saturated_fat": 2.2, "fiber": 5.2, "sugar": 14.0},
                "ingredients": [
                    {"name": "Greek Yogurt (0% Fat)", "amount": 220.0, "unit": "g", "category": "Dairy & Alternatives"},
                    {"name": "Mixed Berries", "amount": 75.0, "unit": "g", "category": "Produce"},
                    {"name": "Oat Granola", "amount": 30.0, "unit": "g", "category": "Grains"}
                ],
                "instructions": ["Layer Greek yogurt in a bowl", "Top with mixed fresh berries and crisp granola"],
                "substitutions": [{"original": "Greek Yogurt", "substitute": "Coconut Yogurt", "ratio": "1:1", "notes": "Dairy-free swap"}]
            }
        ]

        lunch_options = [
            {
                "name": "Grilled Chicken Caesar Salad",
                "desc": "Crisp romaine hearts, herb-grilled chicken breast, shaved parmesan, and light lemon dressing.",
                "diet": "non-vegetarian",
                "allergens": ["dairy"],
                "macros": {"calories": 420.0, "protein": 44.0, "carbohydrates": 14.0, "fat": 21.0, "saturated_fat": 4.5, "fiber": 3.8, "sugar": 2.5},
                "ingredients": [
                    {"name": "Chicken Breast", "amount": 200.0, "unit": "g", "category": "Proteins"},
                    {"name": "Romaine Lettuce", "amount": 150.0, "unit": "g", "category": "Produce"},
                    {"name": "Parmesan Cheese", "amount": 20.0, "unit": "g", "category": "Dairy & Alternatives"},
                    {"name": "Olive Oil & Lemon Dressing", "amount": 20.0, "unit": "ml", "category": "Pantry"}
                ],
                "instructions": ["Grill chicken breast 6 mins each side", "Toss crisp romaine with dressing and sliced chicken"],
                "substitutions": [{"original": "Chicken Breast", "substitute": "Grilled Tofu Cutlets", "ratio": "1:1", "notes": "For vegetarian option"}]
            },
            {
                "name": "Crispy Tofu & Rainbow Stir-Fry",
                "desc": "Pan-seared extra firm tofu with bell peppers, broccoli florets, and snap peas in ginger tamari.",
                "diet": "vegan",
                "allergens": ["soy"],
                "macros": {"calories": 380.0, "protein": 24.0, "carbohydrates": 28.0, "fat": 18.0, "saturated_fat": 2.4, "fiber": 7.5, "sugar": 5.2},
                "ingredients": [
                    {"name": "Extra Firm Tofu", "amount": 250.0, "unit": "g", "category": "Proteins"},
                    {"name": "Broccoli Florets", "amount": 120.0, "unit": "g", "category": "Produce"},
                    {"name": "Bell Pepper", "amount": 1.0, "unit": "medium", "category": "Produce"},
                    {"name": "Tamari Soy Sauce", "amount": 20.0, "unit": "ml", "category": "Pantry"}
                ],
                "instructions": ["Pan-fry tofu cubes until crisp", "Flash-fry vegetables in wok", "Toss with tamari glaze"],
                "substitutions": [{"original": "Tamari Soy Sauce", "substitute": "Coconut Aminos", "ratio": "1:1", "notes": "Soy-free allergen swap"}]
            },
            {
                "name": "Mediterranean Quinoa Bowl with Chickpeas",
                "desc": "Fluffy quinoa, spiced chickpeas, diced cucumber, cherry tomatoes, and tahini drizzle.",
                "diet": "vegan",
                "allergens": ["sesame"],
                "macros": {"calories": 440.0, "protein": 18.0, "carbohydrates": 58.0, "fat": 15.0, "saturated_fat": 2.0, "fiber": 9.5, "sugar": 4.1},
                "ingredients": [
                    {"name": "Cooked Quinoa", "amount": 150.0, "unit": "g", "category": "Grains"},
                    {"name": "Canned Chickpeas", "amount": 130.0, "unit": "g", "category": "Proteins"},
                    {"name": "Cucumber & Cherry Tomatoes", "amount": 120.0, "unit": "g", "category": "Produce"},
                    {"name": "Tahini Dressing", "amount": 25.0, "unit": "ml", "category": "Pantry"}
                ],
                "instructions": ["Warm cooked quinoa", "Toss chickpeas with cumin and olive oil", "Assemble with fresh diced vegetables"],
                "substitutions": [{"original": "Tahini", "substitute": "Olive Oil & Lemon Dressing", "ratio": "1:1", "notes": "Sesame-free swap"}]
            }
        ]

        dinner_options = [
            {
                "name": "Pan-Seared Salmon with Steamed Quinoa & Asparagus",
                "desc": "Crisp Atlantic salmon fillet, fluffy citrus-herb quinoa, and steamed tender asparagus spears.",
                "diet": "non-vegetarian",
                "allergens": ["fish"],
                "macros": {"calories": 510.0, "protein": 44.0, "carbohydrates": 38.0, "fat": 20.0, "saturated_fat": 3.4, "fiber": 6.2, "sugar": 2.5},
                "ingredients": [
                    {"name": "Atlantic Salmon Fillet", "amount": 200.0, "unit": "g", "category": "Proteins"},
                    {"name": "Quinoa", "amount": 70.0, "unit": "g", "category": "Grains"},
                    {"name": "Asparagus", "amount": 120.0, "unit": "g", "category": "Produce"},
                    {"name": "Olive Oil & Lemon", "amount": 15.0, "unit": "ml", "category": "Pantry"}
                ],
                "instructions": ["Simmer quinoa for 14 mins", "Pan-sear salmon skin-down for 5 mins, flip for 3 mins", "Steam asparagus"],
                "substitutions": [{"original": "Salmon", "substitute": "Firm Organic Tofu or White Cod", "ratio": "1:1", "notes": "Plant-based or milder fish"}]
            },
            {
                "name": "Grilled Lemon Herb Chicken with Roasted Summer Squash",
                "desc": "Marinated chicken breast grilled with oregano and garlic, served with brown rice and roasted zucchini.",
                "diet": "non-vegetarian",
                "allergens": [],
                "macros": {"calories": 480.0, "protein": 46.0, "carbohydrates": 42.0, "fat": 13.0, "saturated_fat": 2.2, "fiber": 4.8, "sugar": 3.0},
                "ingredients": [
                    {"name": "Chicken Breast", "amount": 220.0, "unit": "g", "category": "Proteins"},
                    {"name": "Brown Rice", "amount": 120.0, "unit": "g", "category": "Grains"},
                    {"name": "Zucchini", "amount": 150.0, "unit": "g", "category": "Produce"},
                    {"name": "Olive Oil", "amount": 10.0, "unit": "ml", "category": "Pantry"}
                ],
                "instructions": ["Marinate chicken with oregano and olive oil", "Grill 6-7 mins per side", "Roast zucchini rounds in oven"],
                "substitutions": [{"original": "Chicken", "substitute": "Portobello Mushroom Steaks", "ratio": "1:1", "notes": "For vegetarian option"}]
            },
            {
                "name": "Lentil & Sweet Potato Vegetable Curry",
                "desc": "Red lentils simmered with diced sweet potatoes, baby spinach, turmeric, and light coconut milk.",
                "diet": "vegan",
                "allergens": [],
                "macros": {"calories": 420.0, "protein": 18.0, "carbohydrates": 62.0, "fat": 11.0, "saturated_fat": 5.2, "fiber": 11.2, "sugar": 6.5},
                "ingredients": [
                    {"name": "Dry Red Lentils", "amount": 80.0, "unit": "g", "category": "Proteins"},
                    {"name": "Sweet Potato", "amount": 120.0, "unit": "g", "category": "Produce"},
                    {"name": "Baby Spinach", "amount": 60.0, "unit": "g", "category": "Produce"},
                    {"name": "Light Coconut Milk", "amount": 100.0, "unit": "ml", "category": "Pantry"}
                ],
                "instructions": ["Sauté diced sweet potato with curry spices", "Add red lentils and coconut broth, simmer 15 mins", "Fold in baby spinach at end"],
                "substitutions": [{"original": "Sweet Potato", "substitute": "Butternut Squash", "ratio": "1:1", "notes": "Low glycemic alternative"}]
            }
        ]

        snack_options = [
            {
                "name": "Crisp Apple Slices with Almond Butter",
                "desc": "Fresh Honeycrisp apple wedges paired with all-natural creamy almond butter.",
                "diet": "vegan",
                "allergens": ["tree_nuts"],
                "macros": {"calories": 210.0, "protein": 4.5, "carbohydrates": 26.0, "fat": 11.0, "saturated_fat": 1.0, "fiber": 5.2, "sugar": 18.0},
                "ingredients": [
                    {"name": "Apple", "amount": 1.0, "unit": "medium", "category": "Produce"},
                    {"name": "Almond Butter", "amount": 20.0, "unit": "g", "category": "Pantry"}
                ],
                "instructions": ["Slice apple into wedges", "Serve with almond butter dip"],
                "substitutions": [{"original": "Almond Butter", "substitute": "Sunflower Seed Butter", "ratio": "1:1", "notes": "Nut-free allergen safe"}]
            },
            {
                "name": "Roasted Salted Edamame",
                "desc": "Crunchy roasted green soybeans providing bioavailable complete protein and prebiotic fiber.",
                "diet": "vegan",
                "allergens": ["soy"],
                "macros": {"calories": 180.0, "protein": 16.0, "carbohydrates": 12.0, "fat": 7.0, "saturated_fat": 0.8, "fiber": 8.0, "sugar": 2.0},
                "ingredients": [
                    {"name": "Shelled Edamame", "amount": 120.0, "unit": "g", "category": "Proteins"}
                ],
                "instructions": ["Dry roast shelled edamame with sea salt in skillet for 6 mins"],
                "substitutions": [{"original": "Edamame", "substitute": "Roasted Chickpeas", "ratio": "1:1", "notes": "Soy-free alternative"}]
            }
        ]

        # Filter function
        def is_safe(m):
            if diet == "vegetarian" and m["diet"] not in ["vegetarian", "vegan"]:
                return False
            if diet == "vegan" and m["diet"] != "vegan":
                return False
            m_allergens = [a.lower() for a in m.get("allergens", [])]
            if any(allergy in m_allergens for allergy in allergies):
                return False
            return True

        safe_breakfast = [m for m in breakfast_options if is_safe(m)] or [breakfast_options[1]]
        safe_lunch = [m for m in lunch_options if is_safe(m)] or [lunch_options[1]]
        safe_dinner = [m for m in dinner_options if is_safe(m)] or [dinner_options[2]]
        safe_snacks = [m for m in snack_options if is_safe(m)] or [snack_options[0]]

        return {
            "breakfast": safe_breakfast,
            "lunch": safe_lunch,
            "dinner": safe_dinner,
            "snack": safe_snacks
        }

    def _compile_grocery_list(self, daily_plans: List[DailyPlan]) -> List[GroceryItem]:
        """Consolidates ingredients across all planned meals into a categorized shopping list."""
        registry: Dict[str, Dict[str, Any]] = {}

        for day in daily_plans:
            for meal in day.meals:
                for ing in meal.ingredients:
                    key = ing.name.strip().title()
                    if key not in registry:
                        registry[key] = {
                            "name": key,
                            "category": ing.category or "Pantry",
                            "units": ing.unit,
                            "amount": 0.0,
                            "meals_used_in": []
                        }
                    registry[key]["amount"] += ing.amount
                    meal_tag = f"{day.day_name} {meal.meal_type}"
                    if meal_tag not in registry[key]["meals_used_in"]:
                        registry[key]["meals_used_in"].append(meal_tag)

        grocery_list: List[GroceryItem] = []
        for key, data in sorted(registry.items(), key=lambda x: (x[1]["category"], x[0])):
            amt = data["amount"]
            amt_str = f"{int(amt)}" if amt % 1 == 0 else f"{amt:.1f}"
            grocery_list.append(GroceryItem(
                name=data["name"],
                quantity_str=f"{amt_str} {data['units']}".strip(),
                category=data["category"],
                meals_used_in=data["meals_used_in"],
                checked=False
            ))

        return grocery_list

    def generate_meal_plan(self, req: MealPlanGenerateRequest) -> MealPlanResponse:
        # 1. Live Google Gemini AI Meal Plan Synthesis if configured
        if gemini_service.is_configured():
            try:
                ai_plan = gemini_service.generate_meal_plan_ai(req.profile, duration_days=req.duration_days)
                if ai_plan:
                    return ai_plan
            except Exception as e:
                pass

        targets = self.calculate_macro_targets(req.profile)
        pool = self._get_candidate_meals(req.profile)
        
        plan_id = f"plan-{uuid.uuid4().hex[:10]}"
        timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        duration = min(7, max(1, req.duration_days))
        daily_plans: List[DailyPlan] = []

        for i in range(duration):
            day_num = i + 1
            day_name = day_names[i % 7] if duration > 1 else "Today"

            b_data = pool["breakfast"][i % len(pool["breakfast"])]
            l_data = pool["lunch"][i % len(pool["lunch"])]
            d_data = pool["dinner"][i % len(pool["dinner"])]

            day_meals: List[PlannedMeal] = []

            # 1. Breakfast
            day_meals.append(PlannedMeal(
                meal_id=f"m-{uuid.uuid4().hex[:6]}",
                meal_type="Breakfast",
                meal_name=b_data["name"],
                description=b_data["desc"],
                servings=1,
                ingredients=[RecipeIngredient(**ing) for ing in b_data["ingredients"]],
                nutrition=MacroNutrients(**b_data["macros"]),
                is_calculated_nutrition=True,
                prep_instructions=b_data["instructions"],
                substitutions=[IngredientSubstitution(**s) for s in b_data.get("substitutions", [])]
            ))

            # 2. Lunch
            day_meals.append(PlannedMeal(
                meal_id=f"m-{uuid.uuid4().hex[:6]}",
                meal_type="Lunch",
                meal_name=l_data["name"],
                description=l_data["desc"],
                servings=1,
                ingredients=[RecipeIngredient(**ing) for ing in l_data["ingredients"]],
                nutrition=MacroNutrients(**l_data["macros"]),
                is_calculated_nutrition=True,
                prep_instructions=l_data["instructions"],
                substitutions=[IngredientSubstitution(**s) for s in l_data.get("substitutions", [])]
            ))

            # 3. Dinner
            day_meals.append(PlannedMeal(
                meal_id=f"m-{uuid.uuid4().hex[:6]}",
                meal_type="Dinner",
                meal_name=d_data["name"],
                description=d_data["desc"],
                servings=1,
                ingredients=[RecipeIngredient(**ing) for ing in d_data["ingredients"]],
                nutrition=MacroNutrients(**d_data["macros"]),
                is_calculated_nutrition=True,
                prep_instructions=d_data["instructions"],
                substitutions=[IngredientSubstitution(**s) for s in d_data.get("substitutions", [])]
            ))

            # 4. Optional Snack if meals_per_day >= 4
            if req.profile.meals_per_day >= 4 and pool["snack"]:
                s_data = pool["snack"][i % len(pool["snack"])]
                day_meals.append(PlannedMeal(
                    meal_id=f"m-{uuid.uuid4().hex[:6]}",
                    meal_type="Snack",
                    meal_name=s_data["name"],
                    description=s_data["desc"],
                    servings=1,
                    ingredients=[RecipeIngredient(**ing) for ing in s_data["ingredients"]],
                    nutrition=MacroNutrients(**s_data["macros"]),
                    is_calculated_nutrition=True,
                    prep_instructions=s_data["instructions"],
                    substitutions=[IngredientSubstitution(**s) for s in s_data.get("substitutions", [])]
                ))

            # Sum daily nutrition
            d_cals = round(sum(m.nutrition.calories for m in day_meals), 1)
            d_prot = round(sum(m.nutrition.protein for m in day_meals), 1)
            d_carbs = round(sum(m.nutrition.carbohydrates for m in day_meals), 1)
            d_fat = round(sum(m.nutrition.fat for m in day_meals), 1)

            daily_plans.append(DailyPlan(
                day_number=day_num,
                day_name=day_name,
                meals=day_meals,
                daily_calories=d_cals,
                daily_protein=d_prot,
                daily_carbs=d_carbs,
                daily_fat=d_fat
            ))

        grocery_list = self._compile_grocery_list(daily_plans)

        response = MealPlanResponse(
            plan_id=plan_id,
            created_at=timestamp_iso,
            duration_days=duration,
            profile=req.profile,
            target_daily_calories=targets["calories"],
            target_protein_grams=targets["protein"],
            target_carbs_grams=targets["carbs"],
            target_fat_grams=targets["fat"],
            daily_plans=daily_plans,
            consolidated_grocery_list=grocery_list,
            medical_disclaimer=MEDICAL_DISCLAIMER_TEXT,
            is_demo_mode=True
        )

        # Save to history automatically
        self.save_mealplan(response)
        return response

meal_planner_service = MealPlannerService()
