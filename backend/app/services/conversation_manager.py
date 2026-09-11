"""
conversation_manager.py — Persistent User-Specific Chat Conversation Engine

WHAT IT DOES:
Manages persistent conversation threads and messages for authenticated farmers
in database/conversations.json. Provides strict user-level data isolation,
ownership validation, chronological message ordering, deterministic title generation,
and safe cascading deletion.

WHY IT EXISTS:
Ensures farmers' conversations survive logouts, server restarts, and multi-device access,
providing an authenticated ChatGPT-style personal advisory environment.
"""

import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.utils.logger import logger


class ConversationManager:
    """
    Manages user-isolated persistent conversation threads and message histories.
    Storage format in database/conversations.json:
    {
      "farmer_user_id": {
        "conv_uuid": {
          "id": "conv_uuid",
          "user_id": "farmer_user_id",
          "title": "ಮೆಕ್ಕೆಜೋಳದ ಕೀಟ ನಿಯಂತ್ರಣ",
          "created_at": 1726000000.0,
          "updated_at": 1726000500.0,
          "messages": [...],
          "state": {...}
        }
      }
    }
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is not None:
            self.db_path = Path(db_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = base_dir / "database" / "conversations.json"

        self._ensure_db_initialized()

    def _ensure_db_initialized(self):
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_data({})

    def _read_data(self) -> Dict[str, Dict[str, Any]]:
        if not self.db_path.exists():
            return {}
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except Exception as e:
            logger.error(f"Error reading conversations storage {self.db_path}: {e}")
            return {}

    def _write_data(self, data: Dict[str, Dict[str, Any]]):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing conversations storage {self.db_path}: {e}")

    @staticmethod
    def generate_title(first_message: str, crop_name: Optional[str] = None) -> str:
        """
        Generate a clean, meaningful title from the initial user query
        without invoking expensive LLM calls.
        """
        if not first_message or not first_message.strip():
            return "ಹೊಸ ಸಂಭಾಷಣೆ / New Conversation"

        clean = first_message.strip()
        # Remove markdown symbols and extra punctuation
        clean = clean.replace("#", "").replace("*", "").replace(">", "").strip()

        # Remove repetitive conversational greetings/prefixes
        prefixes_to_strip = [
            "ನಮಸ್ಕಾರ ", "ನನ್ನ ", "ನನಗೆ ", "ಹಲೋ ", "ಹಾಯ್ ",
            "hello ", "hi ", "hey ", "dear sir ", "please tell me "
        ]
        lower_clean = clean.lower()
        for prefix in prefixes_to_strip:
            if lower_clean.startswith(prefix):
                clean = clean[len(prefix):].strip()
                break

        if not clean:
            clean = first_message.strip()

        # Limit to 35 characters at word boundary
        if len(clean) <= 35:
            return clean

        words = clean.split()
        short_title = ""
        for word in words:
            if len(short_title) + len(word) + 1 > 32:
                break
            short_title = f"{short_title} {word}".strip()

        return f"{short_title}..." if short_title else clean[:32] + "..."

    def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
        initial_state: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new persistent conversation thread for the given user.
        If conversation_id is provided, uses that specific identifier.
        """
        if not user_id:
            raise ValueError("user_id must be provided to create a conversation.")

        conv_id = conversation_id or str(uuid.uuid4())
        now = time.time()

        conv = {
            "id": conv_id,
            "user_id": user_id,
            "title": title or "ಹೊಸ ಸಂಭಾಷಣೆ / New Conversation",
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "state": initial_state or {},
        }

        data = self._read_data()
        if user_id not in data:
            data[user_id] = {}

        data[user_id][conv_id] = conv
        self._write_data(data)
        logger.info(f"Created persistent conversation {conv_id} for user {user_id}")
        return conv

    def get_user_conversations(self, user_id: str, include_empty: bool = False) -> List[Dict[str, Any]]:
        """
        Retrieve all conversations owned by user_id, ordered newest first (updated_at DESC).
        Returns lightweight metadata without full message payloads for high performance.
        By default excludes empty 0-message sessions so unused placeholders don't clutter history.
        """
        if not user_id:
            return []

        data = self._read_data()
        user_threads = data.get(user_id, {})
        if not isinstance(user_threads, dict):
            return []

        summaries = []
        for conv_id, conv in user_threads.items():
            messages = conv.get("messages", [])
            if not include_empty and len(messages) == 0:
                continue

            preview = ""
            for m in reversed(messages):
                if m.get("role") in ("farmer", "user"):
                    preview = m.get("content", "")
                    break

            summaries.append({
                "id": conv["id"],
                "title": conv.get("title", "Conversation"),
                "created_at": conv.get("created_at", 0),
                "updated_at": conv.get("updated_at", conv.get("created_at", 0)),
                "message_count": len(messages),
                "preview": preview[:60] if preview else "",
            })

        # Order newest updated first
        summaries.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        return summaries

    def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single conversation by ID, strictly enforcing user ownership.
        Returns None if not found or if the conversation belongs to a different user.
        """
        if not user_id or not conversation_id:
            return None

        data = self._read_data()
        user_threads = data.get(user_id, {})
        if conversation_id in user_threads:
            return user_threads[conversation_id]

        return None

    def add_message(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        auto_title: bool = True
    ) -> Dict[str, Any]:
        """
        Append a message to a user-owned conversation.
        If this is the first user turn, auto-generates a descriptive title.
        """
        if not user_id or not conversation_id:
            raise ValueError("user_id and conversation_id are required.")

        data = self._read_data()
        if user_id not in data or conversation_id not in data[user_id]:
            # Conversation does not exist for this user; create it on the fly
            if user_id not in data:
                data[user_id] = {}
            now = time.time()
            data[user_id][conversation_id] = {
                "id": conversation_id,
                "user_id": user_id,
                "title": "ಹೊಸ ಸಂಭಾಷಣೆ / New Conversation",
                "created_at": now,
                "updated_at": now,
                "messages": [],
                "state": {},
            }

        conv = data[user_id][conversation_id]
        now = time.time()

        msg_id = f"msg_{secrets_token()}"
        msg = {
            "id": msg_id,
            "role": role,
            "content": content,
            "timestamp": now,
            "metadata": metadata or {},
        }

        conv["messages"].append(msg)
        conv["updated_at"] = now

        # If it's a user turn and title is still default, update title
        if auto_title and role in ("farmer", "user"):
            is_default_title = (
                not conv.get("title")
                or conv.get("title") == "ಹೊಸ ಸಂಭಾಷಣೆ / New Conversation"
                or conv.get("title") == "New Conversation"
            )
            if is_default_title:
                crop = conv.get("state", {}).get("crop_name")
                conv["title"] = self.generate_title(content, crop_name=crop)

        self._write_data(data)
        return msg

    def update_dialogue_state(self, user_id: str, conversation_id: str, state: Dict[str, Any]):
        """Update structured dialogue state for contextual continuation."""
        if not user_id or not conversation_id:
            return

        data = self._read_data()
        if user_id in data and conversation_id in data[user_id]:
            data[user_id][conversation_id]["state"] = state
            self._write_data(data)

    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        Permanently delete a conversation thread and its messages.
        Enforces user ownership: User A cannot delete User B's conversation.
        """
        if not user_id or not conversation_id:
            return False

        data = self._read_data()
        if user_id in data and conversation_id in data[user_id]:
            del data[user_id][conversation_id]
            self._write_data(data)
            logger.info(f"Permanently deleted conversation {conversation_id} for user {user_id}")
            return True

        return False

    def find_owner_of_conversation(self, conversation_id: str) -> Optional[str]:
        """Internal helper to locate the user who owns a given conversation ID."""
        data = self._read_data()
        for uid, threads in data.items():
            if conversation_id in threads:
                return uid
        return None


def secrets_token() -> str:
    import secrets
    return secrets.token_hex(6)
