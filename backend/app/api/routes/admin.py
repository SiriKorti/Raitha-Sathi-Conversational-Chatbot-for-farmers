"""
admin.py — System Administration & Status API

WHAT IT DOES:
Exposes internal system status endpoints for monitoring and managing
the RAG backend without restarting the server.

WHY IT EXISTS:
Allows checking the health of the FAISS index, loaded crops, and DB
entry counts — critical for debugging retrieval issues in production.

ENDPOINTS:
  GET  /api/admin/status        — Full system status snapshot
  GET  /api/admin/crops         — List of all loaded crop names
  GET  /api/admin/index-info    — FAISS index statistics
  POST /api/admin/reindex       — Trigger a live re-ingestion from DB
"""

import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.utils.logger import logger
from app.config import settings

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Status Snapshot ───────────────────────────────────────────────────────────

@router.get("/status")
async def system_status():
    """
    Full system health and status snapshot.

    Returns index size, DB entry count, loaded crops,
    active sessions, and service availability flags.
    """
    from app.main import retriever, session_manager, response_generator, stt, tts

    # ── FAISS Index info ──────────────────────────────────────────────────────
    index_loaded = False
    index_vectors = 0
    index_path = Path(settings.FAISS_INDEX_PATH)

    if retriever and retriever._loaded:
        index_loaded = True
        index_vectors = retriever.faiss_index.total_vectors

    # ── Database Searcher info ────────────────────────────────────────────────
    db_entries = 0
    db_crops: list[str] = []
    if response_generator and response_generator.db_searcher:
        db_entries = response_generator.db_searcher.get_entry_count()
        db_crops = response_generator.db_searcher.get_all_crops()

    # ── Session info ──────────────────────────────────────────────────────────
    active_sessions = 0
    if session_manager:
        active_sessions = session_manager.get_active_count()

    # ── Voice availability ────────────────────────────────────────────────────
    stt_available = False
    tts_available = False
    if stt:
        stt_available = await stt.is_available()
    if tts:
        tts_available = await tts.is_available()

    return {
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
        },
        "rag": {
            "index_loaded": index_loaded,
            "index_vectors": index_vectors,
            "index_path": str(index_path),
            "index_exists_on_disk": index_path.exists(),
        },
        "database": {
            "entry_count": db_entries,
            "crops_loaded": len(db_crops),
            "crops": db_crops,
            "database_path": settings.DATABASE_PATH,
        },
        "llm": {
            "gemini_model": settings.GEMINI_MODEL,
            "gemini_key_set": bool(settings.GEMINI_API_KEY),
        },
        "voice": {
            "stt_engine": "faster-whisper",
            "stt_model": settings.WHISPER_MODEL_SIZE,
            "stt_available": stt_available,
            "tts_engine": settings.TTS_ENGINE,
            "tts_available": tts_available,
        },
        "sessions": {
            "active": active_sessions,
            "timeout_minutes": settings.SESSION_TIMEOUT_MINUTES,
            "max_history_turns": settings.MAX_HISTORY_TURNS,
            "backend": settings.MEMORY_BACKEND,
        },
    }


# ── Crop List ─────────────────────────────────────────────────────────────────

@router.get("/crops")
async def list_crops():
    """
    Return all crop names currently loaded in the database searcher.

    Useful for verifying all 15 crop datasets were loaded correctly.
    """
    from app.main import response_generator

    if not response_generator or not response_generator.db_searcher:
        raise HTTPException(status_code=503, detail="Database searcher not initialised")

    crops = response_generator.db_searcher.get_all_crops()
    return {
        "crops": crops,
        "total": len(crops),
    }


# ── FAISS Index Info ──────────────────────────────────────────────────────────

@router.get("/index-info")
async def index_info():
    """
    Return FAISS index statistics and embedding model info.
    """
    from app.main import retriever

    if not retriever:
        raise HTTPException(status_code=503, detail="Retriever not initialised")

    index_path = Path(settings.FAISS_INDEX_PATH)
    meta_path = Path(settings.FAISS_METADATA_PATH)

    index_size_kb = round(index_path.stat().st_size / 1024, 1) if index_path.exists() else 0
    meta_size_kb = round(meta_path.stat().st_size / 1024, 1) if meta_path.exists() else 0

    return {
        "loaded": retriever._loaded,
        "total_vectors": retriever.faiss_index.total_vectors,
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_dimension": settings.EMBEDDING_DIMENSION,
        "top_k": settings.FAISS_TOP_K,
        "index_file": {
            "path": str(index_path),
            "exists": index_path.exists(),
            "size_kb": index_size_kb,
        },
        "metadata_file": {
            "path": str(meta_path),
            "exists": meta_path.exists(),
            "size_kb": meta_size_kb,
        },
    }


# ── Live Re-Index ─────────────────────────────────────────────────────────────

@router.post("/reindex")
async def trigger_reindex(background_tasks: BackgroundTasks):
    """
    Trigger a live re-ingestion of all database files and rebuild FAISS index.

    Runs in the background — the server stays responsive during indexing.
    Check /api/admin/status after a few minutes to verify completion.

    WARNING: During re-indexing, retrieval may temporarily use the old index.
    """
    logger.info("Live re-index triggered via admin API")

    def _run_ingest():
        """Run the ingestion script as a subprocess."""
        try:
            script = Path(__file__).parent.parent.parent.parent / "scripts" / "ingest_data.py"
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=300,  # 5-minute timeout
            )
            if result.returncode == 0:
                logger.info("Re-index completed successfully")
            else:
                logger.error("Re-index failed: {e}", e=result.stderr[:500])
        except subprocess.TimeoutExpired:
            logger.error("Re-index timed out after 300s")
        except Exception as e:
            logger.error("Re-index subprocess error: {e}", e=e)

    background_tasks.add_task(_run_ingest)

    return {
        "status": "started",
        "message": (
            "Re-indexing started in the background. "
            "Check /api/admin/status in a few minutes to verify the new vector count."
        ),
        "database_path": settings.DATABASE_PATH,
        "index_path": settings.FAISS_INDEX_PATH,
    }


# ── Reload Index into Memory ──────────────────────────────────────────────────

@router.post("/reload-index")
async def reload_index():
    """
    Reload the FAISS index from disk into the live retriever.

    Use this after a re-index completes to activate the new vectors
    without restarting the server.
    """
    from app.main import retriever

    if not retriever:
        raise HTTPException(status_code=503, detail="Retriever not initialised")

    index_path = Path(settings.FAISS_INDEX_PATH)
    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Index not found at {index_path}. Run /api/admin/reindex first."
        )

    try:
        retriever.load()
        logger.info("FAISS index reloaded via admin API | vectors={n}", n=retriever.faiss_index.total_vectors)
        return {
            "status": "success",
            "total_vectors": retriever.faiss_index.total_vectors,
            "message": "FAISS index reloaded successfully. New vectors are now active.",
        }
    except Exception as e:
        logger.error("Failed to reload index: {e}", e=e)
        raise HTTPException(status_code=500, detail=f"Reload failed: {str(e)}")
