"""
farm_diary.py — Agricultural Journey & History Tracker

WHAT IT DOES:
Provides a persistent lightweight storage mechanism for long-term farm data.
It tracks the timeline of crop events (e.g., sowing, flowering) and 
a history of past advisories for a specific farmer/session.

WHY IT EXISTS:
Allows the assistant to say "Since you planted Ragi 30 days ago..." 
or "Last week we discussed pest management..."
This transforms the AI from a stateless search engine into a long-term companion.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

class FarmDiary:
    def __init__(self, storage_dir: str = "data/user_profiles"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, session_id: str) -> Path:
        return self.storage_dir / f"{session_id}_profile.json"

    def _load_profile(self, session_id: str) -> dict:
        path = self._get_file_path(session_id)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "crop_journey": [],  # List of {date, crop, event}
            "advisory_history": [],  # List of {date, crop, topic, summary}
            "fertilizer_history": [] # List of {date, crop, fertilizer}
        }

    def _save_profile(self, session_id: str, profile: dict):
        with open(self._get_file_path(session_id), "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=4, ensure_ascii=False)

    def add_journey_event(self, session_id: str, crop: str, event: str):
        """Record a major crop lifecycle event (e.g., Sowing)."""
        profile = self._load_profile(session_id)
        profile["crop_journey"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "crop": crop,
            "event": event
        })
        self._save_profile(session_id, profile)

    def add_advisory_record(self, session_id: str, crop: str, topic: str, summary: str):
        """Record what was recommended to the farmer."""
        profile = self._load_profile(session_id)
        profile["advisory_history"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "crop": crop,
            "topic": topic,
            "summary": summary
        })
        self._save_profile(session_id, profile)
        
    def add_fertilizer_record(self, session_id: str, crop: str, fertilizer: str):
        """Record fertilizer application."""
        profile = self._load_profile(session_id)
        profile["fertilizer_history"].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "crop": crop,
            "fertilizer": fertilizer
        })
        self._save_profile(session_id, profile)

    def get_summary(self, session_id: str) -> str:
        """Return a formatted text summary of the farmer's history for the LLM prompt."""
        profile = self._load_profile(session_id)
        lines = []
        
        if profile.get("crop_journey"):
            lines.append("🌱 Crop Journey (ಬೆಳೆಯ ಹಂತಗಳು):")
            for event in profile["crop_journey"][-3:]:
                lines.append(f"  - {event['date']}: {event['crop']} - {event['event']}")
                
        if profile.get("fertilizer_history"):
            lines.append("🧪 Fertilizer History (ಗೊಬ್ಬರ ಬಳಕೆ):")
            for f in profile["fertilizer_history"][-3:]:
                lines.append(f"  - {f['date']}: {f['crop']} - {f['fertilizer']}")
                
        if profile.get("advisory_history"):
            lines.append("🌾 Previous Advisories (ಹಿಂದಿನ ಸಲಹೆಗಳು):")
            for a in profile["advisory_history"][-2:]:
                lines.append(f"  - {a['date']}: {a['crop']} ({a['topic']})")
                
        return "\n".join(lines) if lines else ""
