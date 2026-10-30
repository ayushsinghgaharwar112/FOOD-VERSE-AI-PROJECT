import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from backend.config import DATA_DIR
from backend.models.schemas import (
    NutritionAnalyzeRequest,
    NutritionAnalyzeResponse,
    MacroNutrients,
    MicroNutrients,
    DailyValuePercentage,
    CalorieDistribution,
    HealthierAlternativeItem,
    ServingComponent
)

class NutritionService:
    def __init__(self):
        self.db_path = DATA_DIR / "nutrition_db.json"
        self._database: Dict[str, Any] = {}
        self.load_database()

    def load_database(self):
        if self.db_path.exists():
            with open(self.db_path, "r", encoding="utf-8") as f:
                self._database = json.load(f)
        else:
            self._database = {}

    @property
    def database(self) -> Dict[str, Any]:
        return self._database

    def find_food(self, food_id_or_name: str) -> Optional[Dict[str, Any]]:
        query = food_id_or_name.strip().lower()
        # Direct key match
        if query in self._database:
            return self._database[query]
        
        # Replace spaces with underscores
        id_query = query.replace(" ", "_")
        if id_query in self._database:
            return self._database[id_query]

        # Alias or partial name match
        for key, item in self._database.items():
            if item.get("name", "").lower() == query:
                return item
            aliases = [a.lower() for a in item.get("aliases", [])]
            if query in aliases:
                return item
            if query in item.get("name", "").lower():
                return item

        # Substring search in key
        for key, item in self._database.items():
            if query in key:
                return item

        # Live USDA FoodData Central Search if configured
        try:
            from backend.services.usda_service import usda_service
            if usda_service.is_configured():
                usda_results = usda_service.search_foods(query, page_size=1)
                if usda_results:
                    best_match = usda_results[0]
                    self.register_food(query, best_match)
                    self.register_food(best_match["food_id"], best_match)
                    return best_match
        except Exception:
            pass

        return None

    def register_food(self, food_id: str, data: Dict[str, Any]):
        """Dynamically add or update food items in the database (e.g. from Gemini AI recognition)."""
        clean_id = food_id.strip().lower().replace(" ", "_")
        self._database[clean_id] = data
        return clean_id

    def calculate_nutrition(self, req: NutritionAnalyzeRequest) -> NutritionAnalyzeResponse:
        food_item = self.find_food(req.food_id_or_name)
        if not food_item:
            # Fallback or raise error
            raise ValueError(f"Food item '{req.food_id_or_name}' not found in verified nutrition database.")

        std_grams = float(food_item.get("standard_serving_grams", 150.0))
        std_name = food_item.get("standard_serving_name", "1 serving")

        # Determine target grams
        if req.unit.lower() in ["servings", "serving"]:
            target_grams = req.serving_size * std_grams
            serving_display = f"{req.serving_size} serving ({round(target_grams, 1)}g)"
        else:
            target_grams = float(req.serving_size)
            servings_equiv = round(target_grams / std_grams, 2)
            serving_display = f"{target_grams}g (~{servings_equiv} standard servings)"

        multiplier = target_grams / 100.0
        p100 = food_item["per_100g"]

        # Calculate macros securely on server
        cals = round(p100["calories"] * multiplier, 1)
        prot = round(p100["protein"] * multiplier, 1)
        carbs = round(p100["carbohydrates"] * multiplier, 1)
        fat = round(p100["fat"] * multiplier, 1)
        sat_fat = round(p100["saturated_fat"] * multiplier, 1)
        fiber = round(p100["fiber"] * multiplier, 1)
        sugar = round(p100["sugar"] * multiplier, 1)

        macros = MacroNutrients(
            calories=cals,
            protein=prot,
            carbohydrates=carbs,
            fat=fat,
            saturated_fat=sat_fat,
            fiber=fiber,
            sugar=sugar
        )

        # Calculate micros
        sodium = round(p100["sodium"] * multiplier, 1)
        potassium = round(p100["potassium"] * multiplier, 1)
        calcium = round(p100["calcium"] * multiplier, 1)
        iron = round(p100["iron"] * multiplier, 1)
        vit_c = round(p100["vitamin_c"] * multiplier, 1)
        chol = round(p100["cholesterol"] * multiplier, 1)

        micros = MicroNutrients(
            sodium=sodium,
            potassium=potassium,
            calcium=calcium,
            iron=iron,
            vitamin_c=vit_c,
            cholesterol=chol
        )

        # Standard Daily Value references (2,000 kcal diet)
        dv_pct = DailyValuePercentage(
            calories=round((cals / 2000.0) * 100, 1),
            protein=round((prot / 50.0) * 100, 1),
            carbohydrates=round((carbs / 275.0) * 100, 1),
            fat=round((fat / 78.0) * 100, 1),
            saturated_fat=round((sat_fat / 20.0) * 100, 1),
            fiber=round((fiber / 28.0) * 100, 1),
            sodium=round((sodium / 2300.0) * 100, 1),
            calcium=round((calcium / 1300.0) * 100, 1),
            iron=round((iron / 18.0) * 100, 1),
            vitamin_c=round((vit_c / 90.0) * 100, 1)
        )

        # 4-4-9 Atwater Factor Calorie Distribution
        p_kcal = round(prot * 4.0, 1)
        c_kcal = round(carbs * 4.0, 1)
        f_kcal = round(fat * 9.0, 1)
        total_macro_kcal = p_kcal + c_kcal + f_kcal
        if total_macro_kcal > 0:
            p_pct = round((p_kcal / total_macro_kcal) * 100, 1)
            c_pct = round((c_kcal / total_macro_kcal) * 100, 1)
            f_pct = round((f_kcal / total_macro_kcal) * 100, 1)
        else:
            p_pct, c_pct, f_pct = 0.0, 0.0, 0.0

        calorie_dist = CalorieDistribution(
            protein_kcal=p_kcal,
            carbs_kcal=c_kcal,
            fat_kcal=f_kcal,
            protein_pct=p_pct,
            carbs_pct=c_pct,
            fat_pct=f_pct
        )

        # Healthier alternatives
        raw_alts = food_item.get("healthier_alternatives", [])
        healthier_alts = [
            HealthierAlternativeItem(
                name=a["name"],
                reason=a["reason"],
                calorie_difference=a.get("calorie_difference", 0)
            ) for a in raw_alts
        ]

        # Serving components scaled to target_grams
        raw_components = food_item.get("components", [])
        components: List[ServingComponent] = []
        if raw_components:
            for c in raw_components:
                pct = float(c.get("percentage", 0))
                grams = round((pct / 100.0) * target_grams, 1)
                components.append(ServingComponent(
                    name=c["name"],
                    grams=grams,
                    percentage=pct
                ))

        return NutritionAnalyzeResponse(
            food_id=food_item["id"],
            food_name=food_item["name"],
            category=food_item.get("category", "Food"),
            serving_size_grams=round(target_grams, 1),
            serving_display=serving_display,
            macros=macros,
            micros=micros,
            daily_value_percentages=dv_pct,
            calorie_distribution=calorie_dist,
            health_score=food_item.get("health_score", 75),
            nutri_grade=food_item.get("nutri_grade", "B"),
            health_notes=food_item.get("health_notes", "Balanced food choice."),
            portion_advice=food_item.get("portion_advice", f"Recommended portion is around {std_grams}g."),
            healthier_alternatives=healthier_alts,
            dietary_tags=food_item.get("dietary_tags", []),
            components=components,
            is_demo_data=True
        )

nutrition_service = NutritionService()
