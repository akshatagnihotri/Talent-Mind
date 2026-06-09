"""
TalentMind AI — FastAPI Application Entry Point
================================================
Wires together all routers, middleware, static file serving, CORS,
and startup / shutdown lifecycle events.

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import settings
from models.database import Base, engine
from routers import analysis, analytics, auth, jobs, ranking, recruiter, resumes

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("talentmind")
console = Console()


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup:
      1. Create all database tables (idempotent via CREATE TABLE IF NOT EXISTS).
      2. Ensure the upload directory exists.
      3. Print a rich startup banner.

    Shutdown:
      - Log graceful shutdown message.
    """
    # ── DB tables ──────────────────────────────────────────────────────────────
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created / verified.")
    except Exception as exc:
        logger.error("Failed to initialise database: %s", exc)
        logger.warning(
            "Continuing without database — ensure PostgreSQL is running and "
            "DATABASE_URL is set correctly."
        )

    # ── Upload directory ───────────────────────────────────────────────────────
    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    logger.info("Upload directory ready: %s", upload_path.resolve())

    # ── Startup banner (only in dev / when stdout is a terminal) ──────────────
    _print_startup_banner()

    yield  # ← application runs here

    # ── Shutdown ───────────────────────────────────────────────────────────────
    logger.info("TalentMind AI shutting down gracefully.")


def _print_startup_banner() -> None:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row("[bold cyan]API Base[/bold cyan]", "http://0.0.0.0:8000")
    table.add_row("[bold cyan]Docs[/bold cyan]", "http://0.0.0.0:8000/docs")
    table.add_row("[bold cyan]ReDoc[/bold cyan]", "http://0.0.0.0:8000/redoc")
    table.add_row("[bold cyan]Demo Mode[/bold cyan]", str(settings.DEMO_MODE))
    table.add_row("[bold cyan]Ollama Model[/bold cyan]", settings.OLLAMA_MODEL)
    table.add_row("[bold cyan]DB URL[/bold cyan]", settings.DATABASE_URL[:60] + "…")
    console.print(
        Panel(table, title="[bold green]TalentMind AI — Backend Starting[/bold green]", border_style="green")
    )


# ── Application factory ───────────────────────────────────────────────────────
app = FastAPI(
    title="TalentMind AI",
    description=(
        "Production-grade HR-Tech SaaS backend for AI-powered resume analysis, "
        "candidate ranking, and recruiter insights."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)


# ── Request timing middleware ──────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Attach X-Process-Time header to every response for performance monitoring."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time"] = f"{elapsed}ms"
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "path": str(request.url),
        },
    )


# ── Static file serving ───────────────────────────────────────────────────────
# Serve uploaded files (resumes) at /uploads/*
_uploads_path = Path(settings.UPLOAD_DIR)
_uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads_path)), name="uploads")


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(analysis.router)
app.include_router(jobs.router)
app.include_router(ranking.router)
app.include_router(recruiter.router)
app.include_router(analytics.router)


# ── Health & Info endpoints ───────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="Health check")
async def health_check():
    """
    Liveness probe endpoint.
    Returns HTTP 200 with basic service info.
    Used by load balancers, Docker HEALTHCHECK, and Kubernetes probes.
    """
    return {
        "status": "healthy",
        "service": "TalentMind AI Backend",
        "version": "1.0.0",
        "demo_mode": settings.DEMO_MODE,
        "ollama_model": settings.OLLAMA_MODEL,
    }


@app.get("/", tags=["System"], summary="API root")
async def root():
    """Root endpoint — redirects clients to the interactive docs."""
    return {
        "message": "Welcome to TalentMind AI API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


@app.get("/api/info", tags=["System"], summary="API configuration info")
async def api_info():
    """Return non-sensitive configuration metadata for the frontend."""
    return {
        "name": "TalentMind AI",
        "version": "1.0.0",
        "demo_mode": settings.DEMO_MODE,
        "ollama_model": settings.OLLAMA_MODEL,
        "features": [
            "resume_upload",
            "ats_scoring",
            "skill_gap_analysis",
            "candidate_ranking",
            "recruiter_notes",
            "interview_questions",
            "analytics_dashboard",
        ],
        "supported_formats": ["PDF", "DOCX", "DOC"],
        "max_upload_mb": 10,
    }
