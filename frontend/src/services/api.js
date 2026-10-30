// Frontend API communication service (Parts 1, 2, & 3)
const API_BASE = "";

// ---------------------------------------------------------------------------
// Part 1: Food Recognition & Nutrition
// ---------------------------------------------------------------------------
export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function configureApiKey(apiKey) {
  const res = await fetch(`${API_BASE}/api/config/api-key`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: apiKey }),
  });
  if (!res.ok) throw new Error("Failed to configure API key");
  return res.json();
}

export async function fetchAiStatus() {
  const res = await fetch(`${API_BASE}/api/config/ai-status`);
  if (!res.ok) throw new Error("Failed to fetch AI status");
  return res.json();
}

export async function fetchSamples() {
  const res = await fetch(`${API_BASE}/api/food/samples`);
  if (!res.ok) throw new Error("Failed to load sample dishes");
  return res.json();
}

export async function recognizeFoodImage(file) {
  const formData = new FormData();
  formData.append("image", file);
  const res = await fetch(`${API_BASE}/api/food/recognize`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Recognition request failed" }));
    throw new Error(err.detail || "Error recognizing food image");
  }
  return res.json();
}

export async function analyzeNutrition(foodIdOrName, servingSize, unit = "grams") {
  const res = await fetch(`${API_BASE}/api/nutrition/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      food_id_or_name: foodIdOrName,
      serving_size: parseFloat(servingSize),
      unit: unit,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Nutrition calculation failed" }));
    throw new Error(err.detail || "Error calculating nutrition metrics");
  }
  return res.json();
}

export async function fetchFoodCatalog() {
  const res = await fetch(`${API_BASE}/api/nutrition/foods`);
  if (!res.ok) throw new Error("Failed to fetch food catalog");
  return res.json();
}

// ---------------------------------------------------------------------------
// Part 2: Food Freshness Intelligence
// ---------------------------------------------------------------------------
export async function fetchFreshnessSamples() {
  const res = await fetch(`${API_BASE}/api/freshness/samples`);
  if (!res.ok) throw new Error("Failed to load freshness samples");
  return res.json();
}

export async function analyzeFoodFreshness(file) {
  const formData = new FormData();
  formData.append("image", file);
  const res = await fetch(`${API_BASE}/api/freshness/analyze`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Freshness analysis failed" }));
    throw new Error(err.detail || "Error analyzing produce freshness");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Part 2: Restaurant Kitchen Hygiene Monitoring
// ---------------------------------------------------------------------------
export async function fetchHygieneSamples() {
  const res = await fetch(`${API_BASE}/api/hygiene/samples`);
  if (!res.ok) throw new Error("Failed to load hygiene samples");
  return res.json();
}

export async function analyzeKitchenImage(file) {
  const formData = new FormData();
  formData.append("image", file);
  const res = await fetch(`${API_BASE}/api/hygiene/analyze-image`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Hygiene image analysis failed" }));
    throw new Error(err.detail || "Error analyzing kitchen photograph");
  }
  return res.json();
}

export async function analyzeKitchenVideo(file) {
  const formData = new FormData();
  formData.append("video", file);
  const res = await fetch(`${API_BASE}/api/hygiene/analyze-video`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Hygiene video analysis failed" }));
    throw new Error(err.detail || "Error processing kitchen video stream");
  }
  return res.json();
}

export async function updateChecklistItemReview(itemId, status, reviewerName, auditId = "") {
  const res = await fetch(`${API_BASE}/api/hygiene/reviews/${itemId}?audit_id=${auditId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      reviewer_status: status,
      reviewer_notes: `Marked as ${status} by ${reviewerName}`,
      reviewer_name: reviewerName,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Reviewer update failed" }));
    throw new Error(err.detail || "Error updating checklist item");
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Part 3: Smart Cooking Assistant
// ---------------------------------------------------------------------------
export async function generateRecipes(payload) {
  const res = await fetch(`${API_BASE}/api/recipes/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Recipe generation failed" }));
    throw new Error(err.detail || "Error generating recipes");
  }
  return res.json();
}

export async function sendCookingChat(payload) {
  const res = await fetch(`${API_BASE}/api/cooking/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Chat request failed" }));
    throw new Error(err.detail || "Error processing cooking chat");
  }
  return res.json();
}

export async function fetchCookingSamplePrompts() {
  const res = await fetch(`${API_BASE}/api/cooking/sample-prompts`);
  if (!res.ok) throw new Error("Failed to fetch sample prompts");
  return res.json();
}

export async function fetchSavedRecipes() {
  const res = await fetch(`${API_BASE}/api/recipes`);
  if (!res.ok) throw new Error("Failed to fetch saved recipes");
  return res.json();
}

export async function saveFavoriteRecipe(recipe, notes = "") {
  const res = await fetch(`${API_BASE}/api/recipes/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recipe, user_notes: notes }),
  });
  if (!res.ok) throw new Error("Failed to save favorite recipe");
  return res.json();
}

export async function deleteSavedRecipe(recipeId) {
  const res = await fetch(`${API_BASE}/api/recipes/${recipeId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete recipe");
  return res.json();
}

// ---------------------------------------------------------------------------
// Part 3: Personalized Meal Planner
// ---------------------------------------------------------------------------
export async function generateMealPlan(payload) {
  const res = await fetch(`${API_BASE}/api/meal-plans/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Meal plan generation failed" }));
    throw new Error(err.detail || "Error generating personalized meal plan");
  }
  return res.json();
}

export async function fetchSavedMealPlans() {
  const res = await fetch(`${API_BASE}/api/meal-plans`);
  if (!res.ok) throw new Error("Failed to fetch meal plans");
  return res.json();
}

export async function saveMealPlan(plan) {
  const res = await fetch(`${API_BASE}/api/meal-plans/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(plan),
  });
  if (!res.ok) throw new Error("Failed to save meal plan");
  return res.json();
}
