"""
test_farm_progress.py — Comprehensive Unit & Integration Tests for Farm Progress

Tests all 16 required scenarios:
1. One crop with sowing date
2. Multiple crops for one farmer
3. Updating one crop without deleting another
4. Future sowing date (days_elapsed clamped to 0)
5. Missing agronomic duration (returns nulls safely)
6. Duration range (duration_min and duration_max preserved)
7. Progress percentage range calculation
8. Harvest-date range calculation
9. Days-until-harvest range calculation
10. Growth-stage calculation when stages exist
11. Missing growth stages (null current_stage)
12. AgronomicService failure (graceful degradation)
13. Invalid sowing date format error
14. Existing farm profile without crop_progress (backward compatibility)
15. Existing farm profile GET route
16. Existing farm profile POST route
"""

import json
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.farm_manager import FarmManager, calculate_crop_progress
from app.services.agronomic_service import AgronomicReference, GrowthStage, AgronomicServiceError


@pytest.fixture
def temp_db_path(tmp_path):
    db_file = tmp_path / "farm_profiles.json"
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump({}, f)
    return db_file


@pytest.fixture
def farm_manager(temp_db_path):
    return FarmManager(db_path=temp_db_path)


@pytest.fixture
def test_client():
    with TestClient(app) as client:
        yield client



# 1. One Crop with Sowing Date
def test_calculate_one_crop():
    current_date = date(2026, 8, 10)
    sowing_date = "2026-07-01"  # 40 days elapsed
    ref = AgronomicReference(
        crop_name="Ragi",
        duration_days_min=100,
        duration_days_max=120,
        growth_stages=[],
    )
    result = calculate_crop_progress("Ragi", sowing_date, variety="GPU-28", agronomy_ref=ref, current_date=current_date)

    assert result["crop_name"] == "Ragi"
    assert result["days_elapsed"] == 40
    assert result["variety"] == "GPU-28"
    assert result["duration_days_min"] == 100
    assert result["duration_days_max"] == 120


# 2. Multiple Crops for One Farmer
def test_multiple_crops_for_one_farmer(farm_manager):
    farm_manager.save_crop_progress("user_101", {"crop_name": "Ragi", "sowing_date": "2026-06-01"})
    farm_manager.save_crop_progress("user_101", {"crop_name": "Paddy", "sowing_date": "2026-07-01"})

    crops = farm_manager.get_crop_progress("user_101")
    assert len(crops) == 2
    names = [c["crop_name"] for c in crops]
    assert "Ragi" in names
    assert "Paddy" in names


# 3. Updating One Crop Without Deleting Another
def test_update_crop_preserves_others(farm_manager):
    farm_manager.save_crop_progress("user_102", {"crop_name": "Ragi", "sowing_date": "2026-06-01", "variety": "GPU-28"})
    farm_manager.save_crop_progress("user_102", {"crop_name": "Paddy", "sowing_date": "2026-06-15", "variety": "Jyothi"})

    # Update only Ragi
    farm_manager.save_crop_progress("user_102", {"crop_name": "Ragi", "sowing_date": "2026-06-05", "variety": "ML-365"})

    crops = farm_manager.get_crop_progress("user_102")
    assert len(crops) == 2
    ragi = next(c for c in crops if c["crop_name"] == "Ragi")
    paddy = next(c for c in crops if c["crop_name"] == "Paddy")

    assert ragi["sowing_date"] == "2026-06-05"
    assert ragi["variety"] == "ML-365"
    assert paddy["sowing_date"] == "2026-06-15"
    assert paddy["variety"] == "Jyothi"


# 4. Future Sowing Date
def test_future_sowing_date():
    current_date = date(2026, 7, 1)
    future_sowing = "2026-07-15"
    ref = AgronomicReference(
        crop_name="Maize",
        duration_days_min=90,
        duration_days_max=110,
        growth_stages=[],
    )
    result = calculate_crop_progress("Maize", future_sowing, agronomy_ref=ref, current_date=current_date)

    assert result["days_elapsed"] == 0
    assert result["sowing_date"] == "2026-07-15"
    assert result["progress_percentage_min"] == 0.0
    assert result["progress_percentage_max"] == 0.0
    assert result["days_until_harvest_min"] == 90
    assert result["days_until_harvest_max"] == 110


