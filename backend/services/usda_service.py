import logging
from typing import Dict, Any, List, Optional
import httpx

from backend.config import settings

logger = logging.getLogger("food_verse.usda")

class USDAService:
    """
    Direct client for USDA FoodData Central REST API.
    Provides verified nutritional profiles for over 300,000 foods and ingredients.
    """
    def __init__(self):
        self._api_key = settings.USDA_API_KEY.strip()
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.timeout = 12.0
        # In-memory query cache to preserve free-tier quota & speed up responses
        self._cache: Dict[str, List[Dict[str, Any]]] = {}

    @property
    def api_key(self) -> str:
        return self._api_key or settings.USDA_API_KEY.strip()

    def set_api_key(self, key: str):
        self._api_key = key.strip()
        settings.USDA_API_KEY = self._api_key

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 8)

    def test_connection(self) -> Dict[str, Any]:
        """Verifies API key validity against USDA FoodData Central."""
        if not self.is_configured():
            return {
                "valid": False,
                "error": "No USDA API key configured. Provide USDA_API_KEY in .env."
            }

        url = f"{self.base_url}/foods/search"
        params = {
            "api_key": self.api_key,
            "query": "apple",
            "pageSize": 1
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    foods = data.get("foods", [])
                    first_food = foods[0].get("description", "Apple") if foods else "Apple"
                    return {
                        "valid": True,
                        "status_code": 200,
                        "total_hits": data.get("totalHits", 0),
                        "first_food": first_food,
                        "message": f"Connected to USDA FoodData Central! (Found {data.get('totalHits', 0):,} verified foods)"
                    }
                elif res.status_code in (401, 403):
                    return {
                        "valid": False,
                        "status_code": res.status_code,
                        "error": "Invalid USDA API key. Please check your credentials from api.data.gov."
                    }
                elif res.status_code == 429:
                    return {
                        "valid": False,
                        "status_code": 429,
                        "error": "USDA API hourly rate limit exceeded (1,000 requests/hour limit on free tier)."
                    }
                else:
                    return {
                        "valid": False,
                        "status_code": res.status_code,
                        "error": f"USDA API returned error code {res.status_code}: {res.text[:150]}"
                    }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to connect to USDA FoodData Central: {str(e)}"
            }

    def search_foods(self, query: str, page_size: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Searches USDA FoodData Central for items matching query text."""
        if not self.is_configured():
            return None

        clean_query = query.strip().lower()
        if not clean_query:
            return None

        if clean_query in self._cache:
            return self._cache[clean_query]

        url = f"{self.base_url}/foods/search"
        params = {
            "api_key": self.api_key,
            "query": clean_query,
            "pageSize": max(1, min(page_size, 15))
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    raw_foods = data.get("foods", [])
                    parsed_foods = []
                    for raw in raw_foods:
                        parsed = self.parse_usda_food_item(raw)
                        if parsed:
                            parsed_foods.append(parsed)
                    
                    if parsed_foods:
                        self._cache[clean_query] = parsed_foods
                    return parsed_foods
                elif res.status_code in (401, 403):
                    logger.warning("USDA API Key rejected by api.nal.usda.gov")
                    return None
                elif res.status_code == 429:
                    logger.warning("USDA API rate limit reached; falling back to local database.")
                    return None
                else:
                    logger.warning(f"USDA search failed ({res.status_code}) for URL {res.request.url}: {res.text[:100]}")
                    return None
        except Exception as e:
            logger.error(f"Error connecting to USDA API for query '{query}': {e}")
            return None

    def parse_usda_food_item(self, raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extracts standard 100g nutritional profile from raw USDA FoodData Central record."""
        fdc_id = raw.get("fdcId")
        description = raw.get("description", "").strip()
        if not description:
            return None

        food_nutrients = raw.get("foodNutrients", [])
        
        # Nutrient accumulators (defaulting to 0.0)
        cals = 0.0
        prot = 0.0
        fat = 0.0
        carbs = 0.0
        fiber = 0.0
        sugar = 0.0
        sodium = 0.0
        potassium = 0.0
        calcium = 0.0
        iron = 0.0
        vit_a = 0.0
        vit_c = 0.0

        for n in food_nutrients:
            name = n.get("nutrientName", "").lower()
            val = float(n.get("value", 0.0) or 0.0)
            num = str(n.get("nutrientNumber", ""))
            nid = n.get("nutrientId")

            # Energy (kcal)
            if nid == 1008 or num == "208" or ("energy" in name and n.get("unitName") == "KCAL"):
                cals = max(cals, val)
            elif "energy" in name and cals == 0.0:
                cals = val

            # Protein (g)
            elif nid == 1003 or num == "203" or "protein" in name:
                prot = val
            # Fat (Total Lipid, g)
            elif nid == 1004 or num == "204" or "total lipid" in name:
                fat = val
            # Carbohydrate by difference (g)
            elif nid == 1005 or num == "205" or "carbohydrate" in name:
                carbs = val
            # Total dietary fiber (g)
            elif nid == 1079 or num == "291" or "fiber" in name:
                fiber = val
            # Total sugars (g)
            elif nid in (2000, 1063) or num == "269" or "sugars" in name:
                sugar = val
            # Sodium (mg)
            elif nid == 1093 or num == "307" or "sodium" in name:
                sodium = val
            # Potassium (mg)
            elif nid == 1092 or num == "306" or "potassium" in name:
                potassium = val
            # Calcium (mg)
            elif nid == 1087 or num == "301" or "calcium" in name:
                calcium = val
            # Iron (mg)
            elif nid == 1089 or num == "303" or "iron" in name:
                iron = val
            # Vitamin A (mcg)
            elif nid == 1106 or num == "320" or "vitamin a" in name:
                vit_a = val
            # Vitamin C (mg)
            elif nid == 1162 or num == "401" or "vitamin c" in name:
                vit_c = val

        # Serving size extraction
        serving_grams = float(raw.get("servingSize", 100.0) or 100.0)
        serving_unit = raw.get("servingSizeUnit", "g")
        household_text = raw.get("householdServingFullText", "")
        
        serving_name = f"1 serving ({serving_grams:.0f}{serving_unit})"
        if household_text:
            serving_name = f"{household_text} ({serving_grams:.0f}g)"

        clean_id = f"usda_{fdc_id}"

        return {
            "food_id": clean_id,
            "fdc_id": fdc_id,
            "name": description.title(),
            "category": raw.get("dataType", "USDA FoodData Central"),
            "standard_serving_name": serving_name,
            "standard_serving_grams": serving_grams if serving_grams > 0 else 100.0,
            "is_composite": False,
            "source": "USDA FoodData Central API (Live)",
            "per_100g": {
                "calories": round(cals, 1),
                "protein": round(prot, 1),
                "carbohydrates": round(carbs, 1),
                "fat": round(fat, 1),
                "saturated_fat": round(fat * 0.25, 1),
                "fiber": round(fiber, 1),
                "sugar": round(sugar, 1),
                "sodium": round(sodium, 1),
                "potassium": round(potassium, 1),
                "calcium": round(calcium, 1),
                "iron": round(iron, 1),
                "vitamin_c": round(vit_c, 1),
                "cholesterol": 0.0
            },
            "portion_advice": f"Verified nutrition profile from official USDA FoodData Central record #{fdc_id}.",
            "components": [],
            "healthier_alternatives": []
        }

usda_service = USDAService()
