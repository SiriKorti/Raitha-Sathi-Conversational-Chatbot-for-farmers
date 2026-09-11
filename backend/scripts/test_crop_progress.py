"""
test_crop_progress.py — Comprehensive Unit Verification for Crop Progress Engine
"""

import sys
import asyncio
from datetime import date, timedelta
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app.services.agronomic_service import AgronomicService
from app.services.farm_manager import calculate_crop_progress

async def main():
    print("=" * 60)
    print("RUNNING CROP PROGRESS ENGINE VERIFICATION")
    print("=" * 60)

    service = AgronomicService()
    today = date(2026, 9, 11)

    # -------------------------------------------------------------
    # TEST 1: Seasonal Crop (Paddy)
    # -------------------------------------------------------------
    print("\n--- TEST 1: Seasonal Crop (Paddy) ---")
    paddy_ref = await service.get_crop_agronomy("Paddy")
    paddy_sown = (today - timedelta(days=50)).strftime("%Y-%m-%d")
    paddy_prog = calculate_crop_progress("Paddy", paddy_sown, agronomy_ref=paddy_ref, current_date=today)
    print(f"Crop: {paddy_prog['crop_name']} | Days Elapsed: {paddy_prog['days_elapsed']}")
    print(f"Duration: {paddy_prog['duration_days_min']}–{paddy_prog['duration_days_max']} days")
    print(f"Progress: {paddy_prog['progress_percentage_min']}% – {paddy_prog['progress_percentage_max']}%")
    print(f"Current Stage: {paddy_prog['current_stage']['name']}")
    print(f"Estimated Harvest: {paddy_prog['estimated_harvest_date_min']} to {paddy_prog['estimated_harvest_date_max']}")
    print(f"Days Remaining: {paddy_prog['days_until_harvest_min']}–{paddy_prog['days_until_harvest_max']} days")

    assert paddy_prog['days_elapsed'] == 50
    assert paddy_prog['duration_days_min'] == 120
    assert paddy_prog['is_perennial'] is False
    assert paddy_prog['current_stage'] is not None
    assert "Booting" in paddy_prog['current_stage']['name'] or "Stem" in paddy_prog['current_stage']['name']

    # -------------------------------------------------------------
    # TEST 2: Perennial Crop (Arecanut) - Young (Planted 2 years ago)
    # -------------------------------------------------------------
    print("\n--- TEST 2: Perennial Crop (Arecanut - 2 Years Old) ---")
    areca_ref = await service.get_crop_agronomy("Arecanut")
    areca_sown = (today - timedelta(days=730)).strftime("%Y-%m-%d")
    areca_prog = calculate_crop_progress("Arecanut", areca_sown, agronomy_ref=areca_ref, current_date=today)
    print(f"Crop: {areca_prog['crop_name']} | Days Elapsed: {areca_prog['days_elapsed']}")
    print(f"Perennial: {areca_prog['is_perennial']} | Crop Type: {areca_prog['crop_type']}")
    print(f"Establishment Progress: {areca_prog['progress_percentage_min']}%")
    print(f"Current Stage: {areca_prog['current_stage']['name']}")
    print(f"Stage Desc: {areca_prog['current_stage']['description']}")
    print(f"Estimated First Bearing: {areca_prog['estimated_harvest_date_min']}")
    print(f"Days Remaining to Bearing: {areca_prog['days_until_harvest_min']} days")

    assert areca_prog['is_perennial'] is True
    assert areca_prog['days_elapsed'] == 730
    assert areca_prog['current_stage'] is not None
    assert "Juvenile" in areca_prog['current_stage']['name'] or "Vegetative" in areca_prog['current_stage']['name']
    assert areca_prog['progress_percentage_min'] > 0
    assert areca_prog['estimated_harvest_date_min'] is not None

    # -------------------------------------------------------------
    # TEST 3: Future Sowing Date (e.g. 2026-09-22)
    # -------------------------------------------------------------
    print("\n--- TEST 3: Future Sowing Date (2026-09-22 vs today 2026-09-11) ---")
    future_date = "2026-09-22"
    future_prog = calculate_crop_progress("Arecanut", future_date, agronomy_ref=areca_ref, current_date=today)
    print(f"Crop: {future_prog['crop_name']} | Sowing Date: {future_prog['sowing_date']}")
    print(f"Is Future: {future_prog['is_future']} | Days Until Planting: {future_prog['days_until_planting']}")
    print(f"Days Elapsed: {future_prog['days_elapsed']} | Progress: {future_prog['progress_percentage_min']}%")
    print(f"Current Stage: {future_prog['current_stage']['name']}")

    assert future_prog['is_future'] is True
    assert future_prog['days_until_planting'] == 11
    assert future_prog['days_elapsed'] == 0
    assert future_prog['progress_percentage_min'] == 0.0
    assert "Scheduled" in future_prog['current_stage']['name']

    # -------------------------------------------------------------
    # TEST 4: Mature Annual Crop (e.g. Maize sown 150 days ago)
    # -------------------------------------------------------------
    print("\n--- TEST 4: Mature Annual Crop (Maize sown 150 days ago) ---")
    maize_ref = await service.get_crop_agronomy("Maize")
    maize_sown = (today - timedelta(days=150)).strftime("%Y-%m-%d")
    maize_prog = calculate_crop_progress("Maize", maize_sown, agronomy_ref=maize_ref, current_date=today)
    print(f"Crop: {maize_prog['crop_name']} | Days Elapsed: {maize_prog['days_elapsed']}")
    print(f"Is Mature: {maize_prog['is_mature']} | Progress: {maize_prog['progress_percentage_min']}%")
    print(f"Days Until Harvest: {maize_prog['days_until_harvest_min']}")
    print(f"Current Stage: {maize_prog['current_stage']['name']}")

    assert maize_prog['is_mature'] is True
    assert maize_prog['progress_percentage_min'] == 100.0
    assert maize_prog['days_until_harvest_min'] == 0
    assert maize_prog['current_stage'] is not None
    assert "Maturity" in maize_prog['current_stage']['name'] or "Harvest" in maize_prog['current_stage']['name']

    # -------------------------------------------------------------
    # TEST 5: Day 0 Newly Planted Crop
    # -------------------------------------------------------------
    print("\n--- TEST 5: Day 0 Newly Planted Crop ---")
    ragi_ref = await service.get_crop_agronomy("Ragi")
    ragi_sown = today.strftime("%Y-%m-%d")
    ragi_prog = calculate_crop_progress("Ragi", ragi_sown, agronomy_ref=ragi_ref, current_date=today)
    print(f"Crop: {ragi_prog['crop_name']} | Days Elapsed: {ragi_prog['days_elapsed']}")
    print(f"Progress: {ragi_prog['progress_percentage_min']}%")
    print(f"Stage: {ragi_prog['current_stage']['name']}")

    assert ragi_prog['days_elapsed'] == 0
    assert ragi_prog['progress_percentage_min'] == 0.0
    assert "Germination" in ragi_prog['current_stage']['name']

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