# 5. Missing Agronomic Duration
def test_missing_agronomic_duration():
    current_date = date(2026, 7, 10)
    sowing_date = "2026-06-10"
    ref = AgronomicReference(
        crop_name="UnknownCrop",
        duration_days_min=None,
        duration_days_max=None,
        growth_stages=[],
    )
    result = calculate_crop_progress("UnknownCrop", sowing_date, agronomy_ref=ref, current_date=current_date)

    assert result["days_elapsed"] == 30
    assert result["duration_days_min"] is None
    assert result["duration_days_max"] is None
    assert result["progress_percentage_min"] is None
    assert result["progress_percentage_max"] is None
    assert result["estimated_harvest_date_min"] is None
    assert result["estimated_harvest_date_max"] is None
    assert result["days_until_harvest_min"] is None
    assert result["days_until_harvest_max"] is None


# 6. Duration Range Preservation
def test_duration_range_preservation():
    ref = AgronomicReference(
        crop_name="Cotton",
        duration_days_min=150,
        duration_days_max=180,
    )
    result = calculate_crop_progress("Cotton", "2026-05-01", agronomy_ref=ref, current_date=date(2026, 8, 1))

    assert result["duration_days_min"] == 150
    assert result["duration_days_max"] == 180
    assert result["duration_days_min"] != result["duration_days_max"]


# 7. Progress Percentage Range Calculation
def test_progress_percentage_calculation():
    # 60 days elapsed out of 100-120 days
    # min progress = (60 / 120) * 100 = 50.0%
    # max progress = (60 / 100) * 100 = 60.0%
    current_date = date(2026, 8, 30)
    sowing_date = "2026-07-01"
    ref = AgronomicReference(
        crop_name="Paddy",
        duration_days_min=100,
        duration_days_max=120,
    )
    result = calculate_crop_progress("Paddy", sowing_date, agronomy_ref=ref, current_date=current_date)

    assert result["days_elapsed"] == 60
    assert result["progress_percentage_min"] == 50.0
    assert result["progress_percentage_max"] == 60.0


# 8. Harvest Date Range Calculation
def test_harvest_date_range_calculation():
    sowing_date = "2026-06-01"
    ref = AgronomicReference(
        crop_name="Sunflower",
        duration_days_min=85,
        duration_days_max=95,
    )
    result = calculate_crop_progress("Sunflower", sowing_date, agronomy_ref=ref, current_date=date(2026, 7, 1))

    # 2026-06-01 + 85 days = 2026-08-25
    # 2026-06-01 + 95 days = 2026-09-04
    assert result["estimated_harvest_date_min"] == "2026-08-25"
    assert result["estimated_harvest_date_max"] == "2026-09-04"


# 9. Days Until Harvest Range
def test_days_until_harvest_range():
    current_date = date(2026, 7, 1)
    sowing_date = "2026-06-01"  # 30 days elapsed
    ref = AgronomicReference(
        crop_name="Chickpea",
        duration_days_min=90,
        duration_days_max=110,
    )
    result = calculate_crop_progress("Chickpea", sowing_date, agronomy_ref=ref, current_date=current_date)

    assert result["days_elapsed"] == 30
    assert result["days_until_harvest_min"] == 60   # 90 - 30
    assert result["days_until_harvest_max"] == 80   # 110 - 30


