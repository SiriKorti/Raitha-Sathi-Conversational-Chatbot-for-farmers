"""
main.py — FastAPI Application Entry Point

WHAT IT DOES:
The root of the application. It initializes the FastAPI app instance, 
sets up shared singletons (STT, TTS, Retriever, etc.), and registers 
all REST and WebSocket routers.

WHY IT EXISTS:
It acts as the "glue" for the entire project. By centralizing model 
initialization in a lifespan context, it ensures heavy models are loaded 
once and shared across all incoming requests.

CONNECTIONS:
- Imports 'app.config' for global settings.
- Imports all 'app.api.routes' to register HTTP endpoints.
- Imports 'app.api.websocket' for real-time interaction.
- Provides 'stt', 'tts', 'retriever', and 'session_manager' as global instances.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import os

from app.config import settings
from app.utils.logger import logger

# ── Shared Singletons (accessible across all modules via import) ───────────────
# These are created at startup and reused across all requests.
# Avoids reloading models on every request.

retriever = None          # SemanticRetriever (FAISS + Embedder)
session_manager = None    # SessionManager (conversation memory)
response_generator = None # ResponseGenerator (full RAG pipeline)
stt = None                # Speech-to-text (not configured)
tts = None                # Text-to-speech (not configured)


# ── Application Lifecycle ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Code before 'yield' runs at startup.
    Code after 'yield' runs at shutdown.

    This replaces the deprecated @app.on_event("startup") pattern.
    """
    # ── STARTUP ───────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("Starting {name} v{ver}", name=settings.APP_NAME, ver=settings.APP_VERSION)
    logger.info("=" * 60)

    global retriever, session_manager, response_generator

    # 1. Initialise Session Manager (lightweight, no I/O)
    from app.conversation.session_manager import SessionManager
    session_manager = SessionManager()
    logger.info("✓ Session manager ready")

    # 2. Initialise Retriever and load FAISS index
    from app.rag.retriever import Retriever
    retriever = Retriever()
    try:
        retriever.load()
        logger.info(
            "✓ FAISS index loaded | {n} vectors",
            n=retriever.faiss_index.total_vectors
        )
    except Exception as e:
        # Non-fatal: app can still run without index (returns no-context responses)
        logger.warning(
            "⚠ FAISS index not loaded: {e}. "
            "Run scripts/ingest_data.py to build the index.",
            e=e
        )

    # 3. Initialise Response Generator
    from app.llm.response_generator import ResponseGenerator
    response_generator = ResponseGenerator(retriever, session_manager)
    logger.info("✓ Response generator ready")



    logger.info("=" * 60)
    logger.info("Server running at http://{h}:{p}", h=settings.HOST, p=settings.PORT)
    logger.info("API docs at http://{h}:{p}/docs", h=settings.HOST, p=settings.PORT)
    logger.info("=" * 60)

    yield  # ← Application runs here

    # ── SHUTDOWN ──────────────────────────────────────────────────────────────
    logger.info("Shutting down {name}...", name=settings.APP_NAME)
    # Clean up if needed (e.g., close DB connections)
    logger.info("Shutdown complete.")


# ── FastAPI App Instance ───────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered Kannada Agricultural Conversational RAG Assistant. "
        "Provides real-time multilingual agricultural guidance to farmers "
        "through voice and text interaction."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS Middleware ────────────────────────────────────────────────────────────
# Allow all origins in development. Restrict in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # In production: specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Disable caching for development
@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ── Register Routers ──────────────────────────────────────────────────────────

from app.api.routes.health import router as health_router
from app.api.routes.chat import router as chat_router
from app.api.routes.voice import router as voice_router
from app.api.routes.admin import router as admin_router
from app.api.routes.farm import router as farm_router
from app.api.routes.diagnosis import router as diagnosis_router
from app.api.routes.auth import router as auth_router
from app.api.websocket.ws_handler import router as ws_router

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat_router)
app.include_router(voice_router, prefix="/api/voice")
app.include_router(admin_router)
app.include_router(farm_router, prefix="/api/farm", tags=["Farm Profile"])
app.include_router(diagnosis_router, prefix="/api/vision", tags=["Visual Diagnosis"])

# WebSocket routes
app.include_router(ws_router)


# Mount static files (will be used later for React build if needed)
# app.mount("/", StaticFiles(directory="frontend-react/dist", html=True), name="frontend")

