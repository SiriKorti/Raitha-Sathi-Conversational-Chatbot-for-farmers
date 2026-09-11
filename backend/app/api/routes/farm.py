from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List

from app.services.farm_manager import FarmManager, calculate_crop_progress
from app.services.agronomic_service import AgronomicService, AgronomicReference
from app.services.advice_manager import AdviceManager, StorageCorruptedError
from app.services.weather_service import WeatherService
from app.utils.logger import logger

router = APIRouter()
farm_manager = FarmManager()
agronomic_service = AgronomicService()
advice_manager = AdviceManager()

@router.get("/weather/{location}")
async def get_live_weather(location: str):
    """
    Retrieve real-time structured weather data, hourly curve, and 7-day forecast.
    """
    logger.info(f"Fetching live weather for: {location}")
    try:
        data = WeatherService.get_weather_data(location)
        return data
    except Exception as e:
        logger.error(f"Error fetching weather for {location}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch weather data")


@router.get("/profile/{user_id}")
async def get_farm_profile(user_id: str):
    """
    Retrieve farm profile data for a given user.
    """
    logger.info(f"Fetching farm profile for user: {user_id}")
    profile = farm_manager.get_profile(user_id)
    if profile:
        return {"status": "success", "data": profile}
    else:
        # Instead of 404, we can just return empty data or status 'not_setup'
        return {"status": "not_setup", "data": None}


@router.post("/profile/{user_id}")
async def save_farm_profile(user_id: str, payload: Dict[str, Any]):
    """
    Save or update farm profile data for a given user.
    """
    logger.info(f"Saving farm profile for user: {user_id}")
    
    try:
        # Merge or overwrite. For now, we overwrite the whole profile
        updated_profile = farm_manager.save_profile(user_id, payload)
        return {"status": "success", "message": "Farm profile saved successfully.", "data": updated_profile}
    except Exception as e:
        logger.error(f"Failed to save farm profile for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save farm profile")


@router.get("/progress/{user_id}")
async def get_farm_progress(user_id: str):
    """
    Retrieve farmer's crop progress records and calculate deterministic progress.
    """
    logger.info(f"Fetching farm progress for user: {user_id}")
    raw_crops = farm_manager.get_crop_progress(user_id)
    if not raw_crops:
        return {"status": "success", "user_id": user_id, "crops": []}

    calculated_crops = []
    # Per-request lookup to avoid duplicate AI calls for identical crops within the same request
    agronomy_cache: Dict[str, Optional[AgronomicReference]] = {}

    for crop in raw_crops:
        crop_name = crop.get("crop_name", "").strip()
        sowing_date_str = crop.get("sowing_date", "")
        variety = crop.get("variety")

        if not crop_name or not sowing_date_str:
            continue

        cache_key = crop_name.lower()
        if cache_key not in agronomy_cache:
            try:
                ref = await agronomic_service.get_crop_agronomy(crop_name)
                agronomy_cache[cache_key] = ref
            except Exception as e:
                logger.warning(
                    f"Agronomic reference fetch failed for {crop_name}: {e}"
                )
                agronomy_cache[cache_key] = None

        ref = agronomy_cache[cache_key]
        try:
            calculated = calculate_crop_progress(
                crop_name=crop_name,
                sowing_date_str=sowing_date_str,
                variety=variety,
                agronomy_ref=ref,
            )
            calculated_crops.append(calculated)
        except ValueError as ve:
            logger.warning(f"Invalid crop progress date for user {user_id}: {ve}")
            continue

    return {
        "status": "success",
        "user_id": user_id,
        "crops": calculated_crops,
    }


