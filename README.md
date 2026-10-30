# 🥗 Food Verse AI — Parts 1, 2, 3 & 4 (Full-Stack Production Platform)

> **Food Verse AI**: An enterprise-grade multimodal food intelligence and culinary health web application. Food Verse AI unifies deep computer-vision food recognition and USDA nutrient analysis (Part 1), produce freshness inspection and restaurant kitchen sanitation monitoring (Part 2), an adaptive AI cooking assistant with 7-day personalized meal planning (Part 3), and production-grade full-stack architecture with user authentication, database persistence, Alembic migrations, actionable cross-module AI insights, and Docker containerization (Part 4).

---

## 🏛️ System Architecture

```
                                [ Modern React 18 SPA Client ]
                                               │
                                 (REST / Multipart / Bearer JWT)
                                               ▼
                              [ FastAPI Application Gateway ]
                ├── Request Logging & Performance Middleware
                ├── Global Exception Handling & CORS Configuration
                ├── Static SPA Serving (static/index.html & static/app.js)
                └── Modular API Routers:
                     ├── 🔐 /api/auth          (Register, Login, Me, Profile, Logout)
                     ├── 🥗 /api/food          (Recognize, Samples)
                     ├── 📊 /api/nutrition     (Analyze, Foods Catalog)
                     ├── 🍎 /api/freshness     (Analyze, Samples)
                     ├── 🛡️ /api/hygiene       (Analyze-Image, Analyze-Video, Reviews, Samples)
                     ├── 👨‍🍳 /api/cooking       (Chat, Sample Prompts, Recipes CRUD)
                     ├── 📅 /api/meal-plans    (Generate, List, Get, Save)
                     ├── 📋 /api/history       (Paginated Food, Freshness, Hygiene, Recipes, Plans)
                     └── 💡 /api/insights      (Aggregated Health & Safety Dashboard Insights)
                                               │
             ┌─────────────────────────────────┴─────────────────────────────────┐
             ▼                                                                   ▼
   [ AI & Data Services ]                                              [ Persistence Layer ]
   ├── Google Gemini 3.5 Multimodal REST Client                        ├── SQLAlchemy ORM Engine
   ├── USDA FoodData Central REST Client (300k+ foods)                 ├── SQLite (Local Development)
   ├── OpenCV Visual Indicators & Video Frame Sampler                  ├── PostgreSQL (Production Ready)
   ├── Actionable Unified Insights Engine                              ├── Alembic Database Migrations
   └── Direct Bcrypt Password Hashing & JWT Security                   └── Multi-User Isolation Enforcement
```

---

## ✨ Features by Module

### Part 1: Food Recognition & Nutrition Intelligence
- **Food Recognition**: Drag-and-drop or select images; classified by Google Gemini Multimodal Vision with model tier and confidence score.
- **USDA FoodData Central Integration**: Live search and retrieval of verified nutrient metrics (Calories, Protein, Carbohydrates, Total Fat, Saturated Fat, Fiber, Sugar, Sodium, Potassium, Calcium, Iron, Vitamin C).
- **Dynamic Serving Scaler**: Adjust serving quantity in grams or standard servings with instant proportional recalculation.
- **Nutri-Grade & Daily Values**: Percentage Daily Value (% DV) breakdown, Calorie distribution chart, and portion advice.

### Part 2: Produce Freshness & Kitchen Hygiene Intelligence
- **Produce Freshness Assessment**: Inspects apples, bananas, tomatoes, and leafy greens for surface browning, impact bruising, lesions, and shriveling.
- **Storage Guidance**: Provides optimal storage temperature, humidity, ethylene sensitivity, and shelf-life forecasts.
- **Appearance-Only Safety Disclaimer**: Explicit compliance disclaimer noting that surface computer vision cannot detect internal bacteria, toxins, or microbes.
- **Kitchen Sanitation Audit**: Analyzes restaurant prep station photos and video clips (≤30s) at 1 fps. Flags uncovered ingredients, surface clutter, food/waste proximity, and PPE compliance with a reviewer checklist.

