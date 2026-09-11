"""
dataset_loader.py — Agricultural Dataset Loader & Validator

WHAT IT DOES:
Reads raw agricultural data from JSON files in 'data/raw/', validates 
that they have the required fields (ID, question, answer), and 
cleans up any formatting issues.

WHY IT EXISTS:
Ensures data integrity. By having a dedicated loader, we can catch 
broken or missing data before it ever reaches the AI, preventing 
crashes or nonsensical responses.

CONNECTIONS:
- Used by ingestion scripts to load data before embedding it.
- Connected to 'app.config' for the default data paths.
"""

import json
import re
import uuid
from pathlib import Path
from typing import Optional
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import DatasetLoadError, DatasetValidationError

# Minimum fields every entry must have
REQUIRED_FIELDS = ["id", "question", "language"]


class DatasetLoader:
    """
    Loads and validates agricultural QA datasets from JSON files.

    Supports single JSON file or a directory of JSON files.
    Auto-repairs missing IDs and normalises list/dict fields.
    """

    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = Path(dataset_path or settings.DATASET_PATH)

    # ── Public API ────────────────────────────────────────────────────────────

    def load_all(self) -> list[dict]:
        """
        Load all entries from the configured dataset path.

        Returns:
            Validated list of dataset entry dicts
        Raises:
            DatasetLoadError: if the path does not exist
        """
        if not self.dataset_path.exists():
            raise DatasetLoadError(
                f"Dataset path not found: {self.dataset_path}. "
                "Add JSON files to data/raw/ and run scripts/ingest_data.py"
            )

        entries: list[dict] = []

        if self.dataset_path.is_file():
            entries = self._load_json_file(self.dataset_path)
        elif self.dataset_path.is_dir():
            for json_file in sorted(self.dataset_path.glob("*.json")):
                file_entries = self._load_json_file(json_file)
                entries.extend(file_entries)
                logger.info("Loaded {n} entries from {f}", n=len(file_entries), f=json_file.name)

        validated = self._validate_all(entries)
        logger.info("Total validated entries: {n}", n=len(validated))
        return validated

    def load_sample(self) -> list[dict]:
        """Load the small sample dataset for testing."""
        path = Path(settings.SAMPLE_DATASET_PATH)
        if not path.exists():
            raise DatasetLoadError(f"Sample dataset not found: {path}")
        return self._load_json_file(path)

    def get_unique_crops(self, entries: list[dict]) -> list[str]:
        """Return sorted list of unique crop names in the dataset."""
        return sorted({e["crop_name"] for e in entries if e.get("crop_name")})

    def get_stats(self, entries: list[dict]) -> dict:
        """Return summary stats: counts by language, crop, topic."""
        stats: dict = {"total": len(entries), "by_language": {}, "by_crop": {}, "by_topic": {}}
        for e in entries:
            for key, field in [("by_language", "language"), ("by_crop", "crop_name"), ("by_topic", "topic")]:
                val = e.get(field, "unknown")
                stats[key][val] = stats[key].get(val, 0) + 1
        return stats

    # ── Private Helpers ───────────────────────────────────────────────────────

    def _load_json_file(self, path: Path) -> list[dict]:
        """Read and parse a single JSON file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as e:
            raise DatasetLoadError(f"Invalid JSON in {path}: {e}")

        if isinstance(raw, dict):
            # Unwrap common wrapper keys
            for key in ("entries", "data", "dataset", "records"):
                if key in raw:
                    raw = raw[key]
                    break
            else:
                raw = [raw]

        if not isinstance(raw, list):
            raise DatasetLoadError(f"Expected JSON list in {path}, got {type(raw).__name__}")

        # Infer crop name from filename if not present in each entry
        # e.g., 'maize_info.json' -> 'maize' -> 'ಮೆಕ್ಕೆಜೋಳ'
        raw_crop = path.stem.split('_')[0].lower()
        crop_map = {
            "jowar": "ಜೋಳ", "ragi": "ರಾಗಿ", "cotton": "ಹತ್ತಿ",
            "groundnut": "ಶೇಂಗಾ", "sugarcane": "ಕಬ್ಬು", "rice": "ಭತ್ತ",
            "maize": "ಮೆಕ್ಕೆಜೋಳ", "redgram": "ತೊಗರಿ", "sunflower": "ಸೂರ್ಯಕಾಂತಿ",
            "turmeric": "ಅರಿಶಿನ", "bajra": "ಸಜ್ಜೆ", "coffee": "ಕಾಫಿ",
            "coconut": "ತೆಂಗು", "arecanut": "ಅಡಿಕೆ", "chickpea": "ಕಡಲೆ"
        }
        inferred_crop = crop_map.get(raw_crop, raw_crop)

        for entry in raw:
            if not isinstance(entry, dict):
                continue
            # Infer crop_name from filename
            if not entry.get("crop_name"):
                entry["crop_name"] = inferred_crop
            # Normalize whitespace in text fields (some datasets have triple-spaces or
            # embedded newlines — e.g. maize_info.json uses "   " as separator)
            for field in ("question", "question_kn", "answer", "answer_kn",
                          "question_kannada", "answer_kannada", "solution_kn"):
                if field in entry and isinstance(entry[field], str):
                    entry[field] = re.sub(r'\s+', ' ', entry[field]).strip()

        return raw

    def _validate_all(self, entries: list[dict]) -> list[dict]:
        """Validate and repair all entries; skip completely broken ones."""
        valid, skipped = [], 0
        for i, entry in enumerate(entries):
            try:
                valid.append(self._repair_entry(entry, i))
            except DatasetValidationError as e:
                skipped += 1
                logger.warning("Skipping entry #{i}: {e}", i=i, e=e)

        if skipped:
            logger.warning("Skipped {s}/{t} invalid entries", s=skipped, t=len(entries))
        return valid

    def _repair_entry(self, entry: dict, index: int) -> dict:
        """Validate and fix a single entry in-place."""
        if not isinstance(entry, dict):
            raise DatasetValidationError(f"Entry #{index} is not a dict")

        # Map variant keys to standard keys
        key_mappings = {
            "question_kn": "question",
            "question_kannada": "question",
            "answer_kn": "answer",
            "answer_kannada": "answer",
            "solution_kn": "answer",
            "solution": "answer"
        }
        
        for variant, standard in key_mappings.items():
            if variant in entry and standard not in entry:
                entry[standard] = entry[variant]

        # Auto-generate missing ID
        if not entry.get("id"):
            entry["id"] = str(uuid.uuid4())

        # Must have at least a question or retrieval_text
        if not entry.get("question") and not entry.get("retrieval_text"):
            raise DatasetValidationError(f"Entry #{index} has no question or retrieval_text")

        # Ensure answer is present (even if empty) for RAG output
        if "answer" not in entry:
            entry["answer"] = ""

        # Ensure list fields are lists
        for field in ["question_variants", "keywords", "symptoms", "causes"]:
            if field in entry and not isinstance(entry[field], list):
                entry[field] = [entry[field]] if entry[field] else []

        # Default language
        if not entry.get("language"):
            entry["language"] = "kn"

        return entry
