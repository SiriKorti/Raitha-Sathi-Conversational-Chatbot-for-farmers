"""
memory_manager.py — Conversation Memory Manager

WHAT IT DOES:
Manages the low-level storage of conversation history and dialogue state 
for every user session. It handles adding new turns, retrieving recent 
history, and automatically expiring old sessions to save memory.

WHY IT EXISTS:
LLMs are "stateless"—they forget everything as soon as a request ends. 
This file provides the "short-term memory" required for a natural, 
multi-turn conversation where the farmer can ask follow-up questions.

CONNECTIONS:
- Owned by 'SessionManager'.
- Used by 'response_generator.py' to fetch the history needed for prompts.
- Uses 'DialogueState' to store structured information about the problem.
"""

import time
from app.config import settings
from app.conversation.dialogue_state import DialogueState
from app.utils.logger import logger


class MemoryManager:
    """
    In-memory conversation memory manager.

    Stores conversation history and dialogue state per session.
    Sessions automatically expire after settings.SESSION_TIMEOUT_MINUTES.

    Structure:
        _sessions = {
            "session_id": {
                "history":    [{"role": "farmer", "content": "..."}, ...],
                "state":      DialogueState dict,
                "created_at": timestamp,
                "last_active": timestamp,
            }
        }
    """

    def __init__(self):
        # In-memory store: session_id → session data
        self._sessions: dict[str, dict] = {}
        self._timeout_seconds = settings.SESSION_TIMEOUT_MINUTES * 60
        self._max_history = settings.MAX_HISTORY_TURNS
        logger.info(
            "MemoryManager initialised | backend=in_memory | timeout={t}min",
            t=settings.SESSION_TIMEOUT_MINUTES
        )

    # ── Session Lifecycle ─────────────────────────────────────────────────────

    def create_session(self, session_id: str) -> dict:
        """
        Create a new conversation session.

        Args:
            session_id: Unique session identifier (UUID)

        Returns:
            New empty session dict
        """
        now = time.time()
        session = {
            "history": [],
            "state": DialogueState().to_dict(),
            "created_at": now,
            "last_active": now,
        }
        self._sessions[session_id] = session
        logger.info("New session created: {id}", id=session_id)
        return session

    def get_or_create_session(self, session_id: str) -> dict:
        """
        Return an existing session or create a new one.

        Also purges expired sessions on each call (lightweight cleanup).

        Args:
            session_id: Session identifier

        Returns:
            Session dict
        """
        self._purge_expired()

        if session_id not in self._sessions:
            return self.create_session(session_id)

        # Update last active timestamp
        self._sessions[session_id]["last_active"] = time.time()
        return self._sessions[session_id]

    def delete_session(self, session_id: str):
        """Remove a session and all its history."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("Session deleted: {id}", id=session_id)

    def session_exists(self, session_id: str) -> bool:
        """Check if a session exists and is still active."""
        if session_id not in self._sessions:
            return False
        session = self._sessions[session_id]
        return not self._is_expired(session)

    # ── Conversation History ──────────────────────────────────────────────────

    def add_turn(self, session_id: str, role: str, content: str):
        """
        Add a conversation turn to the session history.

        Args:
            session_id: Session identifier
            role:       "farmer" or "assistant"
            content:    Text content of the turn
        """
        session = self.get_or_create_session(session_id)

        turn = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
        }
        session["history"].append(turn)

        # Trim history if it exceeds max allowed turns
        # We keep pairs (farmer + assistant = 1 turn), so multiply by 2
        max_messages = self._max_history * 2
        if len(session["history"]) > max_messages:
            # Drop oldest messages but always keep the first exchange for context
            session["history"] = session["history"][-max_messages:]

        logger.debug(
            "Turn added | session={id} | role={role} | len={n}",
            id=session_id, role=role, n=len(session["history"])
        )

    def get_history(self, session_id: str) -> list[dict]:
        """
        Get the full conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of turn dicts: [{"role": ..., "content": ..., "timestamp": ...}]
        """
        if not self.session_exists(session_id):
            return []

        return self._sessions[session_id]["history"]

    def get_recent_history(self, session_id: str, n_turns: int = 5) -> list[dict]:
        """
        Get the most recent n_turns turns from the conversation.

        Args:
            session_id: Session identifier
            n_turns:    Number of recent turns to return

        Returns:
            List of the most recent turn dicts
        """
        history = self.get_history(session_id)
        return history[-(n_turns * 2):]  # n_turns pairs = n_turns * 2 messages

    # ── Dialogue State ────────────────────────────────────────────────────────

    def get_state(self, session_id: str) -> DialogueState:
        """
        Get the current dialogue state for a session.

        Args:
            session_id: Session identifier

        Returns:
            DialogueState object for the session
        """
        session = self.get_or_create_session(session_id)
        return DialogueState.from_dict(session["state"])

    def update_state(self, session_id: str, state: DialogueState):
        """
        Save an updated dialogue state for a session.

        Args:
            session_id: Session identifier
            state:      Updated DialogueState object
        """
        session = self.get_or_create_session(session_id)
        session["state"] = state.to_dict()

    # ── Private Helpers ───────────────────────────────────────────────────────

    def _is_expired(self, session: dict) -> bool:
        """Check if a session has exceeded its timeout."""
        return (time.time() - session["last_active"]) > self._timeout_seconds

    def _purge_expired(self):
        """Remove all expired sessions to free memory."""
        expired = [
            sid for sid, session in self._sessions.items()
            if self._is_expired(session)
        ]
        for sid in expired:
            del self._sessions[sid]
            logger.debug("Expired session purged: {id}", id=sid)

    def get_active_session_count(self) -> int:
        """Return number of currently active sessions."""
        self._purge_expired()
        return len(self._sessions)
