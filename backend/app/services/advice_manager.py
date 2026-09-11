import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.utils.logger import logger


class StorageCorruptedError(RuntimeError):
    """Raised when the saved advice persistent JSON store is corrupted or malformed."""
    pass


class AdviceManager:
    """
    Manages persistent storage and retrieval of farmer-saved advice records.
    Stores records keyed by user_id in database/saved_advice.json.
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is not None:
            self.db_path = db_path
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = base_dir / "database" / "saved_advice.json"

        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _read_data(self) -> Dict[str, List[Dict[str, Any]]]:
        if not self.db_path.exists():
            return {}

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                data = json.loads(content)
                if not isinstance(data, dict):
                    raise StorageCorruptedError(
                        f"Saved advice storage '{self.db_path}' must contain a root JSON object."
                    )
                return data
        except json.JSONDecodeError as jde:
            logger.error(f"Saved advice storage file corrupted: {self.db_path} - {jde}")
            raise StorageCorruptedError(
                f"Saved advice storage '{self.db_path}' is corrupted: {jde}"
            ) from jde
        except StorageCorruptedError:
            raise
        except Exception as e:
            logger.error(f"Error reading saved advice database: {e}")
            raise StorageCorruptedError(
                f"Unable to read saved advice storage '{self.db_path}': {e}"
            ) from e

    def _write_data(self, data: Dict[str, List[Dict[str, Any]]]):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing saved advice database: {e}")
            raise StorageCorruptedError(
                f"Unable to write to saved advice storage '{self.db_path}': {e}"
            ) from e

    def get_saved_advice(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all saved advice records for a given user, ordered newest first.
        """
        data = self._read_data()
        user_records = data.get(user_id, [])
        if not isinstance(user_records, list):
            return []

        # Sort newest first by saved_at timestamp
        return sorted(
            user_records,
            key=lambda x: x.get("saved_at", ""),
            reverse=True,
        )

    def save_advice(self, user_id: str, advice_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save an already-generated advice record under a user_id.
        Performs deterministic duplicate check (user_id + user_query + content).
        If duplicate exists, returns the existing record (idempotent).
        """
        if not user_id or not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id must be a non-empty string.")

        content = advice_payload.get("content")
        if not content or not isinstance(content, str) or not content.strip():
            raise ValueError("Field 'content' is required and must be a non-empty string.")

        user_query = advice_payload.get("user_query")
        if user_query is not None and isinstance(user_query, str):
            user_query = user_query.strip()
        else:
            user_query = ""

        cleaned_content = content.strip()
        crop = advice_payload.get("crop")
        topic = advice_payload.get("topic")
        source = advice_payload.get("source")
        provider = advice_payload.get("provider")

        data = self._read_data()
        user_records: List[Dict[str, Any]] = data.get(user_id, [])
        if not isinstance(user_records, list):
            user_records = []

        # Deterministic duplicate prevention: check user_query + content
        for existing in user_records:
            existing_query = (existing.get("user_query") or "").strip()
            existing_content = (existing.get("content") or "").strip()
            if existing_query == user_query and existing_content == cleaned_content:
                logger.info(f"Duplicate saved advice detected for user {user_id}. Returning existing record.")
                return existing

        advice_id = str(uuid.uuid4())
        saved_at = datetime.now(timezone.utc).isoformat()

        record = {
            "advice_id": advice_id,
            "user_id": user_id,
            "saved_at": saved_at,
            "user_query": user_query if user_query else None,
            "content": cleaned_content,
            "crop": crop if crop else None,
            "topic": topic if topic else None,
            "source": source if source else None,
            "provider": provider if provider else None,
        }

        user_records.append(record)
        data[user_id] = user_records
        self._write_data(data)

        logger.info(f"Saved new advice record '{advice_id}' for user '{user_id}'.")
        return record

    def delete_advice(self, user_id: str, advice_id: str) -> bool:
        """
        Delete a specific advice record for a user by advice_id.
        Returns True if deleted, False if not found.
        """
        if not user_id or not advice_id:
            return False

        data = self._read_data()
        user_records = data.get(user_id, [])
        if not isinstance(user_records, list) or not user_records:
            return False

        original_count = len(user_records)
        new_records = [rec for rec in user_records if rec.get("advice_id") != advice_id]

        if len(new_records) == original_count:
            # Not found in this user's records
            return False

        data[user_id] = new_records
        self._write_data(data)
        logger.info(f"Deleted advice record '{advice_id}' for user '{user_id}'.")
        return True