@router.post("/progress/{user_id}")
async def save_farm_progress(user_id: str, payload: Dict[str, Any]):
    """
    Create or update a farmer's crop progress record.
    """
    logger.info(f"Saving crop progress for user: {user_id}")

    entries_to_save: List[Dict[str, Any]] = []
    if "crops" in payload and isinstance(payload["crops"], list):
        entries_to_save = payload["crops"]
    else:
        entries_to_save = [payload]

    if not entries_to_save:
        raise HTTPException(status_code=400, detail="No crop progress payload provided.")

    for entry in entries_to_save:
        if not isinstance(entry, dict):
            raise HTTPException(status_code=400, detail="Invalid crop entry payload.")

        crop_name = entry.get("crop_name")
        sowing_date = entry.get("sowing_date")

        if not crop_name or not isinstance(crop_name, str) or not crop_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Field 'crop_name' is required and must be a non-empty string.",
            )

        if not sowing_date or not isinstance(sowing_date, str):
            raise HTTPException(
                status_code=400,
                detail="Field 'sowing_date' is required in YYYY-MM-DD format.",
            )

        try:
            datetime.strptime(sowing_date.strip(), "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid date format '{sowing_date}'. Expected YYYY-MM-DD.",
            )

        clean_entry = {
            "crop_name": crop_name.strip(),
            "sowing_date": sowing_date.strip(),
            "variety": entry.get("variety"),
        }
        farm_manager.save_crop_progress(user_id, clean_entry)

    return await get_farm_progress(user_id)


@router.delete("/progress/{user_id}/{crop_name}")
async def delete_farm_crop_progress(user_id: str, crop_name: str):
    """
    Remove a crop from a farmer's progress tracker and return updated list.
    """
    logger.info(f"Removing crop progress for user {user_id}, crop: {crop_name}")
    farm_manager.delete_crop_progress(user_id, crop_name)
    return await get_farm_progress(user_id)


# ── Saved Advice Endpoints ───────────────────────────────────────────────────

@router.get("/advice/saved/{user_id}")
async def get_saved_advice(user_id: str):
    """
    Retrieve all saved advice records for a given user, sorted newest first.
    """
    logger.info(f"Fetching saved advice for user: {user_id}")
    try:
        advice_list = advice_manager.get_saved_advice(user_id)
        return {
            "status": "success",
            "user_id": user_id,
            "count": len(advice_list),
            "advice": advice_list,
        }
    except StorageCorruptedError as sce:
        logger.error(f"Saved advice storage corrupted during GET for {user_id}: {sce}")
        raise HTTPException(
            status_code=500, detail="Saved advice storage is currently unavailable."
        )
    except Exception as e:
        logger.error(f"Failed to fetch saved advice for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch saved advice.")


@router.post("/advice/saved/{user_id}")
async def save_advice(user_id: str, payload: Dict[str, Any]):
    """
    Save an already-generated advice record under a user_id without calling AI.
    """
    logger.info(f"Saving advice for user: {user_id}")
    if not payload or not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid request payload.")

    content = payload.get("content")
    if not content or not isinstance(content, str) or not content.strip():
        raise HTTPException(
            status_code=400,
            detail="Field 'content' is required and must be a non-empty string.",
        )

    try:
        saved_record = advice_manager.save_advice(user_id, payload)
        return {
            "status": "success",
            "message": "Advice saved successfully.",
            "data": saved_record,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except StorageCorruptedError as sce:
        logger.error(f"Saved advice storage corrupted during POST for {user_id}: {sce}")
        raise HTTPException(
            status_code=500, detail="Saved advice storage is currently unavailable."
        )
    except Exception as e:
        logger.error(f"Failed to save advice for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save advice.")


@router.delete("/advice/saved/{user_id}/{advice_id}")
async def delete_saved_advice(user_id: str, advice_id: str):
    """
    Delete a specific saved advice record for a user by advice_id.
    """
    logger.info(f"Deleting saved advice '{advice_id}' for user: {user_id}")
    try:
        deleted = advice_manager.delete_advice(user_id, advice_id)
        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Saved advice '{advice_id}' not found for user '{user_id}'.",
            )
        return {
            "status": "success",
            "message": f"Saved advice '{advice_id}' deleted successfully.",
            "advice_id": advice_id,
        }
    except HTTPException:
        raise
    except StorageCorruptedError as sce:
        logger.error(f"Saved advice storage corrupted during DELETE for {user_id}: {sce}")
        raise HTTPException(
            status_code=500, detail="Saved advice storage is currently unavailable."
        )
    except Exception as e:
        logger.error(f"Failed to delete advice for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete advice.")

