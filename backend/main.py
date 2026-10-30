import os
import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings, PROJECT_ROOT
from backend.database import create_all_tables
from backend.routers import (
    health,
    food,
    nutrition,
    freshness,
    hygiene,
    cooking,
    meal_planner,
    auth as auth_router,
    history as history_router,
    insights as insights_router,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("food_verse_ai")


# ── Lifespan handler (FastAPI modern startup/shutdown) ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Food Verse AI %s starting — initialising database…", settings.APP_VERSION)
    create_all_tables()
    logger.info("Database tables initialized successfully.")
    yield
    logger.info("Food Verse AI backend shutting down.")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Food Verse AI — Full-Stack Multimodal Food Intelligence Platform "
        "(Parts 1–4): Nutrition, Freshness, Hygiene, Cooking Assistant, "
        "Meal Planner, Authentication, History & Unified Actionable Insights."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %d (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": str(exc)},
    )


# ── Routers — Parts 1, 2, 3 ──────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(food.router)
app.include_router(nutrition.router)
app.include_router(freshness.router)
app.include_router(hygiene.router)
app.include_router(cooking.router)
app.include_router(meal_planner.router)

# ── Routers — Part 4 ──────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(history_router.router)
app.include_router(insights_router.router)


# ── Static SPA ────────────────────────────────────────────────────────────────
static_dir = PROJECT_ROOT / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
def serve_root():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Food Verse AI API is running. Visit /docs for documentation."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
