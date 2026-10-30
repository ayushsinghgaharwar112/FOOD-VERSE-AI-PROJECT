const { useState, useEffect, useRef } = React;

// ── Authenticated API Fetch Helper ──────────────────────────────────────────
const apiFetch = (url, options = {}) => {
  const token = localStorage.getItem("fv_token");
  const headers = { ...(options.headers || {}) };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return fetch(url, { ...options, headers });
};

function App() {
  // Navigation: 'overview', 'nutrition', 'freshness', 'hygiene', 'cooking', 'planner', 'history', 'profile', 'login', 'register'
  const [activeTab, setActiveTab] = useState("overview");

  // =========================================================================
  // USER AUTHENTICATION & PROFILE STATE
  // =========================================================================
  const [currentUser, setCurrentUser] = useState(null);
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [registerName, setRegisterName] = useState("");
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerDiet, setRegisterDiet] = useState("any");
  const [registerGoal, setRegisterGoal] = useState("balanced");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState(null);

  // Profile Edit State
  const [profileForm, setProfileForm] = useState({
    name: "",
    dietary_preference: "any",
    goal: "balanced",
    allergies: []
  });
  const [profileSaving, setProfileSaving] = useState(false);

  // Toast Notifications
  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = "success") => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3500);
  };

  // =========================================================================
  // OVERVIEW DASHBOARD & INSIGHTS STATE
  // =========================================================================
  const [dashboardInsights, setDashboardInsights] = useState(null);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);

  // =========================================================================
  // HISTORY STATE
  // =========================================================================
  const [historyCategory, setHistoryCategory] = useState("food");
  const [historyItems, setHistoryItems] = useState([]);
  const [historyTotal, setHistoryTotal] = useState(0);
  const [historyPage, setHistoryPage] = useState(1);
  const [historyTotalPages, setHistoryTotalPages] = useState(1);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // =========================================================================
  // PART 1: FOOD RECOGNITION & NUTRITION
  // =========================================================================
  const [part1Samples, setPart1Samples] = useState([]);
  const [part1ImageFile, setPart1ImageFile] = useState(null);
  const [part1ImagePreviewUrl, setPart1ImagePreviewUrl] = useState(null);
  const [part1ImageMetadata, setPart1ImageMetadata] = useState(null);
  const [isRecognizing, setIsRecognizing] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [selectedFoodId, setSelectedFoodId] = useState(null);
  const [servingUnit, setServingUnit] = useState("grams");
  const [servingSize, setServingSize] = useState(150);
  const [isAnalyzingNutrition, setIsAnalyzingNutrition] = useState(false);
  const [nutrition, setNutrition] = useState(null);
  const [part1Error, setPart1Error] = useState(null);
  const part1FileInputRef = useRef(null);

  // =========================================================================
  // PART 2: FRESHNESS INTELLIGENCE
  // =========================================================================
  const [freshnessSamples, setFreshnessSamples] = useState([]);
  const [freshnessImageFile, setFreshnessImageFile] = useState(null);
  const [freshnessImagePreviewUrl, setFreshnessImagePreviewUrl] = useState(null);
  const [isAnalyzingFreshness, setIsAnalyzingFreshness] = useState(false);
  const [freshnessResult, setFreshnessResult] = useState(null);
  const [freshnessError, setFreshnessError] = useState(null);
  const freshnessFileInputRef = useRef(null);

  // =========================================================================
  // PART 2: KITCHEN HYGIENE
  // =========================================================================
  const [hygieneSamples, setHygieneSamples] = useState([]);
  const [hygieneMediaFile, setHygieneMediaFile] = useState(null);
  const [hygieneMediaPreviewUrl, setHygieneMediaPreviewUrl] = useState(null);
  const [hygieneMediaType, setHygieneMediaType] = useState("image");
  const [isAnalyzingHygiene, setIsAnalyzingHygiene] = useState(false);
  const [hygieneAudit, setHygieneAudit] = useState(null);
  const [hygieneError, setHygieneError] = useState(null);
  const [reviewerName, setReviewerName] = useState("Sanitation Auditor");
  const hygieneFileInputRef = useRef(null);

  // =========================================================================
  // PART 3: SMART COOKING ASSISTANT
  // =========================================================================
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      content: "Hello! I am your Food Verse AI Chef 👨‍🍳. Enter the ingredients you have on hand, specify dietary goals or equipment, or ask any cooking technique question!",
      timestamp: "Just now"
    }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [activeRecipe, setActiveRecipe] = useState(null);
  const [recipeServings, setRecipeServings] = useState(2);
  const [availableIngredients, setAvailableIngredients] = useState(["Salmon", "Broccoli", "Quinoa", "Olive Oil"]);
  const [newIngredientInput, setNewIngredientInput] = useState("");
  const [savedRecipes, setSavedRecipes] = useState([]);
  const [cookingDietPreference, setCookingDietPreference] = useState("any");
  const [cookingAllergies, setCookingAllergies] = useState([]);
  const chatMessagesEndRef = useRef(null);

  // =========================================================================
  // PART 3: PERSONALIZED MEAL PLANNER
  // =========================================================================
  const [plannerProfile, setPlannerProfile] = useState({
    dietary_preference: "non-vegetarian",
    allergies: [],
    goal: "balanced",
    age_range: "18-35",
    activity_level: "moderate",
    budget: "moderate",
    available_ingredients: [],
    meals_per_day: 3,
    preferred_cuisines: ["Mediterranean", "Asian"]
  });
  const [plannerDuration, setPlannerDuration] = useState(7);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [currentMealPlan, setCurrentMealPlan] = useState(null);
  const [selectedPlanDay, setSelectedPlanDay] = useState(0);
  const [groceryChecklist, setGroceryChecklist] = useState([]);
  const [savedMealPlans, setSavedMealPlans] = useState([]);

  // -------------------------------------------------------------------------
  // Lifecycle & Authentication Boot
  // -------------------------------------------------------------------------
  const fetchCurrentUser = async () => {
    const token = localStorage.getItem("fv_token");
    if (!token) {
      setCurrentUser(null);
      return;
    }
    try {
      const res = await apiFetch("/api/auth/me");
      if (res.ok) {
        const u = await res.json();
        setCurrentUser(u);
        setProfileForm({
          name: u.name,
          dietary_preference: u.dietary_preference || "any",
          goal: u.goal || "balanced",
          allergies: u.allergies || []
        });
      } else {
        localStorage.removeItem("fv_token");
        setCurrentUser(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError(null);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: loginEmail.trim(), password: loginPassword })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Invalid email or password");
      
      localStorage.setItem("fv_token", data.access_token);
      setCurrentUser(data.user);
      setProfileForm({
        name: data.user.name,
        dietary_preference: data.user.dietary_preference || "any",
        goal: data.user.goal || "balanced",
        allergies: data.user.allergies || []
      });
      showToast(`Welcome back, ${data.user.name}!`, "success");
      setActiveTab("overview");
      fetchDashboardOverview();
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError(null);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: registerEmail.trim(),
          password: registerPassword,
          name: registerName.trim() || "Food Verse Gourmet"
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Registration failed");

      localStorage.setItem("fv_token", data.access_token);
      setCurrentUser(data.user);
      
      // Update with chosen initial diet/goal
      await apiFetch("/api/auth/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dietary_preference: registerDiet,
          goal: registerGoal
        })
      });

      setProfileForm({
        name: data.user.name,
        dietary_preference: registerDiet,
        goal: registerGoal,
        allergies: []
      });

      showToast("Account registered! Welcome to Food Verse AI.", "success");
      setActiveTab("overview");
      fetchDashboardOverview();
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("fv_token");
    setCurrentUser(null);
    showToast("Signed out. You are now exploring as a guest.", "info");
    setActiveTab("overview");
    fetchDashboardOverview();
  };

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setProfileSaving(true);
    try {
      const res = await apiFetch("/api/auth/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profileForm)
      });
      if (!res.ok) throw new Error("Failed to update profile");
      const updated = await res.json();
      setCurrentUser(updated);
      showToast("Profile and dietary preferences saved successfully!", "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setProfileSaving(false);
    }
  };

  // Toggle allergen chip in profile
  const toggleAllergen = (allergen) => {
    setProfileForm(prev => {
      const exists = prev.allergies.includes(allergen);
      const updated = exists ? prev.allergies.filter(a => a !== allergen) : [...prev.allergies, allergen];
      return { ...prev, allergies: updated };
    });
  };

  // -------------------------------------------------------------------------
  // Dashboard & History Fetchers
  // -------------------------------------------------------------------------
  const fetchDashboardOverview = async () => {
    setLoadingDashboard(true);
    try {
      const [insightsRes, statsRes] = await Promise.all([
        apiFetch("/api/insights/dashboard"),
        apiFetch("/api/history/dashboard")
      ]);
      if (insightsRes.ok) setDashboardInsights(await insightsRes.json());
      if (statsRes.ok) setDashboardStats(await statsRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingDashboard(false);
    }
  };

  const fetchHistory = async (category = historyCategory, page = 1) => {
    setLoadingHistory(true);
    try {
      const res = await apiFetch(`/api/history/${category}?page=${page}&page_size=8`);
      if (res.ok) {
        const data = await res.json();
        setHistoryItems(data.items || []);
        setHistoryTotal(data.total || 0);
        setHistoryPage(data.page || 1);
        setHistoryTotalPages(data.total_pages || 1);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleDeleteHistoryItem = async (cat, id) => {
    if (!confirm("Are you sure you want to delete this historical record?")) return;
    try {
      const res = await apiFetch(`/api/history/${cat}/${id}`, { method: "DELETE" });
      if (res.ok) {
        showToast("Record removed from your history.", "success");
        fetchHistory(cat, historyPage);
        fetchDashboardOverview();
      } else {
        showToast("Could not delete record.", "error");
      }
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  // -------------------------------------------------------------------------
  // Component Mount Setup
  // -------------------------------------------------------------------------
  useEffect(() => {
    fetch("/api/food/samples").then(res => res.json()).then(setPart1Samples).catch(console.error);
    fetch("/api/freshness/samples").then(res => res.json()).then(setFreshnessSamples).catch(console.error);
    fetch("/api/hygiene/samples").then(res => res.json()).then(setHygieneSamples).catch(console.error);
    apiFetch("/api/recipes").then(res => res.json()).then(setSavedRecipes).catch(console.error);
    fetchCurrentUser();
    fetchDashboardOverview();
  }, []);

  useEffect(() => {
    if (activeTab === "overview") {
      fetchDashboardOverview();
    } else if (activeTab === "history") {
      fetchHistory(historyCategory, 1);
    }
  }, [activeTab, historyCategory]);

  useEffect(() => {
    if (chatMessagesEndRef.current) {
      chatMessagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages]);

  // -------------------------------------------------------------------------
  // Part 1: Food Recognition & Nutrition Logic
  // -------------------------------------------------------------------------
  const processPart1File = async (file) => {
    setPart1Error(null);
    if (!file) return;
    setPart1ImageFile(file);
    setPart1ImagePreviewUrl(URL.createObjectURL(file));
    setPart1ImageMetadata({ filename: file.name, size: `${(file.size / 1024).toFixed(1)} KB` });
    setIsRecognizing(true);
    setRecognition(null);
    setNutrition(null);
    const fd = new FormData();
    fd.append("image", file);
    try {
      const res = await apiFetch("/api/food/recognize", { method: "POST", body: fd });
      if (!res.ok) throw new Error("Food recognition inference failed");
      const data = await res.json();
      setRecognition(data);
      setSelectedFoodId(data.food_id);
      const def = data.standard_serving_grams || 150;
      setServingSize(def);
      fetchNutrition(data.food_id, def, "grams");
      showToast(`Identified: ${data.primary_prediction} (${Math.round(data.confidence * 100)}% match)`, "success");
    } catch (err) {
      setPart1Error(err.message);
    } finally {
      setIsRecognizing(false);
    }
  };

  const fetchNutrition = async (fid, size, unit) => {
    if (!fid) return;
    setIsAnalyzingNutrition(true);
    try {
      const res = await apiFetch("/api/nutrition/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ food_id_or_name: fid, serving_size: parseFloat(size), unit })
      });
      if (!res.ok) throw new Error("Nutrition lookup failed");
      const data = await res.json();
      setNutrition(data);
    } catch (err) {
      setPart1Error(err.message);
    } finally {
      setIsAnalyzingNutrition(false);
    }
  };

  // -------------------------------------------------------------------------
  // Part 2: Produce Freshness Logic
  // -------------------------------------------------------------------------
  const processFreshnessFile = async (file) => {
    setFreshnessError(null);
    if (!file) return;
    setFreshnessImageFile(file);
    setFreshnessImagePreviewUrl(URL.createObjectURL(file));
    setIsAnalyzingFreshness(true);
    setFreshnessResult(null);
    const fd = new FormData();
    fd.append("image", file);
    try {
      const res = await apiFetch("/api/freshness/analyze", { method: "POST", body: fd });
      if (!res.ok) throw new Error("Freshness assessment failed");
      const data = await res.json();
      setFreshnessResult(data);
      showToast(`Freshness Grade: ${data.quality_grade}`, "success");
    } catch (err) {
      setFreshnessError(err.message);
    } finally {
      setIsAnalyzingFreshness(false);
    }
  };

  // -------------------------------------------------------------------------
  // Part 2: Restaurant Hygiene Logic
  // -------------------------------------------------------------------------
  const processHygieneFile = async (file) => {
    setHygieneError(null);
    if (!file) return;
    const isVideo = file.type.startsWith("video/") || file.name.endsWith(".mp4");
    setHygieneMediaType(isVideo ? "video" : "image");
    setHygieneMediaFile(file);
    setHygieneMediaPreviewUrl(URL.createObjectURL(file));
    setIsAnalyzingHygiene(true);
    setHygieneAudit(null);
    const fd = new FormData();
    fd.append(isVideo ? "video" : "image", file);
    try {
      const res = await apiFetch(isVideo ? "/api/hygiene/analyze-video" : "/api/hygiene/analyze-image", { method: "POST", body: fd });
      if (!res.ok) throw new Error("Hygiene inspection failed");
      const data = await res.json();
      setHygieneAudit(data);
      showToast(`Sanitation Rating: ${data.compliance_grade} (${data.overall_score}/100)`, "success");
    } catch (err) {
      setHygieneError(err.message);
    } finally {
      setIsAnalyzingHygiene(false);
    }
  };

  // -------------------------------------------------------------------------
  // Part 3: Cooking Chef & Recipe Generation
  // -------------------------------------------------------------------------
  const handleSendChatMessage = async (overrideText = null) => {
    const textToSend = overrideText || chatInput;
    if (!textToSend.trim()) return;

    const newMsg = { role: "user", content: textToSend, timestamp: "Just now" };
    const updatedHistory = [...chatMessages, newMsg];
    setChatMessages(updatedHistory);
    setChatInput("");
    setIsChatLoading(true);

    try {
      const res = await apiFetch("/api/cooking/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: updatedHistory,
          current_recipe: activeRecipe,
          available_ingredients: availableIngredients,
          dietary_preference: cookingDietPreference,
          allergies: cookingAllergies
        })
      });

      if (!res.ok) throw new Error("Chef chat failed");
      const data = await res.json();
      setChatMessages(prev => [...prev, {
        role: "assistant",
        content: data.reply,
        timestamp: "Just now"
      }]);

      if (data.suggested_recipes && data.suggested_recipes.length > 0) {
        setActiveRecipe(data.suggested_recipes[0]);
        setRecipeServings(data.suggested_recipes[0].servings);
      }
    } catch (err) {
      setChatMessages(prev => [...prev, {
        role: "assistant",
        content: "Sorry, I had trouble processing that request. Please try again.",
        timestamp: "Just now"
      }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleGenerateRecipes = async () => {
    if (availableIngredients.length === 0) {
      showToast("Please add at least 1 ingredient", "error");
      return;
    }
    setIsChatLoading(true);
    try {
      const res = await apiFetch("/api/recipes/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ingredients: availableIngredients,
          dietary_preference: cookingDietPreference,
          allergies: cookingAllergies,
          servings: recipeServings
        })
      });
      if (!res.ok) throw new Error("Recipe synthesis failed");
      const list = await res.json();
      if (list && list.length > 0) {
        setActiveRecipe(list[0]);
        showToast(`Created Recipe: ${list[0].title}`, "success");
      }
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleSaveRecipe = async (recipe) => {
    if (!recipe) return;
    try {
      const res = await apiFetch("/api/recipes/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipe, user_notes: "Saved from chef session" })
      });
      if (res.ok) {
        showToast(`Saved "${recipe.title}" to your favorites!`, "success");
        apiFetch("/api/recipes").then(r => r.json()).then(setSavedRecipes).catch(console.error);
      }
    } catch (e) {
      showToast(e.message, "error");
    }
  };

  // -------------------------------------------------------------------------
  // Part 3: Meal Planner Logic
  // -------------------------------------------------------------------------
  const handleGenerateMealPlan = async () => {
    setIsGeneratingPlan(true);
    try {
      const res = await apiFetch("/api/meal-plans/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile: plannerProfile,
          duration_days: plannerDuration
        })
      });
      if (!res.ok) throw new Error("Meal plan synthesis failed");
      const data = await res.json();
      setCurrentMealPlan(data);
      setGroceryChecklist(data.consolidated_grocery_list || []);
      setSelectedPlanDay(0);
      showToast(`Generated ${plannerDuration}-Day Meal Plan!`, "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const handleSaveMealPlan = async () => {
    if (!currentMealPlan) return;
    try {
      const res = await apiFetch("/api/meal-plans/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentMealPlan)
      });
      if (res.ok) {
        showToast("Meal plan stored in your account!", "success");
        apiFetch("/api/meal-plans").then(r => r.json()).then(setSavedMealPlans).catch(console.error);
      }
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  // Available common allergen tags
  const ALLERGEN_OPTIONS = ["Peanuts", "Tree Nuts", "Dairy", "Gluten", "Shellfish", "Eggs", "Soy", "Fish", "Sesame"];

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      {/* ── Top Header (Brand, Navigation Actions, User Profile) ─────────── */}
      <header className="app-header">
        <div className="brand-container" onClick={() => setActiveTab("overview")}>
          <div className="brand-logo-icon">🥗</div>
          <div>
            <div className="brand-title">
              Food Verse <span>AI</span>
            </div>
            <div className="brand-tag">Multimodal Intelligence Platform</div>
          </div>
        </div>

        {/* User Account Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
          {currentUser ? (
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
              <button
                onClick={() => setActiveTab("profile")}
                style={{
                  background: activeTab === "profile" ? "var(--primary-light)" : "rgba(255, 255, 255, 0.08)",
                  border: activeTab === "profile" ? "1px solid var(--primary)" : "1px solid var(--bg-card-border)",
                  borderRadius: "20px",
                  padding: "0.35rem 0.85rem",
                  color: "#F8FAFC",
                  fontSize: "0.82rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.45rem",
                  transition: "var(--transition)"
                }}
              >
                <span>👤</span>
                <span>{currentUser.name}</span>
              </button>
              <button
                onClick={handleLogout}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "var(--text-dim)",
                  fontSize: "0.78rem",
                  cursor: "pointer",
                  padding: "0.3rem 0.5rem"
                }}
              >
                Sign Out
              </button>
            </div>
          ) : (
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <button
                onClick={() => setActiveTab("login")}
                className={`btn btn-secondary ${activeTab === "login" ? "active" : ""}`}
                style={{ padding: "0.4rem 0.9rem", fontSize: "0.82rem", borderRadius: "8px" }}
              >
                Sign In
              </button>
              <button
                onClick={() => setActiveTab("register")}
                className="btn btn-primary"
                style={{ padding: "0.4rem 0.95rem", fontSize: "0.82rem", borderRadius: "8px" }}
              >
                Register Free
              </button>
            </div>
          )}
        </div>
      </header>

      {/* ── Main Layout: Sidebar Navigation + Dynamic View Content ────────── */}
      <div className="dashboard-wrapper">
        {/* Left Sidebar Navigation */}
        <aside className="dashboard-sidebar">
          <div className="sidebar-section-title">Core Intelligence</div>
          <button
            className={`sidebar-nav-item ${activeTab === "overview" ? "active" : ""}`}
            onClick={() => setActiveTab("overview")}
          >
            <span>🏠</span>
            <span>Home & Insights</span>
          </button>
          <button
            className={`sidebar-nav-item ${activeTab === "nutrition" ? "active" : ""}`}
            onClick={() => setActiveTab("nutrition")}
          >
            <span>🥗</span>
            <span>Food Recognition</span>
          </button>
          <button
            className={`sidebar-nav-item ${activeTab === "freshness" ? "active" : ""}`}
            onClick={() => setActiveTab("freshness")}
          >
            <span>🍎</span>
            <span>Produce Freshness</span>
          </button>
          <button
            className={`sidebar-nav-item ${activeTab === "hygiene" ? "active" : ""}`}
            onClick={() => setActiveTab("hygiene")}
          >
            <span>🛡️</span>
            <span>Kitchen Hygiene</span>
          </button>

          <div className="sidebar-section-title" style={{ marginTop: "0.85rem" }}>Culinary & Planning</div>
          <button
            className={`sidebar-nav-item ${activeTab === "cooking" ? "active" : ""}`}
            onClick={() => setActiveTab("cooking")}
          >
            <span>👨‍🍳</span>
            <span>Smart Chef Assistant</span>
          </button>
          <button
            className={`sidebar-nav-item ${activeTab === "planner" ? "active" : ""}`}
            onClick={() => setActiveTab("planner")}
          >
            <span>📅</span>
            <span>Personalized Meal Plan</span>
          </button>

          <div className="sidebar-section-title" style={{ marginTop: "0.85rem" }}>Records & Settings</div>
          <button
            className={`sidebar-nav-item ${activeTab === "history" ? "active" : ""}`}
            onClick={() => setActiveTab("history")}
          >
            <span>📋</span>
            <span>Analysis History</span>
          </button>
          <button
            className={`sidebar-nav-item ${activeTab === "profile" ? "active" : ""}`}
            onClick={() => setActiveTab("profile")}
          >
            <span>👤</span>
            <span>Profile & Dietary</span>
          </button>

          {!currentUser && (
            <div style={{ marginTop: "1rem", padding: "0.75rem", background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.2)", borderRadius: "8px" }}>
              <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--primary)", marginBottom: "0.2rem" }}>Guest Explorer</div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>Sign up to save scans and meal plans permanently.</div>
              <button onClick={() => setActiveTab("register")} className="btn btn-primary" style={{ width: "100%", padding: "0.3rem", fontSize: "0.75rem" }}>
                Create Account
              </button>
            </div>
          )}

          <div style={{ marginTop: "auto", paddingTop: "1rem", borderTop: "1px solid var(--bg-card-border)" }}>
            <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", lineHeight: 1.4 }}>
              Integrated Multimodal Vision & USDA Nutrition Engine
            </div>
            <div style={{ fontSize: "0.68rem", color: "#10B981", marginTop: "0.25rem", fontWeight: 600 }}>
              ✓ All Services Active
            </div>
          </div>
        </aside>

        {/* Dynamic Content Area */}
        <main className="dashboard-content">
          {/* ================================================================= */}
          {/* VIEW: HOME / OVERVIEW                                             */}
          {/* ================================================================= */}
          {activeTab === "overview" && (
            <div>
              {/* Hero Banner */}
              <div className="card glass-panel" style={{ padding: "2rem", marginBottom: "1.75rem", position: "relative", overflow: "hidden" }}>
                <div style={{ maxWidth: "720px", position: "relative", zIndex: 1 }}>
                  <div style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem", padding: "0.3rem 0.75rem", borderRadius: "999px", background: "var(--primary-light)", color: "var(--primary)", fontSize: "0.75rem", fontWeight: 700, marginBottom: "0.75rem" }}>
                    <span>✨</span> FULL-STACK MULTIMODAL INTELLIGENCE
                  </div>
                  <h1 style={{ fontSize: "2rem", fontWeight: 800, marginBottom: "0.5rem", letterSpacing: "-0.02em" }}>
                    {currentUser ? `Welcome back, ${currentUser.name}!` : "Welcome to Food Verse AI"}
                  </h1>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", lineHeight: 1.6, marginBottom: "1.5rem" }}>
                    Identify food dishes, calculate verified USDA macros, inspect produce freshness with visual indicators, audit kitchen sanitation, and generate zero-waste recipes tailored to your body.
                  </p>
                  <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
                    <button className="btn btn-primary" onClick={() => setActiveTab("nutrition")}>
                      <span>📸</span> Scan Food Image
                    </button>
                    <button className="btn btn-secondary" onClick={() => setActiveTab("freshness")}>
                      <span>🍎</span> Check Freshness
                    </button>
                    <button className="btn btn-secondary" onClick={() => setActiveTab("cooking")}>
                      <span>👨‍🍳</span> Ask AI Chef
                    </button>
                  </div>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-header">
                    <span>FOOD SCANS</span>
                    <span>🥗</span>
                  </div>
                  <div className="stat-value">{dashboardStats?.total_food_analyses || 0}</div>
                  <div className="stat-desc">Analyzed dishes & USDA nutrients</div>
                </div>

                <div className="stat-card">
                  <div className="stat-header">
                    <span>FRESHNESS CHECKS</span>
                    <span>🍎</span>
                  </div>
                  <div className="stat-value">{dashboardStats?.total_freshness_checks || 0}</div>
                  <div className="stat-desc">Quality & decay assessments</div>
                </div>

                <div className="stat-card">
                  <div className="stat-header">
                    <span>HYGIENE AUDITS</span>
                    <span>🛡️</span>
                  </div>
                  <div className="stat-value">{dashboardStats?.total_hygiene_audits || 0}</div>
                  <div className="stat-desc">Commercial kitchen inspections</div>
                </div>

                <div className="stat-card">
                  <div className="stat-header">
                    <span>SAVED RECIPES</span>
                    <span>🔖</span>
                  </div>
                  <div className="stat-value">{dashboardStats?.total_saved_recipes || savedRecipes.length}</div>
                  <div className="stat-desc">Favorite culinary formulas</div>
                </div>

                <div className="stat-card" style={{ borderColor: "rgba(16, 185, 129, 0.4)" }}>
                  <div className="stat-header">
                    <span>HEALTH SCORE</span>
                    <span>💚</span>
                  </div>
                  <div className="stat-value" style={{ color: "var(--primary)" }}>
                    {dashboardInsights?.overall_health_score || 85}<span style={{ fontSize: "1.1rem", color: "var(--text-dim)" }}>/100</span>
                  </div>
                  <div className="stat-desc">Based on logged nutrition metrics</div>
                </div>
              </div>

              {/* Actionable Insights & Goals */}
              <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "1.25rem", marginBottom: "1.5rem" }}>
                <div className="card" style={{ padding: "1.4rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                    <h3 style={{ fontSize: "1.05rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <span>💡</span> Actionable AI Insights
                    </h3>
                  </div>

                  {dashboardInsights?.insights && dashboardInsights.insights.length > 0 ? (
                    dashboardInsights.insights.map((ins, idx) => (
                      <div key={idx} style={{ background: "#0B1120", border: "1px solid var(--bg-card-border)", borderRadius: "8px", padding: "1rem", marginBottom: "0.75rem" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.35rem" }}>
                          <span style={{ fontWeight: 700, fontSize: "0.92rem", color: "#F8FAFC" }}>{ins.title}</span>
                          <span style={{ fontSize: "0.72rem", padding: "0.15rem 0.5rem", borderRadius: "4px", background: "rgba(16, 185, 129, 0.15)", color: "#10B981", fontWeight: 700 }}>
                            {ins.attribution?.label || "AI Verified"}
                          </span>
                        </div>
                        <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>{ins.summary}</p>
                        <ul style={{ margin: 0, paddingLeft: "1.2rem", fontSize: "0.8rem", color: "var(--text-main)" }}>
                          {ins.action_items?.map((action, aidx) => (
                            <li key={aidx} style={{ marginBottom: "0.2rem" }}>{action}</li>
                          ))}
                        </ul>
                      </div>
                    ))
                  ) : (
                    <div style={{ textAlign: "center", padding: "2rem", color: "var(--text-dim)", fontSize: "0.85rem" }}>
                      Scan a food image or run a produce check to generate instant cross-module insights.
                    </div>
                  )}
                </div>

                <div className="card" style={{ padding: "1.4rem" }}>
                  <h3 style={{ fontSize: "1.05rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
                    <span>🎯</span> Personalized Nutrition Plan
                  </h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                    {(dashboardInsights?.personalized_recommendations || [
                      "Upload your first food photo in 'Food Recognition' to discover verified USDA macro breakdowns.",
                      "Explore the Smart Cooking Assistant to generate custom zero-waste recipes from whatever is in your fridge.",
                      "Personalize your dietary preferences in Profile Settings to unlock tailored AI meal plans."
                    ]).map((rec, rIdx) => (
                      <div key={rIdx} style={{ display: "flex", alignItems: "flex-start", gap: "0.6rem", background: "#0B1120", padding: "0.85rem", borderRadius: "8px", border: "1px solid var(--bg-card-border)", fontSize: "0.84rem" }}>
                        <span style={{ color: "var(--primary)", fontWeight: "bold" }}>✓</span>
                        <span style={{ color: "var(--text-muted)", lineHeight: 1.5 }}>{rec}</span>
                      </div>
                    ))}
                  </div>

                  <div style={{ marginTop: "1rem", padding: "0.85rem", background: "rgba(6, 182, 212, 0.08)", border: "1px solid rgba(6, 182, 212, 0.2)", borderRadius: "8px", fontSize: "0.78rem", color: "#67E8F9" }}>
                    <strong>Active Framework: </strong>
                    <span style={{ textTransform: "capitalize" }}>{currentUser?.goal || "Balanced Wellness"}</span> • <span style={{ textTransform: "capitalize" }}>{currentUser?.dietary_preference || "Any Diet"}</span>
                  </div>
                </div>
              </div>

              {/* Regulatory Disclaimer */}
              <div style={{ padding: "0.85rem 1.25rem", background: "#0B1120", border: "1px solid var(--bg-card-border)", borderRadius: "8px", fontSize: "0.75rem", color: "var(--text-dim)", lineHeight: 1.5 }}>
                ⚠️ <strong>Health & Safety Notice:</strong> Nutritional figures are sourced from USDA FoodData Central and multimodal computer vision for wellness tracking. Computer vision surface analysis cannot detect internal bacteria, toxins, pathogens, or allergens. Consult certified clinical nutritionists for medical dietetics.
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* VIEW: FOOD RECOGNITION & NUTRITION                                */}
          {/* ================================================================= */}
          {activeTab === "nutrition" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1.25fr", gap: "1.5rem" }}>
              {/* Left Column: Image Upload & Recognition */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div className="card glass-panel" style={{ padding: "1.5rem" }}>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.4rem" }}>📸 Food Image Recognition</h3>
                  <p style={{ fontSize: "0.84rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
                    Upload any meal photo. Multimodal vision detects the dish and pulls verified USDA nutritional data.
                  </p>

                  <div
                    className="drop-zone"
                    onClick={() => part1FileInputRef.current?.click()}
                  >
                    <input
                      type="file"
                      ref={part1FileInputRef}
                      onChange={e => processPart1File(e.target.files?.[0])}
                      accept="image/jpeg,image/png,image/webp"
                      style={{ display: "none" }}
                    />
                    {part1ImagePreviewUrl ? (
                      <div>
                        <img src={part1ImagePreviewUrl} alt="Preview" style={{ maxHeight: "220px", borderRadius: "8px", maxWidth: "100%", objectFit: "cover" }} />
                        <div style={{ fontSize: "0.78rem", color: "var(--text-dim)", marginTop: "0.5rem" }}>
                          {part1ImageMetadata?.filename} ({part1ImageMetadata?.size})
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>📤</div>
                        <div style={{ fontSize: "0.95rem", fontWeight: 700 }}>Click to browse or drop food image</div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "0.3rem" }}>Supports JPEG, PNG, WebP (up to 10MB)</div>
                      </div>
                    )}
                  </div>

                  {/* Sample Test Images */}
                  <div style={{ marginTop: "1.25rem" }}>
                    <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.6rem" }}>
                      Or Test Instantly With Curated Meals:
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.5rem" }}>
                      {part1Samples.map(sample => (
                        <div
                          key={sample.id}
                          onClick={() => {
                            setSelectedFoodId(sample.food_id);
                            setServingSize(150);
                            setPart1ImagePreviewUrl(sample.image_url);
                            setRecognition({
                              primary_prediction: sample.title,
                              food_id: sample.food_id,
                              confidence: 0.95,
                              category: "Prepared Meal",
                              model_tier: "Multimodal Vision + USDA FoodData Central",
                              multi_item_note: sample.subtitle
                            });
                            fetchNutrition(sample.food_id, 150, "grams");
                          }}
                          style={{
                            border: "1px solid var(--bg-card-border)",
                            borderRadius: "8px",
                            padding: "0.5rem",
                            cursor: "pointer",
                            background: "#0B1120",
                            textAlign: "center",
                            transition: "var(--transition)"
                          }}
                        >
                          <img src={sample.image_url} alt={sample.title} style={{ width: "100%", height: "55px", objectFit: "cover", borderRadius: "4px", marginBottom: "0.3rem" }} />
                          <div style={{ fontSize: "0.72rem", fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {sample.title}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {isRecognizing && (
                  <div className="card" style={{ padding: "1.5rem", textAlign: "center" }}>
                    <div style={{ fontSize: "1.8rem", marginBottom: "0.5rem" }}>⚡</div>
                    <div style={{ fontWeight: 600 }}>Analyzing food composition with Multimodal AI...</div>
                  </div>
                )}

                {recognition && !isRecognizing && (
                  <div className="card" style={{ padding: "1.4rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", textTransform: "uppercase", fontWeight: 700 }}>Identified Dish</div>
                      <span className="grade-badge optimal">{Math.round(recognition.confidence * 100)}% Match</span>
                    </div>
                    <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--primary)", marginBottom: "0.35rem" }}>
                      {recognition.primary_prediction}
                    </div>
                    <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "0.75rem" }}>
                      Category: <strong>{recognition.category || "General Food"}</strong>
                    </div>

                    {recognition.multi_item_components && recognition.multi_item_components.length > 0 && (
                      <div style={{ marginTop: "0.75rem", borderTop: "1px solid var(--bg-card-border)", paddingTop: "0.75rem" }}>
                        <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: "0.4rem" }}>
                          Identified Ingredients / Components:
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.35rem" }}>
                          {recognition.multi_item_components.map((c, ci) => (
                            <div key={ci} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", background: "#0B1120", padding: "0.4rem 0.65rem", borderRadius: "6px" }}>
                              <span>• {c.name}</span>
                              <span style={{ color: "var(--text-muted)" }}>{c.percentage}% ({c.estimated_grams}g)</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {part1Error && (
                  <div style={{ padding: "0.85rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid #EF4444", borderRadius: "8px", color: "#EF4444", fontSize: "0.84rem" }}>
                    {part1Error}
                  </div>
                )}
              </div>

              {/* Right Column: Nutrition Results & Serving Scaler */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div className="card glass-panel" style={{ padding: "1.5rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
                    <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>📊 Verified USDA Nutritional Metrics</h3>
                    {nutrition && (
                      <span className="grade-badge optimal">Score: {nutrition.health_score}/100</span>
                    )}
                  </div>

                  {/* Serving Size Scaler */}
                  <div style={{ display: "flex", gap: "0.85rem", alignItems: "flex-end", marginBottom: "1.4rem", background: "#0B1120", padding: "0.85rem 1rem", borderRadius: "8px", border: "1px solid var(--bg-card-border)" }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-dim)", fontWeight: 600, marginBottom: "0.3rem" }}>
                        Serving Quantity
                      </label>
                      <input
                        type="number"
                        min="10"
                        max="2000"
                        value={servingSize}
                        onChange={e => {
                          const sz = parseFloat(e.target.value) || 100;
                          setServingSize(sz);
                          if (selectedFoodId) fetchNutrition(selectedFoodId, sz, servingUnit);
                        }}
                        style={{
                          width: "100%",
                          background: "#1E293B",
                          border: "1px solid #334155",
                          borderRadius: "6px",
                          padding: "0.45rem 0.65rem",
                          color: "#fff",
                          fontSize: "0.88rem",
                          fontWeight: 700
                        }}
                      />
                    </div>
                    <div style={{ width: "140px" }}>
                      <label style={{ display: "block", fontSize: "0.75rem", color: "var(--text-dim)", fontWeight: 600, marginBottom: "0.3rem" }}>Unit</label>
                      <select
                        value={servingUnit}
                        onChange={e => {
                          setServingUnit(e.target.value);
                          if (selectedFoodId) fetchNutrition(selectedFoodId, servingSize, e.target.value);
                        }}
                        style={{
                          width: "100%",
                          background: "#1E293B",
                          border: "1px solid #334155",
                          borderRadius: "6px",
                          padding: "0.45rem 0.65rem",
                          color: "#fff",
                          fontSize: "0.88rem",
                          fontWeight: 600
                        }}
                      >
                        <option value="grams">Grams (g)</option>
                        <option value="servings">Servings</option>
                      </select>
                    </div>
                  </div>

                  {isAnalyzingNutrition ? (
                    <div style={{ textAlign: "center", padding: "3rem" }}>Recalculating nutrients from USDA database...</div>
                  ) : nutrition ? (
                    <div>
                      {/* Macro Grid */}
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.6rem", marginBottom: "1.25rem" }}>
                        <div style={{ background: "#0B1120", padding: "0.85rem", borderRadius: "8px", textAlign: "center", border: "1px solid var(--bg-card-border)" }}>
                          <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", fontWeight: 700 }}>CALORIES</div>
                          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--primary)" }}>{Math.round(nutrition.macros.calories)}</div>
                          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>kcal</div>
                        </div>
                        <div style={{ background: "#0B1120", padding: "0.85rem", borderRadius: "8px", textAlign: "center", border: "1px solid var(--bg-card-border)" }}>
                          <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", fontWeight: 700 }}>PROTEIN</div>
                          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--cyan)" }}>{nutrition.macros.protein.toFixed(1)}</div>
                          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>grams</div>
                        </div>
                        <div style={{ background: "#0B1120", padding: "0.85rem", borderRadius: "8px", textAlign: "center", border: "1px solid var(--bg-card-border)" }}>
                          <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", fontWeight: 700 }}>CARBS</div>
                          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--accent)" }}>{nutrition.macros.carbohydrates.toFixed(1)}</div>
                          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>grams</div>
                        </div>
                        <div style={{ background: "#0B1120", padding: "0.85rem", borderRadius: "8px", textAlign: "center", border: "1px solid var(--bg-card-border)" }}>
                          <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", fontWeight: 700 }}>FAT</div>
                          <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#F472B6" }}>{nutrition.macros.fat.toFixed(1)}</div>
                          <div style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>grams</div>
                        </div>
                      </div>

                      {/* Visual Macro Energy Distribution Bar */}
                      {nutrition.calorie_distribution && (
                        <div style={{ marginBottom: "1.25rem" }}>
                          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-dim)", fontWeight: 600, marginBottom: "0.3rem" }}>
                            <span>Calorie Distribution:</span>
                            <span>
                              <span style={{ color: "var(--cyan)" }}>● {nutrition.calorie_distribution.protein_pct.toFixed(0)}% P</span> • 
                              <span style={{ color: "var(--accent)" }}> ● {nutrition.calorie_distribution.carbs_pct.toFixed(0)}% C</span> • 
                              <span style={{ color: "#F472B6" }}> ● {nutrition.calorie_distribution.fat_pct.toFixed(0)}% F</span>
                            </span>
                          </div>
                          <div className="macro-bar-container">
                            <div className="macro-bar-prot" style={{ width: `${nutrition.calorie_distribution.protein_pct}%` }} />
                            <div className="macro-bar-carb" style={{ width: `${nutrition.calorie_distribution.carbs_pct}%` }} />
                            <div className="macro-bar-fat" style={{ width: `${nutrition.calorie_distribution.fat_pct}%` }} />
                          </div>
                        </div>
                      )}

                      {/* Detailed Micro & Macro Breakdown */}
                      <div style={{ background: "#0B1120", borderRadius: "8px", padding: "1rem", marginBottom: "1.25rem", border: "1px solid var(--bg-card-border)" }}>
                        <div style={{ fontSize: "0.78rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-dim)", marginBottom: "0.6rem" }}>
                          Nutrient & Daily Recommended Value (% DV):
                        </div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "0.6rem", fontSize: "0.82rem" }}>
                          <div>Fiber: <strong>{nutrition.macros.fiber}g</strong> ({nutrition.daily_value_percentages.fiber}% DV)</div>
                          <div>Sugar: <strong>{nutrition.macros.sugar}g</strong></div>
                          <div>Sodium: <strong>{nutrition.micros.sodium}mg</strong> ({nutrition.daily_value_percentages.sodium}% DV)</div>
                          <div>Potassium: <strong>{nutrition.micros.potassium}mg</strong></div>
                          <div>Calcium: <strong>{nutrition.micros.calcium}mg</strong> ({nutrition.daily_value_percentages.calcium}% DV)</div>
                          <div>Iron: <strong>{nutrition.micros.iron}mg</strong> ({nutrition.daily_value_percentages.iron}% DV)</div>
                        </div>
                      </div>

                      {/* Health Advice & Nutri-Grade */}
                      <div style={{ display: "flex", gap: "0.85rem", alignItems: "flex-start", background: "rgba(16, 185, 129, 0.08)", border: "1px solid rgba(16, 185, 129, 0.25)", borderRadius: "8px", padding: "0.85rem 1rem" }}>
                        <div style={{ fontSize: "1.6rem" }}>💡</div>
                        <div style={{ fontSize: "0.84rem", lineHeight: 1.5 }}>
                          <strong>Nutri-Grade {nutrition.nutri_grade}: </strong>
                          {nutrition.portion_advice}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div style={{ textAlign: "center", padding: "3.5rem 1rem", color: "var(--text-dim)" }}>
                      Upload a food photo or pick a sample on the left to extract full USDA nutrient details.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* VIEW: PRODUCE FRESHNESS INTELLIGENCE                              */}
          {/* ================================================================= */}
          {activeTab === "freshness" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1.25fr", gap: "1.5rem" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div className="card glass-panel" style={{ padding: "1.5rem" }}>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.4rem" }}>🍎 Visual Produce Freshness</h3>
                  <p style={{ fontSize: "0.84rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
                    Inspect fruits & vegetables for browning, impact bruising, surface spots, and shriveling.
                  </p>

                  <div className="drop-zone" onClick={() => freshnessFileInputRef.current?.click()}>
                    <input
                      type="file"
                      ref={freshnessFileInputRef}
                      onChange={e => processFreshnessFile(e.target.files?.[0])}
                      accept="image/jpeg,image/png,image/webp"
                      style={{ display: "none" }}
                    />
                    {freshnessImagePreviewUrl ? (
                      <img src={freshnessImagePreviewUrl} alt="Freshness Preview" style={{ maxHeight: "220px", borderRadius: "8px", maxWidth: "100%", objectFit: "cover" }} />
                    ) : (
                      <div>
                        <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>🔍</div>
                        <div style={{ fontSize: "0.95rem", fontWeight: 700 }}>Upload Produce Photo</div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "0.3rem" }}>Supports Apples, Bananas, Tomatoes, Leafy Greens</div>
                      </div>
                    )}
                  </div>

                  {/* Curated Freshness Samples */}
                  <div style={{ marginTop: "1.25rem" }}>
                    <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.6rem" }}>
                      Curated Test Benchmarks:
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "0.5rem" }}>
                      {freshnessSamples.map(sample => (
                        <div
                          key={sample.id}
                          onClick={() => {
                            setFreshnessImagePreviewUrl(sample.image_url);
                            setIsAnalyzingFreshness(true);
                            setFreshnessResult(null);
                            apiFetch(sample.image_url)
                              .then(r => r.blob())
                              .then(blob => processFreshnessFile(new File([blob], sample.filename, { type: "image/jpeg" })))
                              .catch(console.error);
                          }}
                          style={{
                            border: "1px solid var(--bg-card-border)",
                            borderRadius: "8px",
                            padding: "0.6rem",
                            cursor: "pointer",
                            background: "#0B1120",
                            textAlign: "center"
                          }}
                        >
                          <img src={sample.image_url} alt={sample.title} style={{ width: "100%", height: "65px", objectFit: "cover", borderRadius: "4px", marginBottom: "0.3rem" }} />
                          <div style={{ fontSize: "0.76rem", fontWeight: 700 }}>{sample.title}</div>
                          <div style={{ fontSize: "0.68rem", color: "var(--text-dim)" }}>{sample.expected_grade}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {freshnessError && (
                  <div style={{ padding: "0.85rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid #EF4444", borderRadius: "8px", color: "#EF4444", fontSize: "0.84rem" }}>
                    {freshnessError}
                  </div>
                )}
              </div>

              {/* Freshness Findings */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div className="card glass-panel" style={{ padding: "1.5rem" }}>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "1.25rem" }}>📋 Freshness & Quality Report</h3>

                  {isAnalyzingFreshness ? (
                    <div style={{ textAlign: "center", padding: "4rem" }}>Evaluating produce surface with computer vision...</div>
                  ) : freshnessResult ? (
                    <div>
                      {/* Quality Grade Card */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0B1120", padding: "1.15rem", borderRadius: "8px", marginBottom: "1.25rem", border: "1px solid var(--bg-card-border)" }}>
                        <div>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", textTransform: "uppercase", fontWeight: 700 }}>Assessed Item</div>
                          <div style={{ fontSize: "1.3rem", fontWeight: 800 }}>{freshnessResult.item_name}</div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", textTransform: "uppercase", fontWeight: 700 }}>Grade</div>
                          <div style={{ fontSize: "1.05rem", fontWeight: 700, color: freshnessResult.quality_grade.includes("Optimal") ? "#10B981" : (freshnessResult.quality_grade.includes("Degraded") ? "#EF4444" : "#F59E0B") }}>
                            {freshnessResult.quality_grade}
                          </div>
                        </div>
                      </div>

                      {/* Visual Indicators Table */}
                      <div style={{ marginBottom: "1.25rem" }}>
                        <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: "0.5rem" }}>
                          Detected Quality Indicators:
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                          {freshnessResult.visual_indicators?.map((ind, i) => (
                            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0B1120", padding: "0.65rem 0.95rem", borderRadius: "6px", fontSize: "0.82rem", border: "1px solid var(--bg-card-border)" }}>
                              <div>
                                <span style={{ fontWeight: 700 }}>{ind.name}: </span>
                                <span style={{ color: "var(--text-muted)" }}>{ind.description}</span>
                              </div>
                              <span style={{
                                padding: "0.2rem 0.55rem",
                                borderRadius: "4px",
                                fontSize: "0.72rem",
                                fontWeight: 700,
                                background: ind.severity === "Severe" ? "rgba(239, 68, 68, 0.2)" : (ind.severity === "Moderate" ? "rgba(245, 158, 11, 0.2)" : "rgba(16, 185, 129, 0.2)"),
                                color: ind.severity === "Severe" ? "#EF4444" : (ind.severity === "Moderate" ? "#F59E0B" : "#10B981")
                              }}>
                                {ind.severity}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Storage Recommendations */}
                      {freshnessResult.storage_guide && (
                        <div style={{ background: "#0B1120", padding: "1rem", borderRadius: "8px", marginBottom: "1.25rem", border: "1px solid var(--bg-card-border)", fontSize: "0.82rem" }}>
                          <div style={{ fontWeight: 700, color: "var(--primary)", marginBottom: "0.4rem" }}>
                            Optimal Storage Parameters:
                          </div>
                          <div>Temp: <strong>{freshnessResult.storage_guide.ideal_temperature}</strong> | Humidity: <strong>{freshnessResult.storage_guide.humidity}</strong></div>
                          <div style={{ marginTop: "0.35rem", color: "var(--text-muted)" }}>
                            Estimated Shelf Life: <strong>{freshnessResult.storage_guide.shelf_life_estimate}</strong>
                          </div>
                        </div>
                      )}

                      {/* Compliance Disclaimer */}
                      <div style={{ padding: "0.75rem", background: "rgba(245, 158, 11, 0.08)", border: "1px solid rgba(245, 158, 11, 0.25)", borderRadius: "8px", fontSize: "0.74rem", color: "#FCD34D", lineHeight: 1.5 }}>
                        {freshnessResult.safety_disclaimer}
                      </div>
                    </div>
                  ) : (
                    <div style={{ textAlign: "center", padding: "4rem", color: "var(--text-dim)" }}>
                      Upload produce photo on the left to inspect visual freshness indicators and storage advice.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* VIEW: RESTAURANT KITCHEN HYGIENE                                  */}
          {/* ================================================================= */}
          {activeTab === "hygiene" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1.25fr", gap: "1.5rem" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div className="card glass-panel" style={{ padding: "1.5rem" }}>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.4rem" }}>🛡️ Commercial Kitchen Sanitation</h3>
                  <p style={{ fontSize: "0.84rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
                    Audit kitchen prep stations for uncovered food, clutter, waste bin proximity, and protective gear.
                  </p>

                  <div className="drop-zone" onClick={() => hygieneFileInputRef.current?.click()}>
                    <input
                      type="file"
                      ref={hygieneFileInputRef}
                      onChange={e => processHygieneFile(e.target.files?.[0])}
                      accept="image/jpeg,image/png,image/webp,video/mp4,video/webm"
                      style={{ display: "none" }}
                    />
                    {hygieneMediaPreviewUrl ? (
                      hygieneMediaType === "video" ? (
                        <video src={hygieneMediaPreviewUrl} controls style={{ maxHeight: "220px", borderRadius: "8px", maxWidth: "100%" }} />
                      ) : (
                        <img src={hygieneMediaPreviewUrl} alt="Hygiene Preview" style={{ maxHeight: "220px", borderRadius: "8px", maxWidth: "100%", objectFit: "cover" }} />
                      )
                    ) : (
                      <div>
                        <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>📹</div>
                        <div style={{ fontSize: "0.95rem", fontWeight: 700 }}>Upload Kitchen Photo or Video Clip</div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "0.3rem" }}>Short clips (≤30s) or prep station photos</div>
                      </div>
                    )}
                  </div>

                  {/* Benchmark Samples */}
                  <div style={{ marginTop: "1.25rem" }}>
                    <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "0.6rem" }}>
                      Curated Sanitation Benchmark Samples:
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                      {hygieneSamples.map(sample => (
                        <div
                          key={sample.id}
                          onClick={() => {
                            setHygieneMediaPreviewUrl(sample.media_url);
                            setHygieneMediaType(sample.media_type);
                            setIsAnalyzingHygiene(true);
                            setHygieneAudit(null);
                            apiFetch(sample.media_url)
                              .then(r => r.blob())
                              .then(blob => processHygieneFile(new File([blob], sample.filename, { type: sample.media_type === "video" ? "video/mp4" : "image/jpeg" })))
                              .catch(console.error);
                          }}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "0.75rem",
                            border: "1px solid var(--bg-card-border)",
                            borderRadius: "8px",
                            padding: "0.65rem 0.85rem",
                            cursor: "pointer",
                            background: "#0B1120"
                          }}
                        >
                          <span style={{ fontSize: "1.3rem" }}>{sample.media_type === "video" ? "🎬" : "📸"}</span>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: "0.84rem", fontWeight: 700 }}>{sample.title}</div>
                            <div style={{ fontSize: "0.72rem", color: "var(--text-dim)" }}>{sample.subtitle}</div>
                          </div>
                          <span style={{ fontSize: "0.76rem", color: "var(--primary)", fontWeight: 700 }}>{sample.expected_rating}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {hygieneError && (
                  <div style={{ padding: "0.85rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid #EF4444", borderRadius: "8px", color: "#EF4444", fontSize: "0.84rem" }}>
                    {hygieneError}
                  </div>
                )}
              </div>

              {/* Hygiene Audit Results */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div className="card glass-panel" style={{ padding: "1.5rem" }}>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "1.25rem" }}>📝 Sanitation Audit Report</h3>

                  {isAnalyzingHygiene ? (
                    <div style={{ textAlign: "center", padding: "4rem" }}>Running temporal frame sanitation audit...</div>
                  ) : hygieneAudit ? (
                    <div>
                      {/* Score Summary */}
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0B1120", padding: "1.15rem", borderRadius: "8px", marginBottom: "1.25rem", border: "1px solid var(--bg-card-border)" }}>
                        <div>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", textTransform: "uppercase", fontWeight: 700 }}>COMPLIANCE RATING</div>
                          <div style={{ fontSize: "1.5rem", fontWeight: 800, color: hygieneAudit.overall_score >= 80 ? "#10B981" : "#EF4444" }}>
                            {hygieneAudit.compliance_grade}
                          </div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", textTransform: "uppercase", fontWeight: 700 }}>SANITATION SCORE</div>
                          <div style={{ fontSize: "1.5rem", fontWeight: 800 }}>
                            {hygieneAudit.overall_score}<span style={{ fontSize: "1rem", color: "var(--text-dim)" }}>/100</span>
                          </div>
                        </div>
                      </div>

                      {/* Checklist & Auditor Actions */}
                      <div style={{ marginBottom: "1.25rem" }}>
                        <div style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--text-dim)", textTransform: "uppercase", marginBottom: "0.6rem" }}>
                          HACCP Sanitation Inspection Checklist:
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                          {hygieneAudit.checklist?.map((item, idx) => (
                            <div key={idx} style={{ background: "#0B1120", border: "1px solid var(--bg-card-border)", borderRadius: "8px", padding: "0.85rem" }}>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.35rem" }}>
                                <span style={{ fontWeight: 700, fontSize: "0.88rem" }}>{item.category}: {item.item_name}</span>
                                <span style={{
                                  padding: "0.2rem 0.55rem",
                                  borderRadius: "4px",
                                  fontSize: "0.72rem",
                                  fontWeight: 700,
                                  background: item.status === "Pass" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                                  color: item.status === "Pass" ? "#10B981" : "#EF4444"
                                }}>
                                  {item.status}
                                </span>
                              </div>
                              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
                                {item.finding_summary}
                              </div>
                              <div style={{ display: "flex", gap: "0.5rem" }}>
                                <button
                                  onClick={async () => {
                                    try {
                                      const r = await apiFetch(`/api/hygiene/reviews/${item.item_id}?audit_id=${hygieneAudit.audit_id}`, {
                                        method: "POST",
                                        headers: { "Content-Type": "application/json" },
                                        body: JSON.stringify({ reviewer_status: "Approved", reviewer_notes: "Approved by inspector", reviewer_name: reviewerName })
                                      });
                                      if (r.ok) showToast(`Marked ${item.item_name} as Approved`, "success");
                                    } catch (e) { console.error(e); }
                                  }}
                                  style={{ padding: "0.25rem 0.65rem", fontSize: "0.74rem", background: "rgba(16, 185, 129, 0.15)", border: "1px solid #10B981", color: "#10B981", borderRadius: "4px", cursor: "pointer", fontWeight: 600 }}
                                >
                                  ✓ Mark Approved
                                </button>
                                <button
                                  onClick={async () => {
                                    try {
                                      const r = await apiFetch(`/api/hygiene/reviews/${item.item_id}?audit_id=${hygieneAudit.audit_id}`, {
                                        method: "POST",
                                        headers: { "Content-Type": "application/json" },
                                        body: JSON.stringify({ reviewer_status: "Flagged", reviewer_notes: "Action required on station", reviewer_name: reviewerName })
                                      });
                                      if (r.ok) showToast(`Flagged ${item.item_name} for sanitation review`, "error");
                                    } catch (e) { console.error(e); }
                                  }}
                                  style={{ padding: "0.25rem 0.65rem", fontSize: "0.74rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid #EF4444", color: "#EF4444", borderRadius: "4px", cursor: "pointer", fontWeight: 600 }}
                                >
                                  ⚠️ Flag for Action
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div style={{ textAlign: "center", padding: "4rem", color: "var(--text-dim)" }}>
                      Upload kitchen photo or video clip to audit visible commercial sanitation protocols.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* VIEW: SMART COOKING ASSISTANT                                     */}
          {/* ================================================================= */}
          {activeTab === "cooking" && (
            <div style={{ display: "grid", gridTemplateColumns: "1.1fr 1.3fr", gap: "1.5rem" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                {/* Ingredients in Fridge */}
                <div className="card glass-panel" style={{ padding: "1.4rem" }}>
                  <h3 style={{ fontSize: "1.05rem", fontWeight: 700, marginBottom: "0.5rem" }}>🥕 Available Ingredients</h3>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.45rem", marginBottom: "0.85rem" }}>
                    {availableIngredients.map((ing, idx) => (
                      <span key={idx} style={{ background: "#1E293B", padding: "0.35rem 0.75rem", borderRadius: "999px", fontSize: "0.82rem", display: "inline-flex", alignItems: "center", gap: "0.45rem" }}>
                        {ing}
                        <span
                          onClick={() => setAvailableIngredients(prev => prev.filter((_, i) => i !== idx))}
                          style={{ cursor: "pointer", color: "var(--text-dim)", fontWeight: "bold" }}
                        >
                          ×
                        </span>
                      </span>
                    ))}
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <input
                      type="text"
                      placeholder="Add an ingredient (e.g. Garlic, Eggs, Rice)..."
                      value={newIngredientInput}
                      onChange={e => setNewIngredientInput(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === "Enter" && newIngredientInput.trim()) {
                          setAvailableIngredients(prev => [...prev, newIngredientInput.trim()]);
                          setNewIngredientInput("");
                        }
                      }}
                      style={{ flex: 1, background: "#0B1120", border: "1px solid #334155", borderRadius: "6px", padding: "0.45rem 0.75rem", color: "#fff", fontSize: "0.84rem" }}
                    />
                    <button
                      onClick={() => {
                        if (newIngredientInput.trim()) {
                          setAvailableIngredients(prev => [...prev, newIngredientInput.trim()]);
                          setNewIngredientInput("");
                        }
                      }}
                      className="btn btn-secondary"
                      style={{ padding: "0.45rem 0.85rem", fontSize: "0.82rem" }}
                    >
                      + Add
                    </button>
                  </div>
                  <div style={{ marginTop: "0.85rem" }}>
                    <button onClick={handleGenerateRecipes} className="btn btn-primary" style={{ width: "100%", padding: "0.55rem", fontSize: "0.88rem" }}>
                      ✨ Generate Custom Recipes from Ingredients
                    </button>
                  </div>
                </div>

                {/* Chef Chat Session */}
                <div className="card" style={{ padding: "1.4rem", display: "flex", flexDirection: "column", height: "420px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem", borderBottom: "1px solid var(--bg-card-border)", paddingBottom: "0.5rem" }}>
                    <h4 style={{ fontSize: "1rem", fontWeight: 700 }}>👨‍🍳 Food Verse Chef Chat</h4>
                  </div>

                  <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "0.6rem", marginBottom: "0.75rem", paddingRight: "0.25rem" }}>
                    {chatMessages.map((msg, i) => (
                      <div
                        key={i}
                        style={{
                          alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                          maxWidth: "85%",
                          background: msg.role === "user" ? "var(--primary)" : "#1E293B",
                          color: msg.role === "user" ? "#022013" : "#F8FAFC",
                          padding: "0.65rem 0.95rem",
                          borderRadius: "12px",
                          fontSize: "0.85rem",
                          fontWeight: msg.role === "user" ? 600 : 400,
                          lineHeight: 1.5
                        }}
                      >
                        {msg.content}
                      </div>
                    ))}
                    {isChatLoading && (
                      <div style={{ alignSelf: "flex-start", background: "#1E293B", padding: "0.5rem 0.8rem", borderRadius: "12px", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        Chef is formulating recipe tips...
                      </div>
                    )}
                    <div ref={chatMessagesEndRef} />
                  </div>

                  {/* Input Box */}
                  <div style={{ display: "flex", gap: "0.5rem" }}>
                    <input
                      type="text"
                      placeholder="Ask for substitutions, cooking tips, or steps..."
                      value={chatInput}
                      onChange={e => setChatInput(e.target.value)}
                      onKeyDown={e => e.key === "Enter" && handleSendChatMessage()}
                      style={{ flex: 1, background: "#0B1120", border: "1px solid #334155", borderRadius: "6px", padding: "0.5rem 0.75rem", color: "#fff", fontSize: "0.85rem" }}
                    />
                    <button onClick={() => handleSendChatMessage()} className="btn btn-primary" style={{ padding: "0.5rem 1rem", fontSize: "0.85rem" }}>
                      Send
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Column: Recipe Card */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div className="card glass-panel" style={{ padding: "1.5rem" }}>
                  {activeRecipe ? (
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
                        <div>
                          <div style={{ fontSize: "0.75rem", color: "var(--primary)", fontWeight: 700, textTransform: "uppercase" }}>{activeRecipe.cuisine} CUISINE</div>
                          <h2 style={{ fontSize: "1.45rem", fontWeight: 800 }}>{activeRecipe.title}</h2>
                          <div style={{ fontSize: "0.84rem", color: "var(--text-muted)" }}>{activeRecipe.description}</div>
                        </div>
                        <button
                          onClick={() => handleSaveRecipe(activeRecipe)}
                          className="btn btn-secondary"
                          style={{ padding: "0.45rem 0.85rem", fontSize: "0.82rem", whiteSpace: "nowrap" }}
                        >
                          🔖 Save Recipe
                        </button>
                      </div>

                      {/* Cook Stats */}
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.5rem", background: "#0B1120", padding: "0.85rem", borderRadius: "8px", marginBottom: "1.25rem", textAlign: "center", border: "1px solid var(--bg-card-border)" }}>
                        <div>
                          <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", fontWeight: 700 }}>PREP</div>
                          <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>{activeRecipe.prep_time_minutes}m</div>
                        </div>
                        <div>
                          <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", fontWeight: 700 }}>COOK</div>
                          <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>{activeRecipe.cook_time_minutes}m</div>
                        </div>
                        <div>
                          <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", fontWeight: 700 }}>SERVINGS</div>
                          <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>{activeRecipe.servings}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: "0.68rem", color: "var(--text-dim)", fontWeight: 700 }}>CALORIES</div>
                          <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--primary)" }}>{Math.round(activeRecipe.nutrition_per_serving?.calories || 0)}</div>
                        </div>
                      </div>

                      {/* Ingredients */}
                      <div style={{ marginBottom: "1.25rem" }}>
                        <h4 style={{ fontSize: "0.82rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-dim)", marginBottom: "0.5rem" }}>
                          Ingredients Needed:
                        </h4>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: "0.45rem", fontSize: "0.84rem" }}>
                          {activeRecipe.ingredients?.map((ing, i) => (
                            <div key={i} style={{ background: "#0B1120", padding: "0.45rem 0.75rem", borderRadius: "6px", border: "1px solid var(--bg-card-border)" }}>
                              • <strong>{ing.amount} {ing.unit}</strong> {ing.name}
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Instructions */}
                      <div>
                        <h4 style={{ fontSize: "0.82rem", fontWeight: 700, textTransform: "uppercase", color: "var(--text-dim)", marginBottom: "0.5rem" }}>
                          Preparation Steps:
                        </h4>
                        <div style={{ display: "flex", flexDirection: "column", gap: "0.55rem" }}>
                          {activeRecipe.instructions?.map((step, idx) => (
                            <div key={idx} style={{ display: "flex", gap: "0.75rem", background: "#0B1120", padding: "0.7rem 0.95rem", borderRadius: "6px", fontSize: "0.84rem", lineHeight: 1.5, border: "1px solid var(--bg-card-border)" }}>
                              <span style={{ fontWeight: 800, color: "var(--primary)" }}>{step.step_number}.</span>
                              <span style={{ color: "#F8FAFC" }}>{step.instruction}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div style={{ textAlign: "center", padding: "5rem 1rem", color: "var(--text-dim)" }}>
                      <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>🍲</div>
                      <div style={{ fontWeight: 700, fontSize: "1.05rem" }}>No Recipe Active</div>
                      <div style={{ fontSize: "0.82rem", marginTop: "0.3rem" }}>
                        Add your ingredients on the left and click "Generate Custom Recipes" or ask the AI Chef.
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* VIEW: PERSONALIZED MEAL PLANNER                                   */}
          {/* ================================================================= */}
          {activeTab === "planner" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: "1.5rem" }}>
              {/* Profile Config */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div className="card glass-panel" style={{ padding: "1.5rem" }}>
                  <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "0.4rem" }}>📋 Meal Plan Parameters</h3>

                  <div style={{ marginBottom: "0.85rem" }}>
                    <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-dim)", fontWeight: 600, marginBottom: "0.3rem" }}>
                      Dietary Framework
                    </label>
                    <select
                      value={plannerProfile.dietary_preference}
                      onChange={e => setPlannerProfile({ ...plannerProfile, dietary_preference: e.target.value })}
                      style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "6px", padding: "0.5rem", color: "#fff", fontSize: "0.85rem" }}
                    >
                      <option value="vegetarian">Vegetarian (Plant-Forward)</option>
                      <option value="vegan">Vegan (Strict Plant-Only)</option>
                      <option value="non-vegetarian">Omnivore / High-Protein</option>
                    </select>
                  </div>

                  <div style={{ marginBottom: "0.85rem" }}>
                    <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-dim)", fontWeight: 600, marginBottom: "0.3rem" }}>
                      Fitness & Metabolic Goal
                    </label>
                    <select
                      value={plannerProfile.goal}
                      onChange={e => setPlannerProfile({ ...plannerProfile, goal: e.target.value })}
                      style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "6px", padding: "0.5rem", color: "#fff", fontSize: "0.85rem" }}
                    >
                      <option value="balanced">Balanced Wellness & Vitality</option>
                      <option value="weight_loss">Calorie Deficit / Fat Loss</option>
                      <option value="muscle_gain">Hypertrophy / Lean Muscle Mass</option>
                    </select>
                  </div>

                  <div style={{ marginBottom: "0.85rem" }}>
                    <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-dim)", fontWeight: 600, marginBottom: "0.3rem" }}>
                      Meals Per Day
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      {[2, 3, 4, 5].map(cnt => (
                        <button
                          key={cnt}
                          onClick={() => setPlannerProfile({ ...plannerProfile, meals_per_day: cnt })}
                          style={{
                            flex: 1,
                            padding: "0.45rem",
                            borderRadius: "6px",
                            background: plannerProfile.meals_per_day === cnt ? "var(--primary)" : "#0B1120",
                            color: plannerProfile.meals_per_day === cnt ? "#022013" : "#fff",
                            border: "1px solid #334155",
                            fontWeight: 700,
                            cursor: "pointer"
                          }}
                        >
                          {cnt}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div style={{ marginBottom: "1.25rem" }}>
                    <label style={{ display: "block", fontSize: "0.78rem", color: "var(--text-dim)", fontWeight: 600, marginBottom: "0.3rem" }}>
                      Duration (Days)
                    </label>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      {[3, 5, 7].map(d => (
                        <button
                          key={d}
                          onClick={() => setPlannerDuration(d)}
                          style={{
                            flex: 1,
                            padding: "0.45rem",
                            borderRadius: "6px",
                            background: plannerDuration === d ? "var(--primary)" : "#0B1120",
                            color: plannerDuration === d ? "#022013" : "#fff",
                            border: "1px solid #334155",
                            fontWeight: 700,
                            cursor: "pointer"
                          }}
                        >
                          {d} Days
                        </button>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={handleGenerateMealPlan}
                    disabled={isGeneratingPlan}
                    className="btn btn-primary"
                    style={{ width: "100%", padding: "0.65rem", fontSize: "0.9rem" }}
                  >
                    {isGeneratingPlan ? "Synthesizing AI Meal Plan..." : `✨ Generate ${plannerDuration}-Day Meal Plan`}
                  </button>
                </div>

                {/* Consolidated Grocery List */}
                {groceryChecklist.length > 0 && (
                  <div className="card" style={{ padding: "1.4rem" }}>
                    <h4 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "0.75rem", display: "flex", justifyContent: "space-between" }}>
                      <span>🛒 Grocery Shopping List</span>
                      <span style={{ fontSize: "0.78rem", color: "var(--primary)" }}>{groceryChecklist.filter(g => g.checked).length}/{groceryChecklist.length}</span>
                    </h4>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", maxHeight: "250px", overflowY: "auto" }}>
                      {groceryChecklist.map((item, idx) => (
                        <div
                          key={idx}
                          onClick={() => {
                            setGroceryChecklist(prev => prev.map((g, i) => i === idx ? { ...g, checked: !g.checked } : g));
                          }}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "0.6rem",
                            padding: "0.45rem 0.65rem",
                            background: "#0B1120",
                            borderRadius: "6px",
                            cursor: "pointer",
                            fontSize: "0.82rem",
                            textDecoration: item.checked ? "line-through" : "none",
                            opacity: item.checked ? 0.5 : 1
                          }}
                        >
                          <input type="checkbox" checked={item.checked} readOnly />
                          <span style={{ flex: 1 }}>{item.name} ({item.quantity_str})</span>
                          <span style={{ fontSize: "0.7rem", color: "var(--text-dim)" }}>{item.category}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Meal Plan Daily Cards */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
                <div className="card glass-panel" style={{ padding: "1.5rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
                    <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>📅 Daily Schedule</h3>
                    {currentMealPlan && (
                      <button onClick={handleSaveMealPlan} className="btn btn-secondary" style={{ padding: "0.4rem 0.85rem", fontSize: "0.82rem" }}>
                        💾 Save Plan
                      </button>
                    )}
                  </div>

                  {isGeneratingPlan ? (
                    <div style={{ textAlign: "center", padding: "5rem" }}>Computing target macros and daily schedule...</div>
                  ) : currentMealPlan ? (
                    <div>
                      {/* Day Selector Tabs */}
                      <div style={{ display: "flex", gap: "0.45rem", overflowX: "auto", paddingBottom: "0.6rem", marginBottom: "1.25rem" }}>
                        {currentMealPlan.daily_plans?.map((dp, i) => (
                          <button
                            key={i}
                            onClick={() => setSelectedPlanDay(i)}
                            style={{
                              padding: "0.45rem 0.85rem",
                              borderRadius: "8px",
                              background: selectedPlanDay === i ? "var(--primary)" : "#0B1120",
                              color: selectedPlanDay === i ? "#022013" : "#fff",
                              border: "1px solid #334155",
                              fontWeight: 700,
                              fontSize: "0.82rem",
                              cursor: "pointer",
                              whiteSpace: "nowrap"
                            }}
                          >
                            Day {dp.day_number}: {dp.day_name}
                          </button>
                        ))}
                      </div>

                      {/* Daily Totals Bar */}
                      {currentMealPlan.daily_plans?.[selectedPlanDay] && (
                        <div>
                          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "0.5rem", background: "#0B1120", padding: "0.75rem", borderRadius: "8px", marginBottom: "1.25rem", textAlign: "center", fontSize: "0.82rem", border: "1px solid var(--bg-card-border)" }}>
                            <div>Cals: <strong>{Math.round(currentMealPlan.daily_plans[selectedPlanDay].daily_calories)}</strong></div>
                            <div>Protein: <strong>{currentMealPlan.daily_plans[selectedPlanDay].daily_protein.toFixed(0)}g</strong></div>
                            <div>Carbs: <strong>{currentMealPlan.daily_plans[selectedPlanDay].daily_carbs.toFixed(0)}g</strong></div>
                            <div>Fat: <strong>{currentMealPlan.daily_plans[selectedPlanDay].daily_fat.toFixed(0)}g</strong></div>
                          </div>

                          {/* Meal Cards */}
                          <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
                            {currentMealPlan.daily_plans[selectedPlanDay].meals?.map((meal, mIdx) => (
                              <div key={mIdx} style={{ background: "#0B1120", border: "1px solid var(--bg-card-border)", borderRadius: "8px", padding: "1rem" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.35rem" }}>
                                  <span style={{ fontSize: "0.78rem", fontWeight: 800, color: "var(--primary)", textTransform: "uppercase" }}>
                                    {meal.meal_type}
                                  </span>
                                  <span style={{ fontSize: "0.76rem", color: "var(--text-dim)" }}>
                                    {Math.round(meal.nutrition?.calories || 0)} kcal • {meal.nutrition?.protein?.toFixed(0) || 0}g protein
                                  </span>
                                </div>
                                <div style={{ fontSize: "1.05rem", fontWeight: 700, marginBottom: "0.25rem" }}>
                                  {meal.meal_name}
                                </div>
                                <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "0.5rem" }}>
                                  {meal.description}
                                </div>
                                <div style={{ fontSize: "0.76rem", color: "var(--text-dim)" }}>
                                  Ingredients: {meal.ingredients?.map(ing => `${ing.amount} ${ing.unit} ${ing.name}`).join(", ")}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{ textAlign: "center", padding: "5rem 1rem", color: "var(--text-dim)" }}>
                      Select your dietary goal on the left to synthesize an adaptive multi-day meal plan.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* VIEW: ANALYSIS & RECIPE HISTORY                                   */}
          {/* ================================================================= */}
          {activeTab === "history" && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
                <div>
                  <h2 style={{ fontSize: "1.45rem", fontWeight: 800 }}>📋 Historical Records & Saved Intelligence</h2>
                  <div style={{ fontSize: "0.84rem", color: "var(--text-muted)" }}>
                    {currentUser ? `User-isolated archive for ${currentUser.name}` : "Sign in to save and sync your records permanently"}
                  </div>
                </div>

                {/* Sub-Category Selector */}
                <div style={{ display: "flex", gap: "0.45rem" }}>
                  {[
                    { id: "food", label: "🥗 Food Scans" },
                    { id: "freshness", label: "🍎 Freshness" },
                    { id: "hygiene", label: "🛡️ Hygiene" },
                    { id: "recipes", label: "🔖 Saved Recipes" },
                    { id: "meal-plans", label: "📅 Meal Plans" }
                  ].map(cat => (
                    <button
                      key={cat.id}
                      onClick={() => { setHistoryCategory(cat.id); setHistoryPage(1); }}
                      style={{
                        padding: "0.45rem 0.85rem",
                        borderRadius: "8px",
                        background: historyCategory === cat.id ? "var(--primary)" : "#1E293B",
                        color: historyCategory === cat.id ? "#022013" : "#F8FAFC",
                        border: "1px solid #334155",
                        fontSize: "0.82rem",
                        fontWeight: 700,
                        cursor: "pointer"
                      }}
                    >
                      {cat.label}
                    </button>
                  ))}
                </div>
              </div>

              {loadingHistory ? (
                <div style={{ textAlign: "center", padding: "4rem" }}>Retrieving archive records...</div>
              ) : historyItems.length > 0 ? (
                <div>
                  {historyItems.map((item, idx) => (
                    <div key={idx} className="history-item-card">
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "0.3rem" }}>
                          <span style={{ fontWeight: 800, fontSize: "1rem" }}>
                            {item.primary_prediction || item.item_name || item.title || `Meal Plan (${item.duration_days} Days)`}
                          </span>
                          <span style={{ fontSize: "0.75rem", color: "var(--text-dim)" }}>
                            {item.created_at ? new Date(item.created_at).toLocaleString() : ""}
                          </span>
                        </div>

                        <div style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                          {item.quality_grade && <span>Quality: <strong>{item.quality_grade}</strong> • </span>}
                          {item.compliance_grade && <span>Rating: <strong>{item.compliance_grade}</strong> ({item.overall_score}/100) • </span>}
                          {item.cuisine && <span>Cuisine: <strong>{item.cuisine}</strong> • Prep: {item.prep_time_minutes}m • </span>}
                          {item.confidence && <span>Confidence: <strong>{Math.round(item.confidence * 100)}%</strong> • </span>}
                          {item.goal && <span>Goal: <strong>{item.goal}</strong></span>}
                        </div>
                      </div>

                      <button
                        onClick={() => handleDeleteHistoryItem(historyCategory, item.id)}
                        style={{
                          background: "rgba(239, 68, 68, 0.15)",
                          border: "1px solid #EF4444",
                          color: "#EF4444",
                          padding: "0.35rem 0.85rem",
                          borderRadius: "6px",
                          fontSize: "0.78rem",
                          fontWeight: 700,
                          cursor: "pointer"
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  ))}

                  {/* Pagination */}
                  <div className="pagination-bar">
                    <div style={{ fontSize: "0.82rem", color: "var(--text-dim)" }}>
                      Page {historyPage} of {historyTotalPages} ({historyTotal} Records Found)
                    </div>
                    <div style={{ display: "flex", gap: "0.5rem" }}>
                      <button
                        className="pagination-btn"
                        disabled={historyPage <= 1}
                        onClick={() => { const p = historyPage - 1; setHistoryPage(p); fetchHistory(historyCategory, p); }}
                      >
                        ← Previous
                      </button>
                      <button
                        className="pagination-btn"
                        disabled={historyPage >= historyTotalPages}
                        onClick={() => { const p = historyPage + 1; setHistoryPage(p); fetchHistory(historyCategory, p); }}
                      >
                        Next →
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="card" style={{ textAlign: "center", padding: "5rem 1rem", color: "var(--text-dim)" }}>
                  <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>📂</div>
                  <div style={{ fontWeight: 700, fontSize: "1.05rem" }}>No Historical Records in This Category</div>
                  <div style={{ fontSize: "0.82rem", marginTop: "0.35rem" }}>
                    Run a food scan or save a recipe while signed in to build your personal culinary log.
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ================================================================= */}
          {/* VIEW: DEDICATED USER PROFILE & DIETARY SETTINGS                   */}
          {/* ================================================================= */}
          {activeTab === "profile" && (
            <div className="profile-page-container">
              {currentUser ? (
                <div className="card glass-panel" style={{ padding: "2.25rem" }}>
                  <div className="profile-avatar-banner">
                    <div className="profile-avatar-circle">
                      {currentUser.name ? currentUser.name.charAt(0).toUpperCase() : "U"}
                    </div>
                    <div style={{ flex: 1 }}>
                      <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>{currentUser.name}</h2>
                      <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>{currentUser.email}</div>
                      <div style={{ display: "inline-block", marginTop: "0.4rem", padding: "0.2rem 0.6rem", borderRadius: "999px", background: "var(--primary-light)", color: "var(--primary)", fontSize: "0.72rem", fontWeight: 700 }}>
                        Verified Food Verse Member
                      </div>
                    </div>
                  </div>

                  <form onSubmit={handleProfileSave}>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem", marginBottom: "1.25rem" }}>
                      <div>
                        <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, marginBottom: "0.35rem" }}>
                          Display Name
                        </label>
                        <input
                          type="text"
                          value={profileForm.name}
                          onChange={e => setProfileForm({ ...profileForm, name: e.target.value })}
                          style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "8px", padding: "0.55rem 0.85rem", color: "#fff", fontSize: "0.88rem" }}
                        />
                      </div>

                      <div>
                        <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, marginBottom: "0.35rem" }}>
                          Account Email
                        </label>
                        <input
                          type="text"
                          value={currentUser.email}
                          disabled
                          style={{ width: "100%", background: "#070A0F", border: "1px solid #1E293B", borderRadius: "8px", padding: "0.55rem 0.85rem", color: "var(--text-dim)", fontSize: "0.88rem" }}
                        />
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem", marginBottom: "1.5rem" }}>
                      <div>
                        <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, marginBottom: "0.35rem" }}>
                          Dietary Framework
                        </label>
                        <select
                          value={profileForm.dietary_preference}
                          onChange={e => setProfileForm({ ...profileForm, dietary_preference: e.target.value })}
                          style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "8px", padding: "0.55rem 0.85rem", color: "#fff", fontSize: "0.88rem" }}
                        >
                          <option value="any">Omnivore (Standard / Flexible)</option>
                          <option value="vegetarian">Vegetarian (Lacto-Ovo)</option>
                          <option value="vegan">Vegan (Strict Plant-Only)</option>
                          <option value="non-vegetarian">High-Protein Omnivore</option>
                        </select>
                      </div>

                      <div>
                        <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, marginBottom: "0.35rem" }}>
                          Metabolic & Fitness Goal
                        </label>
                        <select
                          value={profileForm.goal}
                          onChange={e => setProfileForm({ ...profileForm, goal: e.target.value })}
                          style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "8px", padding: "0.55rem 0.85rem", color: "#fff", fontSize: "0.88rem" }}
                        >
                          <option value="balanced">Balanced Wellness & Vitality</option>
                          <option value="weight_loss">Calorie Deficit / Fat Loss</option>
                          <option value="muscle_gain">Hypertrophy / Lean Muscle Mass</option>
                        </select>
                      </div>
                    </div>

                    {/* Interactive Allergen Exclusion Pills */}
                    <div style={{ marginBottom: "1.75rem" }}>
                      <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, marginBottom: "0.35rem" }}>
                        Strict Allergen Exclusions (Click to Toggle):
                      </label>
                      <div className="allergen-chip-group">
                        {ALLERGEN_OPTIONS.map(allergen => {
                          const isSelected = profileForm.allergies.map(a => a.toLowerCase()).includes(allergen.toLowerCase());
                          return (
                            <span
                              key={allergen}
                              className={`allergen-chip ${isSelected ? "selected" : ""}`}
                              onClick={() => toggleAllergen(allergen.toLowerCase())}
                            >
                              {isSelected ? "🚫" : "+"} {allergen}
                            </span>
                          );
                        })}
                      </div>
                    </div>

                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid var(--bg-card-border)", paddingTop: "1.25rem" }}>
                      <button
                        type="button"
                        onClick={handleLogout}
                        className="btn btn-secondary"
                        style={{ color: "#EF4444" }}
                      >
                        Sign Out of Session
                      </button>
                      <button
                        type="submit"
                        disabled={profileSaving}
                        className="btn btn-primary"
                        style={{ padding: "0.55rem 1.75rem" }}
                      >
                        {profileSaving ? "Saving..." : "Save Profile Changes"}
                      </button>
                    </div>
                  </form>
                </div>
              ) : (
                <div className="card glass-panel" style={{ padding: "3rem 1.5rem", textAlign: "center" }}>
                  <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>🔐</div>
                  <h2 style={{ fontSize: "1.5rem", fontWeight: 800, marginBottom: "0.5rem" }}>User Account Required</h2>
                  <p style={{ color: "var(--text-muted)", maxWidth: "450px", margin: "0 auto 1.5rem", fontSize: "0.9rem" }}>
                    Sign in to personalize your culinary preferences, set allergen exclusions, and sync analysis history.
                  </p>
                  <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center" }}>
                    <button onClick={() => setActiveTab("login")} className="btn btn-primary" style={{ padding: "0.55rem 1.5rem" }}>
                      Sign In Now
                    </button>
                    <button onClick={() => setActiveTab("register")} className="btn btn-secondary" style={{ padding: "0.55rem 1.5rem" }}>
                      Create Account
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ================================================================= */}
          {/* VIEW: DEDICATED SIGN IN PAGE                                      */}
          {/* ================================================================= */}
          {activeTab === "login" && (
            <div className="auth-page-container">
              <div className="auth-card">
                <div style={{ textAlign: "center", marginBottom: "1.75rem" }}>
                  <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>🥗</div>
                  <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>Sign In to Food Verse AI</h2>
                  <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                    Access your personalized nutrition logs and recipe archives.
                  </p>
                </div>

                <form onSubmit={handleLoginSubmit}>
                  <div style={{ marginBottom: "1rem" }}>
                    <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, marginBottom: "0.35rem" }}>Email Address</label>
                    <input
                      type="email"
                      placeholder="chef@example.com"
                      value={loginEmail}
                      onChange={e => setLoginEmail(e.target.value)}
                      required
                      style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "8px", padding: "0.6rem 0.85rem", color: "#fff", fontSize: "0.88rem" }}
                    />
                  </div>

                  <div style={{ marginBottom: "1.4rem" }}>
                    <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, marginBottom: "0.35rem" }}>Password</label>
                    <input
                      type="password"
                      placeholder="••••••••"
                      value={loginPassword}
                      onChange={e => setLoginPassword(e.target.value)}
                      required
                      style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "8px", padding: "0.6rem 0.85rem", color: "#fff", fontSize: "0.88rem" }}
                    />
                  </div>

                  {authError && (
                    <div style={{ padding: "0.65rem 0.85rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid #EF4444", borderRadius: "8px", color: "#EF4444", fontSize: "0.82rem", marginBottom: "1.25rem" }}>
                      {authError}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={authLoading}
                    className="btn btn-primary"
                    style={{ width: "100%", padding: "0.7rem", fontSize: "0.95rem" }}
                  >
                    {authLoading ? "Authenticating..." : "Sign In"}
                  </button>
                </form>

                <div style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                  Don't have an account yet?{" "}
                  <span
                    onClick={() => setActiveTab("register")}
                    style={{ color: "var(--primary)", fontWeight: 700, cursor: "pointer", textDecoration: "underline" }}
                  >
                    Register here →
                  </span>
                </div>

                <div style={{ textAlign: "center", marginTop: "1rem" }}>
                  <button
                    onClick={() => setActiveTab("overview")}
                    style={{ background: "transparent", border: "none", color: "var(--text-dim)", fontSize: "0.8rem", cursor: "pointer" }}
                  >
                    Continue Exploring as Guest
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ================================================================= */}
          {/* VIEW: DEDICATED REGISTRATION PAGE                                 */}
          {/* ================================================================= */}
          {activeTab === "register" && (
            <div className="auth-page-container">
              <div className="auth-card">
                <div style={{ textAlign: "center", marginBottom: "1.75rem" }}>
                  <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>👨‍🍳</div>
                  <h2 style={{ fontSize: "1.5rem", fontWeight: 800 }}>Create Your Account</h2>
                  <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                    Get started with AI-powered food intelligence & tailored meal planning.
                  </p>
                </div>

                <form onSubmit={handleRegisterSubmit}>
                  <div style={{ marginBottom: "1rem" }}>
                    <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, marginBottom: "0.35rem" }}>Full Name</label>
                    <input
                      type="text"
                      placeholder="Chef Alice"
                      value={registerName}
                      onChange={e => setRegisterName(e.target.value)}
                      required
                      style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "8px", padding: "0.6rem 0.85rem", color: "#fff", fontSize: "0.88rem" }}
                    />
                  </div>

                  <div style={{ marginBottom: "1rem" }}>
                    <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, marginBottom: "0.35rem" }}>Email Address</label>
                    <input
                      type="email"
                      placeholder="alice@foodverse.ai"
                      value={registerEmail}
                      onChange={e => setRegisterEmail(e.target.value)}
                      required
                      style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "8px", padding: "0.6rem 0.85rem", color: "#fff", fontSize: "0.88rem" }}
                    />
                  </div>

                  <div style={{ marginBottom: "1rem" }}>
                    <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 700, marginBottom: "0.35rem" }}>Password</label>
                    <input
                      type="password"
                      placeholder="••••••••"
                      value={registerPassword}
                      onChange={e => setRegisterPassword(e.target.value)}
                      required
                      style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "8px", padding: "0.6rem 0.85rem", color: "#fff", fontSize: "0.88rem" }}
                    />
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1.4rem" }}>
                    <div>
                      <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 600, color: "var(--text-dim)", marginBottom: "0.3rem" }}>Diet</label>
                      <select
                        value={registerDiet}
                        onChange={e => setRegisterDiet(e.target.value)}
                        style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "6px", padding: "0.5rem", color: "#fff", fontSize: "0.82rem" }}
                      >
                        <option value="any">Omnivore</option>
                        <option value="vegetarian">Vegetarian</option>
                        <option value="vegan">Vegan</option>
                        <option value="non-vegetarian">High-Protein</option>
                      </select>
                    </div>

                    <div>
                      <label style={{ display: "block", fontSize: "0.78rem", fontWeight: 600, color: "var(--text-dim)", marginBottom: "0.3rem" }}>Goal</label>
                      <select
                        value={registerGoal}
                        onChange={e => setRegisterGoal(e.target.value)}
                        style={{ width: "100%", background: "#0B1120", border: "1px solid #334155", borderRadius: "6px", padding: "0.5rem", color: "#fff", fontSize: "0.82rem" }}
                      >
                        <option value="balanced">Balanced</option>
                        <option value="weight_loss">Fat Loss</option>
                        <option value="muscle_gain">Muscle Gain</option>
                      </select>
                    </div>
                  </div>

                  {authError && (
                    <div style={{ padding: "0.65rem 0.85rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid #EF4444", borderRadius: "8px", color: "#EF4444", fontSize: "0.82rem", marginBottom: "1.25rem" }}>
                      {authError}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={authLoading}
                    className="btn btn-primary"
                    style={{ width: "100%", padding: "0.7rem", fontSize: "0.95rem" }}
                  >
                    {authLoading ? "Creating Account..." : "Create Free Account"}
                  </button>
                </form>

                <div style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
                  Already have an account?{" "}
                  <span
                    onClick={() => setActiveTab("login")}
                    style={{ color: "var(--primary)", fontWeight: 700, cursor: "pointer", textDecoration: "underline" }}
                  >
                    Sign In here →
                  </span>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* ── Toast Notification Container ─────────────────────────────────── */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.type === "error" ? "toast-error" : ""}`}>
            <span>{toast.type === "error" ? "⚠️" : (toast.type === "info" ? "ℹ️" : "✓")}</span>
            <span>{toast.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Mount React Root
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
