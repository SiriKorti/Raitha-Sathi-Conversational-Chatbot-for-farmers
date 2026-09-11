import json
import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.utils.logger import logger
from app.services.agronomic_service import AgronomicReference


def calculate_crop_progress(
    crop_name: str,
    sowing_date_str: str,
    variety: Optional[str] = None,
    agronomy_ref: Optional[AgronomicReference] = None,
    current_date: Optional[date] = None,
) -> Dict[str, Any]:
    """
    Deterministically calculates farmer-specific crop progress from sowing date
    and agronomic reference model. Universally supports both Annual and Perennial crops,
    future scheduled sowing dates, mature crops, and dynamic fallbacks.
    """
    if current_date is None:
        current_date = date.today()

    try:
        sowing_date = datetime.strptime(sowing_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        raise ValueError(
            f"Invalid sowing_date format: '{sowing_date_str}'. Expected YYYY-MM-DD."
        )

    calculated_days = (current_date - sowing_date).days
    is_future = calculated_days < 0
    days_until_planting = abs(calculated_days) if is_future else 0
    days_elapsed = 0 if is_future else calculated_days

    crop_type = getattr(agronomy_ref, "crop_type", "annual") if agronomy_ref else "annual"
    is_perennial = getattr(agronomy_ref, "is_perennial", False) if agronomy_ref else (crop_type in ["perennial", "plantation"])
    harvest_season_desc = getattr(agronomy_ref, "harvest_season_description", None) if agronomy_ref else None

    duration_min = agronomy_ref.duration_days_min if agronomy_ref else None
    duration_max = agronomy_ref.duration_days_max if agronomy_ref else None

    progress_min = None
    progress_max = None
    harvest_date_min = None
    harvest_date_max = None
    days_until_harvest_min = None
    days_until_harvest_max = None
    current_stage = None
    is_mature = False

    # ── CASE 1: Future Sowing Date ────────────────────────────────────────────
    if is_future:
        progress_min = 0.0
        progress_max = 0.0
        if duration_min is not None:
            harvest_date_min = (sowing_date + timedelta(days=duration_min)).strftime("%Y-%m-%d")
            days_until_harvest_min = duration_min
        if duration_max is not None:
            harvest_date_max = (sowing_date + timedelta(days=duration_max)).strftime("%Y-%m-%d")
            days_until_harvest_max = duration_max
        elif duration_min is not None:
            harvest_date_max = harvest_date_min
            days_until_harvest_max = days_until_harvest_min

        current_stage = {
            "name": "Scheduled / ಬಿತ್ತನೆ ನಿಗದಿಯಾಗಿದೆ",
            "start_day": 0,
            "end_day": 0,
            "description": f"Sowing is scheduled on {sowing_date_str} (in {days_until_planting} days). Growth tracking begins after planting.",
        }

    # ── CASE 2: Perennial / Plantation Crop ──────────────────────────────────
    elif is_perennial:
        bearing_days = duration_min or 1460  # Default ~4 years
        bearing_max = duration_max or 1825   # Default ~5 years

        if days_elapsed < bearing_days:
            # Establishment / Juvenile phase prior to commercial bearing
            p_val = round(min(100.0, max(0.0, (days_elapsed / bearing_days) * 100.0)), 1)
            progress_min = p_val
            progress_max = p_val
            days_until_harvest_min = max(0, bearing_days - days_elapsed)
            days_until_harvest_max = max(0, bearing_max - days_elapsed)

            bearing_year = sowing_date.year + int(getattr(agronomy_ref, "bearing_age_years_min", None) or 4)
            harvest_date_min = f"{bearing_year}-10-01"
            harvest_date_max = f"{bearing_year}-12-31"
            is_mature = False
        else:
            # Full Economic Bearing phase
            is_mature = True
            progress_min = 100.0
            progress_max = 100.0
            days_until_harvest_min = 0
            days_until_harvest_max = 0
            curr_y = current_date.year
            harvest_date_min = f"{curr_y}-10-01"
            harvest_date_max = f"{curr_y + 1}-02-28"

        # Match perennial developmental stage
        if agronomy_ref and agronomy_ref.growth_stages:
            for stage in agronomy_ref.growth_stages:
                if stage.start_day <= days_elapsed <= stage.end_day:
                    current_stage = {
                        "name": stage.name,
                        "start_day": stage.start_day,
                        "end_day": stage.end_day,
                        "description": stage.description,
                    }
                    break
            # If past the last stage boundary, use the final full-bearing stage
            if not current_stage and agronomy_ref.growth_stages:
                last_stage = agronomy_ref.growth_stages[-1]
                current_stage = {
                    "name": last_stage.name,
                    "start_day": last_stage.start_day,
                    "end_day": last_stage.end_day,
                    "description": last_stage.description or "Mature economic bearing palm. Active annual bunch production.",
                }

    # ── CASE 3: Annual / Seasonal Crop ────────────────────────────────────────
    elif duration_min is not None:
        effective_max = duration_max or duration_min

        # Check maturity
        if days_elapsed >= effective_max:
            is_mature = True
            progress_min = 100.0
            progress_max = 100.0
            days_until_harvest_min = 0
            days_until_harvest_max = 0
            harvest_date_min = (sowing_date + timedelta(days=duration_min)).strftime("%Y-%m-%d")
            harvest_date_max = (sowing_date + timedelta(days=effective_max)).strftime("%Y-%m-%d")

            # Assign mature/harvest stage
            if agronomy_ref and agronomy_ref.growth_stages:
                last_stage = agronomy_ref.growth_stages[-1]
                current_stage = {
                    "name": last_stage.name,
                    "start_day": last_stage.start_day,
                    "end_day": last_stage.end_day,
                    "description": last_stage.description or "Crop has reached harvest maturity. Ready for harvesting.",
                }
        else:
            # Active growth toward harvest
            p_min = (days_elapsed / effective_max) * 100.0
            p_max = (days_elapsed / duration_min) * 100.0
            progress_min = round(min(100.0, max(0.0, p_min)), 1)
            progress_max = round(min(100.0, max(0.0, p_max)), 1)

            harvest_date_min = (sowing_date + timedelta(days=duration_min)).strftime("%Y-%m-%d")
            harvest_date_max = (sowing_date + timedelta(days=effective_max)).strftime("%Y-%m-%d")
            days_until_harvest_min = max(0, duration_min - days_elapsed)
            days_until_harvest_max = max(0, effective_max - days_elapsed)

            if agronomy_ref and agronomy_ref.growth_stages:
                for stage in agronomy_ref.growth_stages:
                    if stage.start_day <= days_elapsed <= stage.end_day:
                        current_stage = {
                            "name": stage.name,
                            "start_day": stage.start_day,
                            "end_day": stage.end_day,
                            "description": stage.description,
                        }
                        break

    # ── Universal Stage Fallback (if no stage matched but progress exists) ────
    if not current_stage:
        if progress_min is not None:
            if progress_min < 15:
                current_stage = {
                    "name": "Germination & Seedling",
                    "start_day": 0,
                    "end_day": 15,
                    "description": "Initial emergence and root development based on standard crop lifecycle.",
                }
            elif progress_min < 45:
                current_stage = {
                    "name": "Vegetative Growth",
                    "start_day": 16,
                    "end_day": 45,
                    "description": "Foliage expansion, tillering, or branching development.",
                }
            elif progress_min < 75:
                current_stage = {
                    "name": "Flowering & Reproductive",
                    "start_day": 46,
                    "end_day": 75,
                    "description": "Flowering, pod setting, or grain filling.",
                }
            else:
                current_stage = {
                    "name": "Maturity & Harvest",
                    "start_day": 76,
                    "end_day": 100,
                    "description": "Crop ripening toward harvest maturity.",
                }

    return {
        "crop_name": crop_name,
        "sowing_date": sowing_date_str,
        "variety": variety,
        "days_elapsed": days_elapsed,
        "duration_days_min": duration_min,
        "duration_days_max": duration_max,
        "progress_percentage_min": progress_min,
        "progress_percentage_max": progress_max,
        "estimated_harvest_date_min": harvest_date_min,
        "estimated_harvest_date_max": harvest_date_max,
        "days_until_harvest_min": days_until_harvest_min,
        "days_until_harvest_max": days_until_harvest_max,
        "current_stage": current_stage,
        "source": agronomy_ref.source if agronomy_ref else "Raitha Sathi Agronomic System",
        "notes": agronomy_ref.notes if agronomy_ref else None,
        "confidence": agronomy_ref.confidence if agronomy_ref else "medium",
        "crop_type": crop_type,
        "is_perennial": is_perennial,
        "is_future": is_future,
        "is_mature": is_mature,
        "days_until_planting": days_until_planting,
        "harvest_season_description": harvest_season_desc,
    }


class FarmManager:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is not None:
            self.db_path = db_path
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = base_dir / "database" / "farm_profiles.json"

        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _read_data(self) -> Dict[str, Any]:
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading farm profiles: {e}")
            return {}

    def _write_data(self, data: Dict[str, Any]):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing farm profiles: {e}")

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        data = self._read_data()
        return data.get(user_id, None)

    def save_profile(self, user_id: str, profile_data: dict) -> Dict[str, Any]:
        data = self._read_data()
        data[user_id] = profile_data
        self._write_data(data)
        return profile_data

    def get_crop_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves raw crop progress records for a user without performing calculations.
        """
        profile = self.get_profile(user_id)
        if not profile or not isinstance(profile, dict):
            return []
        return profile.get("crop_progress", [])

    def save_crop_progress(
        self, user_id: str, crop_entry: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Creates or updates a farmer's crop progress record in a multi-crop list.
        Preserves existing crops when updating a single crop.
        """
        data = self._read_data()
        profile = data.get(user_id, {})
        if not isinstance(profile, dict):
            profile = {}

        crops_list: List[Dict[str, Any]] = profile.get("crop_progress", [])
        if not isinstance(crops_list, list):
            crops_list = []

        target_name = crop_entry.get("crop_name", "").strip().lower()

        # Update existing record if matching crop_name found, otherwise append
        updated = False
        new_crops_list = []
        for existing in crops_list:
            if existing.get("crop_name", "").strip().lower() == target_name:
                # Merge fields while preserving other existing metadata
                merged = {**existing, **crop_entry}
                new_crops_list.append(merged)
                updated = True
            else:
                new_crops_list.append(existing)

        if not updated:
            new_crops_list.append(crop_entry)

        profile["crop_progress"] = new_crops_list
        data[user_id] = profile
        self._write_data(data)
        return new_crops_list

    def delete_crop_progress(self, user_id: str, crop_name: str) -> List[Dict[str, Any]]:
        """
        Removes a crop progress record matching crop_name for a given user.
        """
        data = self._read_data()
        profile = data.get(user_id, {})
        if not isinstance(profile, dict):
            return []

        crops_list: List[Dict[str, Any]] = profile.get("crop_progress", [])
        if not isinstance(crops_list, list):
            return []

        target_name = crop_name.strip().lower()
        new_crops_list = [
            c for c in crops_list
            if c.get("crop_name", "").strip().lower() != target_name
        ]

        profile["crop_progress"] = new_crops_list
        data[user_id] = profile
        self._write_data(data)
        return new_crops_list


