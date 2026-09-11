"""
logger.py — Centralized Logging Configuration

WHAT IT DOES:
Configures a structured logging system using the Loguru library. It 
simultaneously writes logs to the terminal (in color) and to a rotating 
file in the 'logs/' directory, ensuring all Kannada text is saved correctly.

WHY IT EXISTS:
Essential for transparency and debugging. In a complex RAG system, 
you need to see the "flow" of data—what was transcribed, what was 
retrieved, and what the AI said—to fix issues quickly.

CONNECTIONS:
- Imported and used by **every** module in the project to record 
  activity and errors.
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_level: str = "INFO", log_file: str = "logs/app.log"):
    """
    Configure the Loguru logger with both console and file output.

    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR)
        log_file:  Path to the rotating log file
    """
    # Remove the default Loguru handler
    logger.remove()

    # ── Console Handler (colorized, human-readable) ───────────────────────────
    # Use UTF-8 encoding explicitly so Kannada text displays correctly
    # on Windows terminals that default to CP1252
    import io
    raw_stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding='utf-8', errors='replace'
    ) if hasattr(sys.stdout, 'buffer') else sys.stdout

    class NonClosingStream:
        def __init__(self, stream):
            self._stream = stream
        def write(self, data):
            try:
                self._stream.write(data)
            except Exception:
                pass
        def flush(self):
            try:
                self._stream.flush()
            except Exception:
                pass
        def close(self):
            # No-op to prevent Loguru from closing sys.stdout when handlers are removed
            pass

    utf8_stdout = NonClosingStream(raw_stdout)

    logger.add(
        utf8_stdout,
        level=log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # ── File Handler (rotating, persistent) ──────────────────────────────────
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_path,
        level=log_level,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        rotation="10 MB",    # Create new file when log reaches 10 MB
        retention="7 days",  # Keep logs for 7 days
        compression="zip",   # Compress rotated logs
        encoding="utf-8",    # Important for Kannada text in logs
    )

    logger.info(
        "Logger initialized | level={level} | file={file}",
        level=log_level,
        file=str(log_path),
    )


# ── Initialize on import ──────────────────────────────────────────────────────
# Settings are imported here to avoid circular imports at the module level
try:
    from app.config import settings
    setup_logger(log_level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)
except Exception:
    # Fallback: if config not yet available, use defaults
    setup_logger()

# Re-export logger so other modules can simply do:
# from app.utils.logger import logger
__all__ = ["logger"]
