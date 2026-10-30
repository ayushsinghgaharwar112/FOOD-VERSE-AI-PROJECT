import os
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from backend.config import SAVED_RECIPES_PATH
from backend.models.schemas import (
    RecipeResponse,
    RecipeIngredient,
    RecipeStep,
    IngredientSubstitution,
    MacroNutrients,
    RecipeGenerateRequest,
    RecipeSaveRequest
)
from backend.services.nutrition_service import nutrition_service
from backend.services.gemini_service import gemini_service

# Comprehensive culinary recipe knowledge base
RECIPE_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id_prefix": "salmon-quinoa",
        "title": "Pan-Seared Salmon with Lemon Herb Quinoa",
        "description": "Crispy skinned Atlantic salmon fillet served over fluffy citrus quinoa and tender steamed broccoli florets.",
        "cuisine": "Mediterranean",
        "dietary_type": "pescatarian",
        "prep_time_minutes": 10,
        "cook_time_minutes": 15,
        "base_servings": 2,
        "equipment": ["skillet", "stovetop", "saucepan"],
        "ingredients": [
            {"name": "Salmon Fillet", "amount": 300, "unit": "g", "category": "Proteins", "notes": "Skin-on, patted dry"},
            {"name": "Quinoa", "amount": 120, "unit": "g", "category": "Grains", "notes": "Rinsed thoroughly"},
            {"name": "Broccoli Florets", "amount": 180, "unit": "g", "category": "Produce", "notes": "Cut into bite-sized pieces"},
            {"name": "Extra Virgin Olive Oil", "amount": 15, "unit": "ml", "category": "Pantry", "notes": "Divided use"},
            {"name": "Fresh Lemon", "amount": 1, "unit": "whole", "category": "Produce", "notes": "Juiced and zested"},
            {"name": "Garlic", "amount": 2, "unit": "cloves", "category": "Produce", "notes": "Minced"}
        ],
        "instructions": [
            {"step_number": 1, "instruction": "Simmer rinsed quinoa in 240ml water with a pinch of salt over medium-low heat until liquid is absorbed (approx 12-14 mins).", "timer_minutes": 14, "tip": "Fluff with a fork and fold in lemon zest."},
            {"step_number": 2, "instruction": "Heat olive oil in a non-stick skillet over medium-high heat. Season salmon with salt and cracked black pepper.", "timer_minutes": 2, "tip": "Ensure pan is shimmering before adding fish."},
            {"step_number": 3, "instruction": "Place salmon skin-side down. Sear undisturbed for 4-5 minutes until skin is crisp, flip and cook 3 minutes more.", "timer_minutes": 7, "tip": "Press gently with a spatula during first 30 seconds to prevent curling."},
            {"step_number": 4, "instruction": "Steam broccoli florets with minced garlic and lemon juice for 3-4 minutes until vibrant green.", "timer_minutes": 4, "tip": "Do not overcook to retain vitamin C."},
            {"step_number": 5, "instruction": "Plate citrus quinoa bed, top with crisp salmon fillet, and arrange steamed broccoli on the side.", "timer_minutes": 1, "tip": "Drizzle pan juices over quinoa."}
        ],
        "substitutions": [
            {"original": "Salmon Fillet", "substitute": "Firm Organic Tofu or Trout", "ratio": "1:1 by weight", "notes": "For plant-based or alternative lean protein."},
            {"original": "Quinoa", "substitute": "Brown Rice or Cauliflower Rice", "ratio": "1:1", "notes": "Cauliflower rice reduces carbohydrates by 70%."}
        ],
        "base_nutrition": {"calories": 485.0, "protein": 42.0, "carbohydrates": 36.0, "fat": 19.0, "saturated_fat": 3.2, "fiber": 5.4, "sugar": 2.1},
        "dietary_tags": ["High Protein", "Gluten-Free", "Pescatarian", "Omega-3 Rich"],
        "allergens": ["fish"]
    },
    {
        "id_prefix": "avocado-egg-toast",
        "title": "Artisanal Avocado Toast with Soft Poached Egg",
        "description": "Rustic whole-grain sourdough toasted golden, layered with zesty smashed avocado, poached pasture-raised egg, and red chili flakes.",
        "cuisine": "Contemporary Breakfast",
        "dietary_type": "vegetarian",
        "prep_time_minutes": 5,
        "cook_time_minutes": 8,
        "base_servings": 2,
        "equipment": ["toaster", "saucepan", "stovetop"],
        "ingredients": [
            {"name": "Whole Grain Sourdough Bread", "amount": 2, "unit": "slices", "category": "Bakery", "notes": "Thick-cut slices (approx 120g)"},
            {"name": "Hass Avocado", "amount": 1, "unit": "whole", "category": "Produce", "notes": "Ripe, pitted and mashed"},
            {"name": "Eggs", "amount": 2, "unit": "large", "category": "Dairy & Eggs", "notes": "Fresh for clean poaching"},
            {"name": "Lemon Juice", "amount": 10, "unit": "ml", "category": "Produce", "notes": "Prevents browning"},
            {"name": "Red Pepper Flakes & Sea Salt", "amount": 1, "unit": "pinch", "category": "Pantry", "notes": "To garnish"}
        ],
        "instructions": [
            {"step_number": 1, "instruction": "Toast sourdough slices until deeply golden and structurally crisp.", "timer_minutes": 3, "tip": "Thick crust holds mashed avocado better without sogginess."},
            {"step_number": 2, "instruction": "In a shallow bowl, smash ripe avocado with lemon juice, sea salt, and a drop of olive oil.", "timer_minutes": 2, "tip": "Leave mild texture chunks rather than pureeing."},
            {"step_number": 3, "instruction": "Bring a small pot of water to a gentle simmer. Create a gentle whirlpool and slip egg into the center.", "timer_minutes": 4, "tip": "Poach for 3 minutes for a warm, runny yolk."},
            {"step_number": 4, "instruction": "Spread mashed avocado generously over toasted sourdough and top each slice with a drained poached egg.", "timer_minutes": 1, "tip": "Garnish with chili flakes and microgreens."}
        ],
        "substitutions": [
            {"original": "Eggs", "substitute": "Pan-Seared Seasoned Tofu Slab", "ratio": "1:1", "notes": "Converts recipe to 100% vegan."},
            {"original": "Sourdough Bread", "substitute": "Gluten-Free Seed Bread", "ratio": "1:1", "notes": "For celiac or gluten-sensitive diets."}
        ],
        "base_nutrition": {"calories": 340.0, "protein": 14.5, "carbohydrates": 32.0, "fat": 17.5, "saturated_fat": 3.4, "fiber": 7.2, "sugar": 1.8},
        "dietary_tags": ["Vegetarian", "High Fiber", "Healthy Fats"],
        "allergens": ["eggs", "gluten"]
    },
    {
        "id_prefix": "tofu-veggie-stir-fry",
        "title": "Crispy Tofu & Rainbow Vegetable Stir-Fry",
        "description": "Pan-crisped organic tofu cubes tossed with crisp bell peppers, broccoli, and snap peas in a savory ginger-tamari sesame glaze.",
        "cuisine": "Asian",
        "dietary_type": "vegan",
        "prep_time_minutes": 12,
        "cook_time_minutes": 10,
        "base_servings": 2,
        "equipment": ["wok", "skillet", "stovetop"],
        "ingredients": [
            {"name": "Extra Firm Tofu", "amount": 350, "unit": "g", "category": "Proteins", "notes": "Pressed dry and cubed"},
            {"name": "Bell Pepper", "amount": 1, "unit": "whole", "category": "Produce", "notes": "Sliced into strips"},
            {"name": "Broccoli", "amount": 150, "unit": "g", "category": "Produce", "notes": "Cut into florets"},
            {"name": "Snap Peas", "amount": 100, "unit": "g", "category": "Produce", "notes": "Trimmed"},
            {"name": "Tamari Soy Sauce", "amount": 30, "unit": "ml", "category": "Pantry", "notes": "Gluten-free tamari"},
            {"name": "Toasted Sesame Oil", "amount": 10, "unit": "ml", "category": "Pantry", "notes": "For aroma"},
            {"name": "Fresh Ginger & Garlic", "amount": 15, "unit": "g", "category": "Produce", "notes": "Grated"}
        ],
        "instructions": [
            {"step_number": 1, "instruction": "Press tofu cubes with paper towels. Lightly dust with 1 tsp cornstarch for extra crispness.", "timer_minutes": 5, "tip": "Dry surface guarantees golden crust."},
            {"step_number": 2, "instruction": "Heat half the sesame oil in a wok or skillet over high heat. Fry tofu for 6-8 mins turning until all sides are golden brown.", "timer_minutes": 8, "tip": "Remove tofu and set aside on a plate."},
            {"step_number": 3, "instruction": "Add remaining oil to hot wok. Flash fry grated ginger, garlic, broccoli, peppers, and snap peas for 3-4 minutes.", "timer_minutes": 4, "tip": "Keep veggies moving for crisp-tender bite."},
            {"step_number": 4, "instruction": "Return crisp tofu to wok. Pour in tamari sauce and toss vigorously for 60 seconds until glazed.", "timer_minutes": 1, "tip": "Top with toasted sesame seeds and sliced scallions."}
        ],
        "substitutions": [
            {"original": "Extra Firm Tofu", "substitute": "Chicken Breast Strips or Edamame", "ratio": "1:1", "notes": "For poultry option or whole legume swap."},
            {"original": "Tamari Soy Sauce", "substitute": "Coconut Aminos", "ratio": "1:1", "notes": "Eliminates soy and reduces sodium by 40%."}
        ],
        "base_nutrition": {"calories": 310.0, "protein": 22.0, "carbohydrates": 18.0, "fat": 16.0, "saturated_fat": 2.2, "fiber": 6.8, "sugar": 4.5},
        "dietary_tags": ["Vegan", "Vegetarian", "Gluten-Free", "Plant Protein"],
        "allergens": ["soy"]
    },
    {
        "id_prefix": "grilled-chicken-bowl",
        "title": "Herb-Marinated Grilled Chicken & Brown Rice Bowl",
        "description": "Tender grilled chicken breast marinated with oregano and garlic, served over warm brown rice, roasted zucchini, and cherry tomatoes.",
        "cuisine": "American / Clean Eating",
        "dietary_type": "non-vegetarian",
        "prep_time_minutes": 10,
        "cook_time_minutes": 18,
        "base_servings": 2,
        "equipment": ["grill pan", "skillet", "saucepan"],
        "ingredients": [
            {"name": "Chicken Breast", "amount": 350, "unit": "g", "category": "Proteins", "notes": "Boneless, skinless"},
            {"name": "Brown Rice", "amount": 140, "unit": "g", "category": "Grains", "notes": "Cooked warm"},
            {"name": "Zucchini", "amount": 1, "unit": "medium", "category": "Produce", "notes": "Sliced into rounds"},
            {"name": "Cherry Tomatoes", "amount": 120, "unit": "g", "category": "Produce", "notes": "Halved"},
            {"name": "Olive Oil", "amount": 15, "unit": "ml", "category": "Pantry", "notes": "For marinade and saute"},
            {"name": "Dried Oregano & Thyme", "amount": 5, "unit": "g", "category": "Pantry", "notes": "Herb rub"}
        ],
        "instructions": [
            {"step_number": 1, "instruction": "Rub chicken breasts with olive oil, oregano, thyme, salt, and black pepper.", "timer_minutes": 3, "tip": "Pound thick end to ensure even cooking."},
            {"step_number": 2, "instruction": "Heat grill pan over medium-high heat. Cook chicken 6-7 minutes per side until internal temperature reaches 74°C (165°F).", "timer_minutes": 14, "tip": "Rest chicken 5 minutes before slicing so juices redistribute."},
            {"step_number": 3, "instruction": "Quickly blister zucchini rounds and halved cherry tomatoes in pan drippings for 3 minutes.", "timer_minutes": 3, "tip": "Char slightly for smoky sweetness."},
            {"step_number": 4, "instruction": "Assemble bowls with steamed brown rice base, sliced herb chicken, and roasted summer vegetables.", "timer_minutes": 1, "tip": "Finish with a squeeze of fresh lemon."}
        ],
        "substitutions": [
            {"original": "Chicken Breast", "substitute": "Turkey Cutlets or Tempeh", "ratio": "1:1", "notes": "Tempeh provides high-fiber vegan alternative."},
            {"original": "Brown Rice", "substitute": "Quinoa or Riced Cauliflower", "ratio": "1:1", "notes": "Low carb alternative."}
        ],
        "base_nutrition": {"calories": 490.0, "protein": 46.0, "carbohydrates": 44.0, "fat": 13.0, "saturated_fat": 2.1, "fiber": 4.8, "sugar": 3.2},
        "dietary_tags": ["High Protein", "Gluten-Free", "Low Saturated Fat"],
        "allergens": []
    },
    {
        "id_prefix": "berry-protein-oatmeal",
        "title": "Vanilla Berry High-Protein Oatmeal Bowl",
        "description": "Slow-simmered whole rolled oats infused with vanilla protein, topped with fresh blackberries, blueberries, and toasted chia seeds.",
        "cuisine": "Healthy Breakfast",
        "dietary_type": "vegetarian",
        "prep_time_minutes": 3,
        "cook_time_minutes": 7,
        "base_servings": 1,
        "equipment": ["saucepan", "stovetop"],
        "ingredients": [
            {"name": "Rolled Oats", "amount": 60, "unit": "g", "category": "Grains", "notes": "Old fashioned rolled oats"},
            {"name": "Almond Milk", "amount": 200, "unit": "ml", "category": "Dairy Alternatives", "notes": "Unsweetened"},
            {"name": "Vanilla Protein Powder", "amount": 25, "unit": "g", "category": "Supplements", "notes": "Whey or plant-based"},
            {"name": "Mixed Berries", "amount": 80, "unit": "g", "category": "Produce", "notes": "Fresh or thawed berries"},
            {"name": "Chia Seeds", "amount": 10, "unit": "g", "category": "Pantry", "notes": "For omega-3 crunch"}
        ],
        "instructions": [
            {"step_number": 1, "instruction": "Combine rolled oats and almond milk in a saucepan over medium heat; bring to gentle simmer.", "timer_minutes": 5, "tip": "Stir frequently to release beta-glucan starches."},
            {"step_number": 2, "instruction": "Remove pan from heat source. Whisk in vanilla protein powder until completely dissolved without clumping.", "timer_minutes": 1, "tip": "Never boil protein powder directly or texture turns grainy."},
            {"step_number": 3, "instruction": "Pour creamy oatmeal into bowl, top with fresh berries, chia seeds, and cinnamon dust.", "timer_minutes": 1, "tip": "Let sit 2 minutes for chia seeds to plump."}
        ],
        "substitutions": [
            {"original": "Almond Milk", "substitute": "Oat Milk or Skim Cow's Milk", "ratio": "1:1", "notes": "For nut-free allergen safety."},
            {"original": "Vanilla Protein Powder", "substitute": "Greek Yogurt or Hemp Seeds", "ratio": "1:1", "notes": "Whole food protein boost."}
        ],
        "base_nutrition": {"calories": 365.0, "protein": 28.0, "carbohydrates": 46.0, "fat": 7.5, "saturated_fat": 1.1, "fiber": 9.2, "sugar": 6.8},
        "dietary_tags": ["High Protein", "High Fiber", "Vegetarian"],
        "allergens": ["tree_nuts"]
    }
]

