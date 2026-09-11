"""
exceptions.py — Custom Exception Classes

WHAT IT DOES:
Defines a specific hierarchy of error types for the project (e.g., 
LLMTimeoutError, RetrievalError). This allows the code to catch 
and handle specific problems rather than crashing on generic errors.

WHY IT EXISTS:
Provides "Clean Architecture" and robust error reporting. By using 
custom exceptions, we can provide much more helpful error messages 
back to the farmer (e.g., "The AI is busy" instead of "Error 500").

CONNECTIONS:
- Imported by almost all modules to raise or catch specific errors.
"""


# ── Base Exception ────────────────────────────────────────────────────────────

class AgriAssistantError(Exception):
    """
    Base exception for all Kannada Agricultural RAG Assistant errors.
    All custom exceptions should inherit from this class.
    """
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# ── Dataset Errors ────────────────────────────────────────────────────────────

class DatasetLoadError(AgriAssistantError):
    """Raised when the agricultural dataset cannot be loaded from disk."""
    pass


class DatasetValidationError(AgriAssistantError):
    """Raised when a dataset entry fails JSON schema validation."""
    pass


# ── Embedding Errors ──────────────────────────────────────────────────────────

class EmbeddingError(AgriAssistantError):
    """Raised when the Sentence Transformer model fails to generate embeddings."""
    pass


class ModelLoadError(AgriAssistantError):
    """Raised when a model (embedding, LLM, TTS, STT) fails to load."""
    pass


# ── FAISS / Retrieval Errors ──────────────────────────────────────────────────

class FAISSIndexError(AgriAssistantError):
    """Raised when the FAISS index cannot be built, loaded, or searched."""
    pass


class RetrievalError(AgriAssistantError):
    """Raised when the semantic retrieval pipeline fails."""
    pass


# ── LLM Errors ───────────────────────────────────────────────────────────────

class LLMConnectionError(AgriAssistantError):
    """Raised when the Ollama or Gemini API cannot be reached."""
    pass


class LLMResponseError(AgriAssistantError):
    """Raised when the LLM returns an invalid or empty response."""
    pass


class LLMTimeoutError(AgriAssistantError):
    """Raised when the LLM takes too long to respond."""
    pass


# ── Conversation Errors ───────────────────────────────────────────────────────

class SessionNotFoundError(AgriAssistantError):
    """Raised when a session ID does not exist in the memory manager."""
    pass


class ConversationMemoryError(AgriAssistantError):
    """Raised when conversation memory operations fail."""
    pass


# ── Voice Pipeline Errors ─────────────────────────────────────────────────────

class STTError(AgriAssistantError):
    """Raised when speech-to-text transcription fails."""
    pass


class TTSError(AgriAssistantError):
    """Raised when text-to-speech synthesis fails."""
    pass


class AudioProcessingError(AgriAssistantError):
    """Raised when audio file processing fails (reading, converting, etc.)."""
    pass


# ── Configuration Errors ──────────────────────────────────────────────────────

class ConfigurationError(AgriAssistantError):
    """Raised when required configuration values are missing or invalid."""
    pass