### Part 3: Smart Cooking Assistant & Personalized Meal Planner
- **Interactive AI Chef Chat**: Suggests zero-waste recipes from available ingredients, handles substitutions, and answers culinary technique questions.
- **Recipe Management**: Saves favorite recipes to user's personal cookbook with custom chef notes.
- **Personalized 7-Day Meal Planner**: Generates multi-day plans tailored to dietary framework (Vegetarian, Vegan, Omnivore), fitness goals (Balanced, Fat Loss, Muscle Gain), and allergy exclusions.
- **Consolidated Grocery List**: Categorized shopping checklist with real-time check-off state.

### Part 4: Full-Stack Integration, Security & Deployment
- **Unified Responsive Dashboard**: Modern sidebar navigation covering all 8 functional views with persistent state.
- **Secure Authentication & RBAC**: Stateless JWT Bearer tokens, native bcrypt password hashing, and user profile management.
- **Relational Persistence (SQLAlchemy + Alembic)**: Database models for Users, Food Analyses, Freshness Reports, Hygiene Audits, Saved Recipes, Meal Plans, and Chat History.
- **Multi-User Data Isolation**: User records are strictly partitioned by authenticated user ID; users cannot access or delete other users' history.
- **Actionable AI Insights Service**: Cross-module intelligence engine synthesizing nutrition, freshness, hygiene, and user goals with transparent source attribution.
- **Containerization**: Production `Dockerfile` and `docker-compose.yml` for single-command deployment with PostgreSQL.

---

## 🚀 Quick Start Guide (Local Windows / PowerShell)

### Prerequisites
- Python 3.10+ (tested on Python 3.13)
- Git

### 1. Clone & Setup Directory
```powershell
git clone <repository_url> food-verse-ai
cd food-verse-ai
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` and fill in your keys (free tier):
```env
GEMINI_API_KEY=your_gemini_api_key_here
USDA_API_KEY=your_usda_api_key_here
SECRET_KEY=generate_with_python_secrets_token_hex_32
DATABASE_URL=
```
*(Leave `DATABASE_URL` empty for local SQLite development)*

### 5. Run Database Migrations
```powershell
alembic upgrade head
```

### 6. Launch the Application
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser at **[http://localhost:8000](http://localhost:8000)**.
Interactive OpenAPI docs are available at **[http://localhost:8000/docs](http://localhost:8000/docs)**.

---

## 🐳 Docker Deployment

To launch the full stack with PostgreSQL using Docker Compose:

```bash
# 1. Provide your environment keys
export GEMINI_API_KEY="your_gemini_api_key"
export USDA_API_KEY="your_usda_api_key"

# 2. Build and launch containers
docker compose up -d --build

# 3. Check logs
docker compose logs -f
```

The application will be live at `http://localhost:8000`.

---

## 🧪 Comprehensive Test Suite

Food Verse AI includes **54 automated unit and integration tests** verifying all endpoints and the 7 core user journeys:

```powershell
# Run the complete test suite
python -m pytest backend/tests -v
```

### User Journeys Tested:
1. **Journey 1**: User registration, login, JWT validation, and profile customization.
2. **Journey 2**: Food image recognition -> USDA nutrition lookup -> health score calculation.
3. **Journey 3**: Produce freshness evaluation -> storage recommendations -> history review.
4. **Journey 4**: Commercial kitchen hygiene audit -> report generation -> checklist auditor review.
5. **Journey 5**: Ingredient-based recipe generation -> interactive chef chat -> recipe saving.
6. **Journey 6**: Personalized 7-day meal plan synthesis -> grocery list compilation -> meal plan saving.
7. **Journey 7**: Multi-user isolation verification (confirms User A cannot access or delete User B's records).

---

## 🛡️ Security & Privacy Guarantees

- **No Plaintext Passwords**: Passwords hashed with native `bcrypt` using cryptographic salt rounds.
- **JWT Protection**: Stateless HS256 JWT tokens with configurable expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- **File Validation**: Strict MIME type validation, file size limits (10MB for photos, 25MB for videos), and duration limits (≤30 seconds). Temporary video frames are securely unlinked upon processing.
- **Attribution Transparency**: Every AI output explicitly displays its source (`USDA Verified Database`, `BioFresh-Net Model Prediction`, or `Gemini 3.5 Generative Synthesis`).
- **Secrets Protection**: `.env` is ignored by Git; `.env.example` contains only template placeholders.