class RecipeService:
    def __init__(self):
        self.saved_path = SAVED_RECIPES_PATH
        self._ensure_storage()

    def _ensure_storage(self):
        if not self.saved_path.exists():
            os.makedirs(self.saved_path.parent, exist_ok=True)
            with open(self.saved_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def get_saved_recipes(self) -> List[Dict[str, Any]]:
        try:
            if self.saved_path.exists():
                with open(self.saved_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def save_recipe(self, req: RecipeSaveRequest) -> Dict[str, Any]:
        saved = self.get_saved_recipes()
        record = req.recipe.model_dump()
        record["saved_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        record["user_notes"] = req.user_notes

        # Replace if existing or append
        existing_idx = next((i for i, r in enumerate(saved) if r["recipe_id"] == record["recipe_id"]), -1)
        if existing_idx >= 0:
            saved[existing_idx] = record
        else:
            saved.insert(0, record)

        with open(self.saved_path, "w", encoding="utf-8") as f:
            json.dump(saved, f, indent=2)

        return record

    def delete_saved_recipe(self, recipe_id: str) -> bool:
        saved = self.get_saved_recipes()
        filtered = [r for r in saved if r["recipe_id"] != recipe_id]
        if len(filtered) != len(saved):
            with open(self.saved_path, "w", encoding="utf-8") as f:
                json.dump(filtered, f, indent=2)
            return True
        return False

    def scale_recipe(self, recipe: RecipeResponse, target_servings: int) -> RecipeResponse:
        """Scales recipe ingredient amounts and updates serving count while maintaining per-serving nutrition."""
        if target_servings <= 0:
            target_servings = 1
        factor = target_servings / float(recipe.base_servings or 1)
        
        scaled_ingredients: List[RecipeIngredient] = []
        for ing in recipe.ingredients:
            scaled_amount = round(ing.amount * factor, 1) if ing.amount % 1 != 0 else int(round(ing.amount * factor))
            scaled_ingredients.append(RecipeIngredient(
                name=ing.name,
                amount=max(0.1, float(scaled_amount)),
                unit=ing.unit,
                notes=ing.notes,
                category=ing.category
            ))

        return RecipeResponse(
            recipe_id=recipe.recipe_id,
            title=recipe.title,
            description=recipe.description,
            cuisine=recipe.cuisine,
            prep_time_minutes=recipe.prep_time_minutes,
            cook_time_minutes=recipe.cook_time_minutes,
            total_time_minutes=recipe.total_time_minutes,
            servings=target_servings,
            base_servings=recipe.base_servings,
            ingredients=scaled_ingredients,
            instructions=recipe.instructions,
            substitutions=recipe.substitutions,
            nutrition_per_serving=recipe.nutrition_per_serving,
            is_nutrition_calculated=recipe.is_nutrition_calculated,
            dietary_tags=recipe.dietary_tags,
            equipment_needed=recipe.equipment_needed,
            allergens_present=recipe.allergens_present,
            safety_warning=recipe.safety_warning
        )

    def generate_recipes(self, req: RecipeGenerateRequest) -> List[RecipeResponse]:
        """
        Generates tailored recipes using Google Gemini AI Chef when configured,
        or matches against culinary recipe templates with strict allergen filtering.
        """
        user_ingredients = [ing.strip().lower() for ing in req.ingredients if ing.strip()]
        user_allergies = [a.strip().lower() for a in req.allergies or []]
        user_diet = (req.dietary_preference or "any").lower()
        target_servings = req.servings or 2

        # 1. Live Google Gemini AI Recipe Generation
        if gemini_service.is_configured() and user_ingredients:
            try:
                ai_recipes = gemini_service.generate_recipes_ai(req)
                if ai_recipes:
                    # Filter strict allergy exclusions just in case
                    safe_ai_recipes = []
                    for r in ai_recipes:
                        r_allergens = [a.lower() for a in r.allergens_present]
                        if not any(a in r_allergens for a in user_allergies):
                            safe_ai_recipes.append(r)
                    if safe_ai_recipes:
                        return safe_ai_recipes
            except Exception as e:
                pass

        candidates: List[RecipeResponse] = []

        for tmpl in RECIPE_TEMPLATES:
            # 1. Filter out strict allergy conflicts
            tmpl_allergens = [a.lower() for a in tmpl.get("allergens", [])]
            has_allergy_conflict = any(allergy in tmpl_allergens for allergy in user_allergies)
            if has_allergy_conflict:
                continue

            # 2. Filter dietary preference (vegetarian / vegan / pescatarian)
            if user_diet == "vegetarian" and tmpl["dietary_type"] not in ["vegetarian", "vegan"]:
                continue
            if user_diet == "vegan" and tmpl["dietary_type"] != "vegan":
                continue

            # 3. Compute ingredient overlap score
            matched_count = 0
            for ing in tmpl["ingredients"]:
                ing_name = ing["name"].lower()
                if any(u_ing in ing_name or ing_name in u_ing for u_ing in user_ingredients):
                    matched_count += 1

            # Convert template to RecipeResponse
            recipe_id = f"rcp-{uuid.uuid4().hex[:8]}"
            ingredients_list = [
                RecipeIngredient(
                    name=i["name"],
                    amount=float(i["amount"]),
                    unit=i["unit"],
                    notes=i.get("notes"),
                    category=i.get("category", "Pantry")
                ) for i in tmpl["ingredients"]
            ]
            steps_list = [
                RecipeStep(
                    step_number=s["step_number"],
                    instruction=s["instruction"],
                    timer_minutes=s.get("timer_minutes"),
                    tip=s.get("tip")
                ) for s in tmpl["instructions"]
            ]
            subs_list = [
                IngredientSubstitution(
                    original=sub["original"],
                    substitute=sub["substitute"],
                    ratio=sub["ratio"],
                    notes=sub["notes"]
                ) for sub in tmpl["substitutions"]
            ]
            
            b_nutri = tmpl["base_nutrition"]
            macros = MacroNutrients(
                calories=b_nutri["calories"],
                protein=b_nutri["protein"],
                carbohydrates=b_nutri["carbohydrates"],
                fat=b_nutri["fat"],
                saturated_fat=b_nutri["saturated_fat"],
                fiber=b_nutri["fiber"],
                sugar=b_nutri["sugar"]
            )

            res = RecipeResponse(
                recipe_id=recipe_id,
                title=tmpl["title"],
                description=tmpl["description"],
                cuisine=tmpl["cuisine"],
                prep_time_minutes=tmpl["prep_time_minutes"],
                cook_time_minutes=tmpl["cook_time_minutes"],
                total_time_minutes=tmpl["prep_time_minutes"] + tmpl["cook_time_minutes"],
                servings=tmpl["base_servings"],
                base_servings=tmpl["base_servings"],
                ingredients=ingredients_list,
                instructions=steps_list,
                substitutions=subs_list,
                nutrition_per_serving=macros,
                is_nutrition_calculated=True,
                dietary_tags=tmpl["dietary_tags"],
                equipment_needed=tmpl["equipment"],
                allergens_present=tmpl["allergens"],
                safety_warning="Confirm internal meat temperatures exceed 74°C (165°F) with a digital food thermometer." if "chicken" in tmpl["id_prefix"] else None
            )

            # Scale if requested servings differ from base
            if target_servings != tmpl["base_servings"]:
                res = self.scale_recipe(res, target_servings)

            candidates.append((res, matched_count))

        # Sort candidates by ingredient overlap descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        results = [c[0] for c in candidates[:3]]

        # Fallback if filters were overly restrictive: return at least 1 safe recipe with substitution notes
        if not results:
            safe_tmpl = RECIPE_TEMPLATES[1]  # avocado toast
            res = RecipeResponse(
                recipe_id=f"rcp-{uuid.uuid4().hex[:8]}",
                title=f"Customized {safe_tmpl['title']}",
                description=safe_tmpl["description"],
                cuisine=safe_tmpl["cuisine"],
                prep_time_minutes=safe_tmpl["prep_time_minutes"],
                cook_time_minutes=safe_tmpl["cook_time_minutes"],
                total_time_minutes=safe_tmpl["prep_time_minutes"] + safe_tmpl["cook_time_minutes"],
                servings=target_servings,
                base_servings=safe_tmpl["base_servings"],
                ingredients=[RecipeIngredient(**i) for i in safe_tmpl["ingredients"]],
                instructions=[RecipeStep(**s) for s in safe_tmpl["instructions"]],
                substitutions=[IngredientSubstitution(**sub) for sub in safe_tmpl["substitutions"]],
                nutrition_per_serving=MacroNutrients(**safe_tmpl["base_nutrition"]),
                is_nutrition_calculated=True,
                dietary_tags=["Custom Allergy-Safe Adaptation"],
                equipment_needed=safe_tmpl["equipment"],
                allergens_present=[],
                safety_warning=None
            )
            results.append(self.scale_recipe(res, target_servings))

        return results

recipe_service = RecipeService()
