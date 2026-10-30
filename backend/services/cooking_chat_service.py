import time
from typing import List, Dict, Any, Optional
from backend.config import settings
from backend.services.gemini_service import gemini_service
from backend.models.schemas import (
    CookingChatRequest,
    CookingChatResponse,
    RecipeResponse,
    RecipeGenerateRequest
)
from backend.services.recipe_service import recipe_service

# Common ingredient substitutions dictionary
COMMON_SUBSTITUTIONS = {
    "egg": "1 tbsp ground flaxseed mixed with 3 tbsp water (for baking), or 1/4 cup unsweetened applesauce, or 50g silken tofu.",
    "buttermilk": "1 cup milk (or soy milk) + 1 tbsp fresh lemon juice or white vinegar; let sit 5 minutes until curdled.",
    "heavy cream": "3/4 cup whole milk + 1/3 cup melted unsalted butter, or full-fat canned coconut milk.",
    "sour cream": "Equal quantity of plain Greek yogurt (adds +8g protein and cuts saturated fat).",
    "olive oil": "Avocado oil (equal smoke point), grapeseed oil, or melted coconut oil.",
    "soy sauce": "Tamari (gluten-free) or coconut aminos (low sodium and soy-free).",
    "breadcrumbs": "Rolled oats pulsed in a blender, crushed cornflakes, or almond flour (gluten-free).",
    "parmesan": "Nutritional yeast flakes for a savory umami vegan cheese alternative.",
    "garlic": "1/8 tsp garlic powder per clove, or 1 tsp minced shallot.",
    "all-purpose flour": "1:1 gluten-free baking blend (with xanthan gum) or oat flour."
}

