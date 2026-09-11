"""
config.py — Central Configuration Module

WHAT IT DOES:
Manages application-wide settings using Pydantic's BaseSettings. It loads 
environment variables from a .env file and provides typed access to 
API keys, model names, and system paths.

WHY IT EXISTS:
Ensures a single source of truth for configuration. This prevents hardcoding 
values and allows the application to be easily ported between local 
development and production environments.

CONNECTIONS:
- Imported by almost every module in 'app/' to access 'settings'.
- Reads from the project's root '.env' file.
"""

from pydantic_settings import BaseSettings
from typing import Literal
from pathlib import Path


class Settings(BaseSettings):
    """
    Application-wide settings loaded from environment variables or .env file.
    Every field has a default value so the app runs even without a .env file.
    """

    # ── App Meta ─────────────────────────────────────────────────────────────
    APP_NAME: str = "Kannada Agricultural RAG Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── LLM Settings ─────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-flash-lite-latest"

    # ── Embedding Model ───────────────────────────────────────────────────────
    # paraphrase-multilingual-MiniLM-L12-v2 supports 50+ languages including Kannada
    EMBEDDING_MODEL: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    EMBEDDING_DIMENSION: int = 384  # Dimension of the above model's output

    # ── FAISS Vector Index ────────────────────────────────────────────────────
    FAISS_INDEX_PATH: str = "models/faiss_index/agricultural.index"
    FAISS_METADATA_PATH: str = "models/faiss_index/metadata.json"
    FAISS_TOP_K: int = 10  # Number of similar documents to retrieve

    # ── Dataset ───────────────────────────────────────────────────────────────
    DATASET_PATH: str = "data/raw"
    PROCESSED_DATA_PATH: str = "data/processed"
    SAMPLE_DATASET_PATH: str = "data/sample_dataset.json"
    DATABASE_PATH: str = "database"

    # ── Conversation Memory ───────────────────────────────────────────────────
    # "in_memory" = Python dict (great for development, no extra setup)
    # "redis"     = Redis-backed (for production persistence)
    MEMORY_BACKEND: Literal["in_memory", "redis"] = "in_memory"
    REDIS_URL: str = "redis://localhost:6379"
    SESSION_TIMEOUT_MINUTES: int = 30  # Auto-expire idle sessions
    MAX_HISTORY_TURNS: int = 10        # Max Q&A pairs kept in memory

    # ── Voice Pipeline ────────────────────────────────────────────────────────
    # Whisper model size: tiny/base/small/medium/large-v3
    # "small" gives a good balance of speed + accuracy for Kannada
    WHISPER_MODEL_SIZE: str = "small"
    WHISPER_LANGUAGE: str = "kn"  # ISO 639-1 code for Kannada
    WHISPER_DEVICE: str = "cpu"   # "cuda" if GPU available

    TTS_ENGINE: Literal["coqui", "piper", "gtts"] = "gtts"
    COQUI_MODEL: str = "tts_models/kn/cv/vits"
    PIPER_MODEL_PATH: str = "models/piper/kn_IN-female.onnx"
    AUDIO_SAMPLE_RATE: int = 16000

    # ── Fine-Tuning ───────────────────────────────────────────────────────────
    FINE_TUNED_MODEL_PATH: str = "models/fine_tuned/agri_embedder"
    TRAINING_EPOCHS: int = 3
    TRAINING_BATCH_SIZE: int = 16

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # ── Mandi Price API (data.gov.in) ─────────────────────────────────────────
    # Register at https://data.gov.in to obtain a free API key.
    # Resource: "Current Daily Price of Various Commodities from Various Markets"
    MANDI_API_KEY: str = ""
    MANDI_RESOURCE_ID: str = "9ef84268-d588-465a-a308-a864a43d0070"
    MANDI_API_TIMEOUT: int = 15  # seconds before aborting the request


    # ── Optional Database Settings ────────────────────────────────────────────
    MONGODB_URI: str = ""
    POSTGRES_URI: str = ""

    class Config:
        # Reads from a .env file in the project root
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore unknown env vars instead of crashing

    def get_faiss_index_dir(self) -> Path:
        """Return the directory containing the FAISS index files."""
        return Path(self.FAISS_INDEX_PATH).parent

    def get_dataset_dir(self) -> Path:
        """Return the raw dataset directory as a Path object."""
        return Path(self.DATASET_PATH)

    def get_fine_tuned_model_dir(self) -> Path:
        """Return the fine-tuned model directory as a Path object."""
        return Path(self.FINE_TUNED_MODEL_PATH)


# ── Singleton Instance ────────────────────────────────────────────────────────
# Import this in all other modules:  from app.config import settings
settings = Settings()
