from typing import Dict, Any, List
from backend.models.schemas import NutritionAnalyzeResponse

class AIInsightService:
    @staticmethod
    def generate_contextual_insights(nutri: NutritionAnalyzeResponse) -> Dict[str, Any]:
        """Generate smart nutritional takeaways based on computed macronutrients and portion."""
        tags = []
        cals = nutri.macros.calories
        prot = nutri.macros.protein
        carbs = nutri.macros.carbohydrates
        fat = nutri.macros.fat
        fiber = nutri.macros.fiber
        sodium = nutri.micros.sodium

        # Macronutrient density analysis
        if prot >= 20:
            tags.append("High Protein Muscle Support")
        if fiber >= 5:
            tags.append("High Prebiotic Fiber")
        if carbs <= 15 and fat >= 10:
            tags.append("Keto / Low-Carb Compatible")
        if sodium > 600:
            tags.append("High Sodium Content")
        elif sodium < 140:
            tags.append("Low Sodium Heart Friendly")

        # Dynamic advice based on serving size
        portion_tip = nutri.portion_advice
        if nutri.serving_size_grams > 350 and cals > 600:
            portion_tip += " [Note: This portion is quite hearty. Consider reserving half for a second meal or increasing light aerobic activity.]"
        elif nutri.serving_size_grams < 100 and cals < 150:
            portion_tip += " [Note: This acts primarily as a light snack or side. Pair with a lean protein source to achieve full meal satiety.]"

        # Glycemic & satiety estimate
        if fiber > 4 and prot > 12:
            satiety_rating = "Very High (4-5 hours satiety)"
            glycemic_impact = "Low & Sustained Release"
        elif carbs > 40 and fiber < 2:
            satiety_rating = "Short-lived (Rapid digestive transit)"
            glycemic_impact = "Moderate-to-High spike potential"
        else:
            satiety_rating = "Moderate (2-3 hours)"
            glycemic_impact = "Balanced"

        return {
            "satiety_rating": satiety_rating,
            "glycemic_impact": glycemic_impact,
            "smart_tags": tags,
            "dynamic_portion_tip": portion_tip
        }

ai_insight_service = AIInsightService()
