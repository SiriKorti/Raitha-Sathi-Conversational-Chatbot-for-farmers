"""
session_manager.py — Session Lifecycle Manager

WHAT IT DOES:
Provides a high-level interface for managing user sessions. It handles 
the creation of unique session IDs, recording user/assistant messages, 
and coordinating the update of the dialogue state.

WHY IT EXISTS:
It abstracts the complexity of 'MemoryManager' and 'DialogueState' into 
a simple set of actions. This makes the API and WebSocket handlers 
cleaner and more readable.

CONNECTIONS:
- Initialized in 'app.main' as a shared singleton.
- Orchestrates 'MemoryManager' and 'DialogueState'.
- Called by 'api/routes' and 'websocket/ws_handler'.
"""

import time
import uuid
from typing import Optional, Dict, Any, List
from app.conversation.memory_manager import MemoryManager
from app.conversation.dialogue_state import DialogueState
from app.conversation.farm_diary import FarmDiary
from app.services.conversation_manager import ConversationManager
from app.utils.logger import logger


class SessionManager:
    """
    High-level session management for the agricultural assistant.
    Wraps MemoryManager (for active fast cache) and ConversationManager
    (for durable database/conversations.json persistence).

    Designed to be used as a singleton shared across requests.
    """

    def __init__(self):
        self.memory = MemoryManager()
        self.diary = FarmDiary()
        self.conversation_manager = ConversationManager()
        logger.info("SessionManager initialised with persistent backend")

    # ── Session Operations ────────────────────────────────────────────────────

    def new_session(self, user_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """
        Create a brand-new session and return its ID.
        If user_id is provided, persists it immediately to database/conversations.json.
        """
        session_id = str(uuid.uuid4())
        self.memory.create_session(session_id)

        if user_id:
            self.conversation_manager.create_conversation(
                user_id=user_id,
                title=title or "ಹೊಸ ಸಂಭಾಷಣೆ / New Conversation",
                initial_state=DialogueState().to_dict(),
                conversation_id=session_id,
            )

        logger.info("Session created: {id} | user={uid}", id=session_id, uid=user_id)
        return session_id

    def ensure_session_loaded(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """
        Ensures a session's history and dialogue state are loaded into active memory.
        If not present in RAM, restores seamlessly from database/conversations.json.
        """
        if session_id in self.memory._sessions and not self.memory._is_expired(self.memory._sessions[session_id]):
            return True

        # Attempt to restore from persistent storage
        target_uid = user_id or self.conversation_manager.find_owner_of_conversation(session_id)
        if not target_uid:
            return False

        conv = self.conversation_manager.get_conversation(target_uid, session_id)
        if not conv:
            return False

        # Hydrate active session memory
        state_dict = conv.get("state") or DialogueState().to_dict()
        messages = conv.get("messages", [])

        # Reformat stored messages to memory manager turn structure
        history_turns = []
        for m in messages:
            history_turns.append({
                "role": "farmer" if m.get("role") in ("farmer", "user") else "assistant",
                "content": m.get("content", ""),
                "timestamp": m.get("timestamp", time.time())
            })

        self.memory._sessions[session_id] = {
            "history": history_turns,
            "state": state_dict,
            "created_at": conv.get("created_at", time.time()),
            "last_active": time.time(),
        }
        logger.info("Restored session {id} from disk into memory for user {uid}", id=session_id, uid=target_uid)
        return True

    def session_exists(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """Check if a session exists in memory or persistent storage."""
        if self.memory.session_exists(session_id):
            return True
        return self.ensure_session_loaded(session_id, user_id)

    def close_session(self, session_id: str, user_id: Optional[str] = None):
        """End a session and free its memory. If user_id given, permanently deletes it."""
        self.memory.delete_session(session_id)
        if user_id:
            self.conversation_manager.delete_conversation(user_id, session_id)
        logger.info("Session closed: {id}", id=session_id)

    # ── Conversation Turn Management ──────────────────────────────────────────

    def add_user_turn(self, session_id: str, text: str, user_id: Optional[str] = None):
        """
        Record a farmer's message and update the dialogue state both in RAM
        and in database/conversations.json.
        """
        self.ensure_session_loaded(session_id, user_id)
        self.memory.add_turn(session_id, role="farmer", content=text)

        # Update dialogue state
        state = self.memory.get_state(session_id)
        state.update_from_text(text)
        self.memory.update_state(session_id, state)

        # Persist to disk
        owner_id = user_id or self.conversation_manager.find_owner_of_conversation(session_id)
        if owner_id:
            self.conversation_manager.add_message(
                user_id=owner_id,
                conversation_id=session_id,
                role="farmer",
                content=text,
                auto_title=True
            )
            self.conversation_manager.update_dialogue_state(
                user_id=owner_id,
                conversation_id=session_id,
                state=state.to_dict()
            )

    def add_assistant_turn(self, session_id: str, text: str, user_id: Optional[str] = None, metadata: Optional[dict] = None):
        """
        Record the assistant's response in active memory and database/conversations.json.
        """
        self.memory.add_turn(session_id, role="assistant", content=text)

        owner_id = user_id or self.conversation_manager.find_owner_of_conversation(session_id)
        if owner_id:
            self.conversation_manager.add_message(
                user_id=owner_id,
                conversation_id=session_id,
                role="assistant",
                content=text,
                metadata=metadata or {}
            )

    # ── State Access ──────────────────────────────────────────────────────────

    def get_state(self, session_id: str, user_id: Optional[str] = None) -> DialogueState:
        """Return the current dialogue state for a session."""
        self.ensure_session_loaded(session_id, user_id)
        return self.memory.get_state(session_id)

    def update_state_from_llm(self, session_id: str, extracted: dict, user_id: Optional[str] = None):
        """
        Update the dialogue state with entities extracted by the LLM.
        """
        self.ensure_session_loaded(session_id, user_id)
        state = self.memory.get_state(session_id)
        state.update_from_llm(extracted)
        self.memory.update_state(session_id, state)

        owner_id = user_id or self.conversation_manager.find_owner_of_conversation(session_id)
        if owner_id:
            self.conversation_manager.update_dialogue_state(
                user_id=owner_id,
                conversation_id=session_id,
                state=state.to_dict()
            )

    # ── History Access ────────────────────────────────────────────────────────

    def get_recent_history(self, session_id: str, n: int = 5, user_id: Optional[str] = None) -> list[dict]:
        """Get the n most recent conversation turns."""
        self.ensure_session_loaded(session_id, user_id)
        return self.memory.get_recent_history(session_id, n_turns=n)

    def get_full_history(self, session_id: str, user_id: Optional[str] = None) -> list[dict]:
        """Get the complete conversation history."""
        self.ensure_session_loaded(session_id, user_id)
        return self.memory.get_history(session_id)

    # ── Diagnostics ───────────────────────────────────────────────────────────

    def get_active_count(self) -> int:
        """Return the number of currently active sessions."""
        return self.memory.get_active_session_count()