class CookingChatService:
    def __init__(self):
        self.model_name = settings.COOKING_LLM_MODEL
        self.has_api_key = bool(settings.GEMINI_API_KEY)

    def _extract_ingredients_from_text(self, text: str) -> List[str]:
        common_words = [
            "chicken", "salmon", "tofu", "egg", "eggs", "rice", "quinoa", "pasta",
            "avocado", "broccoli", "spinach", "tomato", "tomatoes", "garlic", "onion",
            "bell pepper", "mushrooms", "cheese", "yogurt", "oats", "berries", "lemon",
            "olive oil", "soy sauce", "ginger", "potatoes", "beef", "shrimp"
        ]
        found = []
        lowered = text.lower()
        for word in common_words:
            if word in lowered:
                found.append(word.capitalize())
        return found

    def process_chat(self, req: CookingChatRequest) -> CookingChatResponse:
        if not req.messages:
            return CookingChatResponse(
                reply="Hello! I am your Food Verse AI Chef. Tell me what ingredients you have in your kitchen or what you are craving, and I will craft the perfect recipe!",
                suggested_recipes=[],
                recommended_followups=[
                    "What can I cook with eggs, spinach, and sourdough?",
                    "Suggest a high-protein dinner under 25 minutes",
                    "How do I substitute buttermilk in a recipe?"
                ],
                extracted_ingredients=[],
                is_demo_mode=not gemini_service.is_configured()
            )

        last_user_msg = req.messages[-1].content.strip().lower()
        extracted = self._extract_ingredients_from_text(last_user_msg)
        if req.available_ingredients:
            for ing in req.available_ingredients:
                if ing not in extracted:
                    extracted.append(ing)

        # 1. Live Google Gemini LLM Conversational Assistant
        if gemini_service.is_configured():
            try:
                dict_messages = [{"role": m.role, "content": m.content} for m in req.messages]
                gemini_res = gemini_service.chat_cooking(
                    messages=dict_messages,
                    available_ingredients=req.available_ingredients or [],
                    dietary_preference=req.dietary_preference or "any",
                    allergies=req.allergies or []
                )
                if gemini_res and gemini_res.get("reply"):
                    return CookingChatResponse(
                        reply=gemini_res["reply"],
                        suggested_recipes=[],
                        recommended_followups=gemini_res.get("suggested_followups", [
                            "How do I modify this recipe?",
                            "Can you give exact cook times?",
                            "What wine or beverage pairs with this?"
                        ]),
                        extracted_ingredients=gemini_res.get("extracted_ingredients", extracted),
                        is_demo_mode=False
                    )
            except Exception as e:
                # Fall back gracefully to rule-based assistant
                pass

        suggested_recipes: List[RecipeResponse] = []
        followups: List[str] = []

        # 1. Ingredient Substitution Questions
        sub_match = None
        for key, sub_text in COMMON_SUBSTITUTIONS.items():
            if f"substitute for {key}" in last_user_msg or f"replace {key}" in last_user_msg or f"no {key}" in last_user_msg:
                sub_match = (key, sub_text)
                break

        if sub_match:
            key, sub_text = sub_match
            reply = f"For **{key.title()}**, you can use:\n\n👉 **{sub_text}**\n\nThis will preserve the moisture balance and structure of your dish without altering the core flavor profile."
            followups = [
                f"Does this substitution change cooking time for {key}?",
                "Can I make this dish dairy-free?",
                "Suggest a side dish that pairs with this"
            ]

        # 2. Cooking Technique / Equipment Adjustment Questions
        elif "air fryer" in last_user_msg or "air fry" in last_user_msg:
            reply = (
                "To adapt this recipe for an **Air Fryer**:\n\n"
                "1. **Preheat**: Set air fryer to **190°C (375°F)** for 3 minutes.\n"
                "2. **Spacing**: Arrange items in a single layer with at least 1cm gap between pieces for convective airflow.\n"
                "3. **Time Adjustment**: Reduce total cooking time by approximately **20-25%** compared to a conventional oven.\n"
                "4. **Shake/Flip**: Shake the basket or flip items at the halfway mark to achieve uniform crispness."
            )
            followups = [
                "How do I prevent food from drying out in an air fryer?",
                "Can I use parchment paper in an air fryer?",
                "What sauces pair well with this?"
            ]

        elif "spicy" in last_user_msg or "hot" in last_user_msg:
            reply = (
                "To enhance heat and depth of flavor:\n\n"
                "- **Fresh Heat**: Fold in finely diced Thai bird's eye chilies or seeded jalapeños during the final 2 minutes of sautéing.\n"
                "- **Smoky Warmth**: Add 1/2 tsp smoked paprika paired with chipotle powder.\n"
                "- **Finishing Kick**: Drizzle with chili crisp or sriracha mixed with fresh lime juice."
            )
            followups = [
                "How do I tone down excess spice if it gets too hot?",
                "Recommend a cooling yogurt sauce to pair with this",
                "What spices complement garlic and ginger?"
            ]

        # 3. New Recipe Request or Ingredients Provided
        elif extracted or "recipe" in last_user_msg or "cook" in last_user_msg or "dinner" in last_user_msg or "lunch" in last_user_msg:
            gen_req = RecipeGenerateRequest(
                ingredients=extracted if extracted else ["salmon", "broccoli", "olive oil"],
                preferences=last_user_msg,
                dietary_preference=req.dietary_preference,
                allergies=req.allergies,
                servings=2
            )
            suggested_recipes = recipe_service.generate_recipes(gen_req)
            top_rec = suggested_recipes[0]
            reply = (
                f"Based on your request, I crafted **{top_rec.title}**!\n\n"
                f"{top_rec.description}\n\n"
                f"⏱️ **Total Time:** {top_rec.total_time_minutes} mins • 🍽️ **Servings:** {top_rec.servings} • "
                f"🔥 **Calories:** {top_rec.nutrition_per_serving.calories} kcal/serving\n\n"
                f"Check the interactive recipe card below to scale servings or review step-by-step instructions!"
            )
            followups = [
                f"How do I scale {top_rec.title} for 4 people?",
                "Can I meal prep this ahead of time?",
                "What can I substitute if I run out of one ingredient?"
            ]

        # 4. Contextual Follow-Up regarding current recipe
        elif req.current_recipe:
            cr = req.current_recipe
            reply = (
                f"Regarding **{cr.title}**:\n\n"
                f"This recipe yields {cr.servings} servings and provides **{cr.nutrition_per_serving.protein}g protein** and **{cr.nutrition_per_serving.calories} kcal** per serving.\n\n"
                f"Tip for step 2: Keep heat strictly at medium to develop golden browning without burning. Feel free to ask about any specific ingredient substitutions or equipment adjustments!"
            )
            followups = [
                f"Can I freeze leftovers of {cr.title}?",
                "How long does this keep in the refrigerator?",
                "Show me wine and beverage pairings"
            ]

        # 5. General Cooking Inquiries
        else:
            reply = (
                "I'm here to help you cook delicious, nutrient-dense food with whatever ingredients you have on hand! "
                "You can tell me:\n"
                "- Ingredients in your fridge (e.g. *'I have eggs, mushrooms, and cheese'*)\n"
                "- Dietary goals (e.g. *'High protein vegan dinner under 500 kcal'*)\n"
                "- Or ask any cooking technique and substitution question."
            )
            followups = [
                "Suggest a Mediterranean salmon dinner",
                "Quick 10-minute breakfast recipe with avocado",
                "What are healthy gluten-free pasta alternatives?"
            ]

        return CookingChatResponse(
            reply=reply,
            suggested_recipes=suggested_recipes,
            recommended_followups=followups,
            extracted_ingredients=extracted,
            is_demo_mode=not self.has_api_key
        )

cooking_chat_service = CookingChatService()
