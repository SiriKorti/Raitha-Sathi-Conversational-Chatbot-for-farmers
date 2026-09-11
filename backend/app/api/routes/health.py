"""
health.py — Health Check API Route

WHAT IT DOES:
Provides a diagnostic endpoint that reports the status of all system 
components (FAISS, Ollama, Whisper, TTS, etc.).

WHY IT EXISTS:
Critical for maintaining system reliability. It allows developers to 
quickly see if a model failed to load or if a local service like Ollama 
is unreachable without checking server logs.

CONNECTIONS:
- Imports 'app.main' to check the status of live singletons.
- Imports 'app.config' to verify configuration values.
"""

from fastapi import APIRouter
from app.config import settings

router = APIRouter()


@router.get("/health", tags=["System"])
async def health_check():
    """
    System health check endpoint.

    Checks all major components and returns their status.
    Returns HTTP 200 even if some components are degraded,
    so load balancers don't stop routing traffic unexpectedly.
    """
    from app.main import retriever, session_manager, stt, tts

    components = {}

    # ── FAISS Index Status ────────────────────────────────────────────────────
    try:
        components["faiss_index"] = {
            "status": "ok" if retriever.faiss_index.is_loaded() else "not_loaded",
            "vectors": retriever.faiss_index.total_vectors,
        }
    except Exception as e:
        components["faiss_index"] = {"status": "error", "detail": str(e)}

    # ── Gemini Fallback Status ────────────────────────────────────────────────
    if settings.GEMINI_API_KEY:
        components["gemini"] = {"status": "ok", "detail": "Configured"}
    else:
        components["gemini"] = {"status": "warning", "detail": "API Key missing"}

    # ── STT Status ────────────────────────────────────────────────────────────
    try:
        stt_available = await stt.is_available()
        components["whisper_stt"] = {
            "status": "ok" if stt_available else "unavailable",
            "model_size": settings.WHISPER_MODEL_SIZE,
        }
    except Exception as e:
        components["whisper_stt"] = {"status": "error", "detail": str(e)}

    # ── TTS Status ────────────────────────────────────────────────────────────
    try:
        tts_available = await tts.is_available()
        components["tts"] = {
            "status": "ok" if tts_available else "unavailable",
            "engine": settings.TTS_ENGINE,
        }
    except Exception as e:
        components["tts"] = {"status": "error", "detail": str(e)}

    # ── Active Sessions ───────────────────────────────────────────────────────
    try:
        active_sessions = session_manager.get_active_count()
    except Exception:
        active_sessions = -1

    # Overall system status
    critical_ok = (
        components.get("gemini", {}).get("status") == "ok"
    )
    overall_status = "healthy" if critical_ok else "degraded"

    return {
        "status": overall_status,
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "components": components,
        "active_sessions": active_sessions,
    }
