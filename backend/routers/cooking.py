from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from backend.models.schemas import (
    RecipeGenerateRequest,
    RecipeResponse,
    CookingChatRequest,
    CookingChatResponse,
    RecipeSaveRequest
)
from backend.services.recipe_service import recipe_service
from backend.services.cooking_chat_service import cooking_chat_service
from backend.auth import get_optional_user
from backend.database import get_db
from backend.models.db_models import SavedRecipe, ChatHistoryRecord, User

router = APIRouter(prefix="/api", tags=["Smart Cooking Assistant"])

@router.post("/recipes/generate", response_model=List[RecipeResponse])
def generate_recipes(payload: RecipeGenerateRequest):
    """
    Generates suitable recipes based on supplied ingredients,
    dietary preferences, and equipment, respecting allergy exclusions.
    """
    if not payload.ingredients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one ingredient must be provided to generate recipes."
        )
    try:
        recipes = recipe_service.generate_recipes(payload)
        return recipes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recipe generation error: {str(e)}"
        )

@router.post("/cooking/chat", response_model=CookingChatResponse)
def cooking_chat(
    payload: CookingChatRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Interactive culinary chat assistant: clarifies ingredients, suggests
    substitutions, handles follow-up questions, and scales recipes.
    Saves message history to DB if user is authenticated.
    """
    try:
        response = cooking_chat_service.process_chat(payload)

        # If user is logged in, persist the last user message and assistant reply to DB
        if current_user and payload.messages:
            try:
                session_id = getattr(payload, "session_id", "default-chat-session")
                last_user_msg = payload.messages[-1]
                rec_user = ChatHistoryRecord(
                    user_id=current_user.id,
                    session_id=session_id,
                    role="user",
                    content=last_user_msg.content,
                )
                rec_ai = ChatHistoryRecord(
                    user_id=current_user.id,
                    session_id=session_id,
                    role="assistant",
                    content=response.reply,
                )
                db.add_all([rec_user, rec_ai])
                db.commit()
            except Exception:
                db.rollback()

        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cooking assistant chat error: {str(e)}"
        )

@router.get("/cooking/sample-prompts")
def get_cooking_sample_prompts():
    """Provides curated sample prompts for 1-click testing."""
    return [
        {
            "id": "p-1",
            "title": "Quick Pan-Seared Salmon",
            "prompt": "I have salmon fillets, quinoa, and broccoli. What can I cook in under 25 minutes?",
            "ingredients": ["Salmon", "Quinoa", "Broccoli", "Olive Oil"]
        },
        {
            "id": "p-2",
            "title": "High-Protein Breakfast Toast",
            "prompt": "I have ripe avocado, sourdough bread, and eggs. Show me a healthy breakfast.",
            "ingredients": ["Avocado", "Sourdough", "Eggs"]
        },
        {
            "id": "p-3",
            "title": "Vegan Rainbow Stir-Fry",
            "prompt": "I have extra firm tofu, bell peppers, broccoli, and soy sauce. Make it gluten-free.",
            "ingredients": ["Tofu", "Bell Pepper", "Broccoli", "Soy Sauce"]
        },
        {
            "id": "p-4",
            "title": "Ingredient Substitution Query",
            "prompt": "What can I substitute for buttermilk in pancakes?",
            "ingredients": []
        }
    ]

@router.get("/recipes", response_model=List[Dict[str, Any]])
def list_saved_recipes(
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Returns user's saved favorite recipes from persistent storage.
    If authenticated, returns DB records; otherwise returns bundled/demo JSON file.
    """
    if current_user:
        db_recipes = (
            db.query(SavedRecipe)
            .filter(SavedRecipe.user_id == current_user.id)
            .order_by(SavedRecipe.created_at.desc())
            .all()
        )
        if db_recipes:
            return [
                {
                    "recipe_id": r.recipe_id,
                    "title": r.title,
                    "cuisine": r.cuisine,
                    "prep_time_minutes": r.prep_time_minutes,
                    "cook_time_minutes": r.cook_time_minutes,
                    "servings": r.servings,
                    "user_notes": r.user_notes,
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                    "recipe_data": r.recipe_data,
                }
                for r in db_recipes
            ]
    return recipe_service.get_saved_recipes()

@router.post("/recipes/save")
def save_favorite_recipe(
    payload: RecipeSaveRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Saves a recipe to user's favorite recipe library (DB when logged in, JSON file fallback)."""
    try:
        if current_user:
            rec = SavedRecipe(
                user_id=current_user.id,
                recipe_id=payload.recipe.recipe_id,
                title=payload.recipe.title,
                cuisine=payload.recipe.cuisine,
                prep_time_minutes=payload.recipe.prep_time_minutes,
                cook_time_minutes=payload.recipe.cook_time_minutes,
                servings=payload.recipe.servings,
                user_notes=payload.user_notes or "",
                recipe_data=payload.recipe.model_dump(),
            )
            db.add(rec)
            db.commit()
            return {"status": "saved", "recipe_id": payload.recipe.recipe_id}

        saved = recipe_service.save_recipe(payload)
        return {"status": "saved", "recipe_id": saved["recipe_id"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save recipe: {str(e)}"
        )

@router.delete("/recipes/{recipe_id}")
def delete_saved_recipe(
    recipe_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Deletes a recipe from user's favorite list."""
    if current_user:
        rec = (
            db.query(SavedRecipe)
            .filter(SavedRecipe.user_id == current_user.id, SavedRecipe.recipe_id == recipe_id)
            .first()
        )
        if rec:
            db.delete(rec)
            db.commit()
            return {"status": "deleted", "recipe_id": recipe_id}

    success = recipe_service.delete_saved_recipe(recipe_id)
    if not success:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return {"status": "deleted", "recipe_id": recipe_id}