# 10. Growth Stage Calculation When Stages Exist
def test_growth_stage_matching():
    current_date = date(2026, 8, 15)
    sowing_date = "2026-07-01"  # 45 days elapsed
    stages = [
        GrowthStage(name="Germination", start_day=0, end_day=10),
        GrowthStage(name="Tillering", start_day=11, end_day=40),
        GrowthStage(name="Flowering", start_day=41, end_day=75, description="Heading phase"),
        GrowthStage(name="Maturity", start_day=76, end_day=110),
    ]
    ref = AgronomicReference(
        crop_name="Ragi",
        duration_days_min=100,
        duration_days_max=110,
        growth_stages=stages,
    )
    result = calculate_crop_progress("Ragi", sowing_date, agronomy_ref=ref, current_date=current_date)

    assert result["days_elapsed"] == 45
    assert result["current_stage"] is not None
    assert result["current_stage"]["name"] == "Flowering"
    assert result["current_stage"]["description"] == "Heading phase"


# 11. Missing Growth Stages
def test_missing_growth_stages():
    ref = AgronomicReference(
        crop_name="Turmeric",
        duration_days_min=240,
        duration_days_max=270,
        growth_stages=[],
    )
    result = calculate_crop_progress("Turmeric", "2026-01-01", agronomy_ref=ref, current_date=date(2026, 4, 1))

    assert result["current_stage"] is None


# 12. AgronomicService Failure / None Ref
def test_agronomic_service_failure_graceful_handling():
    result = calculate_crop_progress("Bajra", "2026-06-01", agronomy_ref=None, current_date=date(2026, 7, 1))

    assert result["crop_name"] == "Bajra"
    assert result["days_elapsed"] == 30
    assert result["duration_days_min"] is None
    assert result["progress_percentage_min"] is None
    assert result["current_stage"] is None


# 13. Invalid Sowing Date
def test_invalid_sowing_date_error():
    with pytest.raises(ValueError) as exc_info:
        calculate_crop_progress("Ragi", "not-a-date")
    assert "Invalid sowing_date format" in str(exc_info.value)


# 14. Existing Farm Profile Without crop_progress
def test_profile_without_crop_progress(farm_manager):
    farm_manager.save_profile("user_old", {
        "farmerName": "Basavaraj",
        "location": "Shimoga",
        "crops": ["Arecanut"],
    })

    crops = farm_manager.get_crop_progress("user_old")
    assert crops == []
    profile = farm_manager.get_profile("user_old")
    assert profile["farmerName"] == "Basavaraj"


# 15. Existing Farm Profile GET API Endpoint
def test_api_get_profile(test_client):
    res = test_client.get("/api/farm/profile/non_existent_test_user")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "not_setup"


# 16. Existing Farm Profile POST API Endpoint
def test_api_post_profile(test_client):
    payload = {
        "farmerName": "Channappa",
        "location": "Dharwad",
        "crops": ["Groundnut"],
    }
    res = test_client.post("/api/farm/profile/user_api_test", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["data"]["farmerName"] == "Channappa"


# 17. API Integration: POST /progress/{user_id} and GET /progress/{user_id}
def test_api_farm_progress_routes(test_client):
    with patch("app.api.routes.farm.agronomic_service.get_crop_agronomy", new_callable=AsyncMock) as mock_get_agronomy:
        mock_get_agronomy.return_value = AgronomicReference(
            crop_name="Ragi",
            duration_days_min=105,
            duration_days_max=120,
            growth_stages=[
                GrowthStage(name="Tillering", start_day=15, end_day=45),
            ],
            source="Test UAS Source",
        )

        # POST progress
        post_payload = {
            "crop_name": "Ragi",
            "sowing_date": "2026-06-01",
            "variety": "GPU-28",
        }
        post_res = test_client.post("/api/farm/progress/user_progress_test", json=post_payload)
        assert post_res.status_code == 200
        post_data = post_res.json()
        assert post_data["status"] == "success"
        assert len(post_data["crops"]) == 1
        assert post_data["crops"][0]["crop_name"] == "Ragi"
        assert post_data["crops"][0]["duration_days_min"] == 105
        assert post_data["crops"][0]["duration_days_max"] == 120

        # GET progress
        get_res = test_client.get("/api/farm/progress/user_progress_test")
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["status"] == "success"
        assert len(get_data["crops"]) == 1
        assert get_data["crops"][0]["variety"] == "GPU-28"
