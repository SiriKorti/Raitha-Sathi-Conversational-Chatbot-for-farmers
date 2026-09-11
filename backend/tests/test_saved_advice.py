"""
test_saved_advice.py — Comprehensive Unit & Integration Tests for Saved Advice Backend

Tests cover:
1. Storage & Manager:
   - Empty storage initialization
   - First save with generated advice_id (UUID) and saved_at (ISO timestamp)
   - Multiple saved records
   - Persistence across manager reloads
   - Content validation (rejects empty/whitespace)
   - Optional metadata handling (crop, topic, source, provider, user_query)
   - Duplicate prevention (deterministic idempotency for same user, query, content)
   - Multi-user isolation (separate users can save identical advice independently)
   - Sorting order (newest saved_at first)
   - Deletion (success, nonexistent record, cross-user delete prevention)

2. REST API Endpoints:
   - GET /api/farm/advice/saved/{user_id}
   - POST /api/farm/advice/saved/{user_id}
   - DELETE /api/farm/advice/saved/{user_id}/{advice_id}
   - 400 Bad Request on missing/empty content
   - 404 Not Found on nonexistent advice deletion
   - Cross-user isolation via API

3. AI / RAG Isolation:
   - Verifies saving and retrieving advice does not invoke LLM, RAG, or Gemini
"""

import json
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.advice_manager import AdviceManager, StorageCorruptedError


@pytest.fixture
def temp_advice_db(tmp_path):
    db_file = tmp_path / "saved_advice.json"
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump({}, f)
    return db_file


@pytest.fixture
def advice_mgr(temp_advice_db):
    return AdviceManager(db_path=temp_advice_db)


@pytest.fixture
def test_client():
    with TestClient(app) as client:
        yield client


# ── 1. Unit Tests: AdviceManager ──────────────────────────────────────────────

def test_empty_storage_returns_empty_list(advice_mgr):
    advice = advice_mgr.get_saved_advice("user_test_1")
    assert advice == []
    assert len(advice) == 0


def test_save_advice_generates_id_and_timestamp(advice_mgr):
    payload = {
        "user_query": "ರಾಗಿ ಬೆಳೆಗೆ ಯಾವ ಗೊಬ್ಬರ ಹಾಕಬೇಕು?",
        "content": "ರಾಗಿ ಬೆಳೆಗೆ ಎಕರೆಗೆ 50 ಕೆಜಿ ಡಿಎಪಿ ಮತ್ತು 25 ಕೆಜಿ ಯೂರಿಯಾ ಬಳಸಲು ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ.",
        "crop": "Ragi",
        "topic": "fertilizer",
        "source": "database",
        "provider": "gemini",
    }
    saved = advice_mgr.save_advice("user_101", payload)

    assert "advice_id" in saved
    assert isinstance(saved["advice_id"], str)
    # Check valid UUID
    uuid_obj = uuid.UUID(saved["advice_id"])
    assert str(uuid_obj) == saved["advice_id"]

    assert "saved_at" in saved
    assert "T" in saved["saved_at"]  # Valid ISO timestamp string
    assert saved["user_id"] == "user_101"
    assert saved["user_query"] == payload["user_query"]
    assert saved["content"] == payload["content"]
    assert saved["crop"] == "Ragi"
    assert saved["topic"] == "fertilizer"
    assert saved["source"] == "database"
    assert saved["provider"] == "gemini"


def test_save_advice_content_validation(advice_mgr):
    # Empty content should raise ValueError
    with pytest.raises(ValueError, match="content"):
        advice_mgr.save_advice("user_101", {"content": "", "user_query": "test"})

    with pytest.raises(ValueError, match="content"):
        advice_mgr.save_advice("user_101", {"content": "   ", "user_query": "test"})

    with pytest.raises(ValueError, match="content"):
        advice_mgr.save_advice("user_101", {"user_query": "test"})

    # Invalid user_id
    with pytest.raises(ValueError, match="user_id"):
        advice_mgr.save_advice("", {"content": "Valid advice"})


def test_save_advice_optional_metadata_null_handling(advice_mgr):
    payload = {
        "content": "General farming advisory without crop tag."
    }
    saved = advice_mgr.save_advice("user_102", payload)

    assert saved["content"] == "General farming advisory without crop tag."
    assert saved["user_query"] is None
    assert saved["crop"] is None
    assert saved["topic"] is None
    assert saved["source"] is None
    assert saved["provider"] is None


def test_duplicate_save_is_idempotent(advice_mgr):
    payload = {
        "user_query": "How to control stem borer in paddy?",
        "content": "Apply Cartap hydrochloride 4G at 10 kg per acre.",
        "crop": "Paddy",
    }

    first_save = advice_mgr.save_advice("user_103", payload)
    second_save = advice_mgr.save_advice("user_103", payload)

    # Must return the identical record (same advice_id, same timestamp)
    assert first_save["advice_id"] == second_save["advice_id"]
    assert first_save["saved_at"] == second_save["saved_at"]

    # Storage should only contain 1 record for this user
    all_advice = advice_mgr.get_saved_advice("user_103")
    assert len(all_advice) == 1


def test_multiple_users_isolated(advice_mgr):
    payload = {
        "user_query": "Tomato blight control",
        "content": "Spray Mancozeb 2g per liter.",
    }

    user_a_save = advice_mgr.save_advice("user_A", payload)
    user_b_save = advice_mgr.save_advice("user_B", payload)

    # Different advice IDs and different user ownership
    assert user_a_save["advice_id"] != user_b_save["advice_id"]
    assert user_a_save["user_id"] == "user_A"
    assert user_b_save["user_id"] == "user_B"

    # User A only sees their own advice
    user_a_records = advice_mgr.get_saved_advice("user_A")
    assert len(user_a_records) == 1
    assert user_a_records[0]["advice_id"] == user_a_save["advice_id"]

    # User B only sees their own advice
    user_b_records = advice_mgr.get_saved_advice("user_B")
    assert len(user_b_records) == 1
    assert user_b_records[0]["advice_id"] == user_b_save["advice_id"]


def test_get_saved_advice_newest_first(advice_mgr):
    user_id = "user_sorting_test"
    rec1 = advice_mgr.save_advice(user_id, {"content": "Advice 1 (first)"})
    rec2 = advice_mgr.save_advice(user_id, {"content": "Advice 2 (second)"})
    rec3 = advice_mgr.save_advice(user_id, {"content": "Advice 3 (third)"})

    records = advice_mgr.get_saved_advice(user_id)
    assert len(records) == 3
    # Newest (Advice 3) first
    assert records[0]["content"] == "Advice 3 (third)"
    assert records[1]["content"] == "Advice 2 (second)"
    assert records[2]["content"] == "Advice 1 (first)"


def test_delete_advice_success_and_failures(advice_mgr):
    user_id = "user_delete_test"
    saved = advice_mgr.save_advice(user_id, {"content": "To be deleted advice."})
    advice_id = saved["advice_id"]

    # Delete existing
    deleted = advice_mgr.delete_advice(user_id, advice_id)
    assert deleted is True

    # Check that it is gone
    records = advice_mgr.get_saved_advice(user_id)
    assert len(records) == 0

    # Delete non-existent
    deleted_again = advice_mgr.delete_advice(user_id, advice_id)
    assert deleted_again is False

    # Delete with wrong user_id cannot delete other user's record
    saved_other = advice_mgr.save_advice("other_user", {"content": "Secret advice."})
    assert advice_mgr.delete_advice("wrong_user", saved_other["advice_id"]) is False
    assert len(advice_mgr.get_saved_advice("other_user")) == 1


def test_persistence_across_manager_reloads(temp_advice_db):
    mgr1 = AdviceManager(db_path=temp_advice_db)
    saved = mgr1.save_advice("user_reload_test", {"content": "Persistent advice across sessions."})
    advice_id = saved["advice_id"]

    # Create fresh manager instance with same db_path
    mgr2 = AdviceManager(db_path=temp_advice_db)
    records = mgr2.get_saved_advice("user_reload_test")
    assert len(records) == 1
    assert records[0]["advice_id"] == advice_id
    assert records[0]["content"] == "Persistent advice across sessions."


# ── 2. Integration Tests: REST API Routes ─────────────────────────────────────

def test_api_get_saved_advice_empty(test_client):
    res = test_client.get("/api/farm/advice/saved/user_api_new")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["user_id"] == "user_api_new"
    assert isinstance(data["advice"], list)


def test_api_post_saved_advice_valid(test_client):
    payload = {
        "user_query": "ತೊಗರಿ ಬೆಳೆಯಲ್ಲಿ ಕಾಯಿಕೊರಕ ಹುಳು ನಿಯಂತ್ರಣ ಹೇಗೆ?",
        "content": "ತೊಗರಿ ಬೆಳೆಯಲ್ಲಿ ಕಾಯಿಕೊರಕ ಹುಳು ನಿಯಂತ್ರಣಕ್ಕಾಗಿ ಎಮಾಮೆಕ್ಟಿನ್ ಬೆಂಜೋಯೆಟ್ 5 ಎಸ್.ಜಿ 0.4 ಗ್ರಾಂ ಪ್ರತಿ ಲೀಟರ್ ನೀರಿಗೆ ಬೆರೆಸಿ ಸಿಂಪಡಿಸಿ.",
        "crop": "Redgram",
        "topic": "pesticide",
        "source": "database",
        "provider": "gemini",
    }
    res = test_client.post("/api/farm/advice/saved/user_api_1", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "data" in data
    saved = data["data"]
    assert saved["crop"] == "Redgram"
    assert saved["advice_id"] is not None
    assert saved["saved_at"] is not None

    # Verify retrieval via GET
    get_res = test_client.get("/api/farm/advice/saved/user_api_1")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["count"] >= 1
    matched = [a for a in get_data["advice"] if a["advice_id"] == saved["advice_id"]]
    assert len(matched) == 1


def test_api_post_saved_advice_invalid_content(test_client):
    res = test_client.post("/api/farm/advice/saved/user_api_1", json={"content": "  "})
    assert res.status_code == 400
    assert "content" in res.json()["detail"].lower()

    res2 = test_client.post("/api/farm/advice/saved/user_api_1", json={})
    assert res2.status_code == 400


def test_api_post_saved_advice_duplicate_idempotent(test_client):
    payload = {
        "user_query": "Coconut button shedding reason?",
        "content": "Boron deficiency or severe water stress causes button shedding.",
        "crop": "Coconut",
    }
    res1 = test_client.post("/api/farm/advice/saved/user_api_dup", json=payload)
    res2 = test_client.post("/api/farm/advice/saved/user_api_dup", json=payload)

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json()["data"]["advice_id"] == res2.json()["data"]["advice_id"]


def test_api_delete_saved_advice(test_client):
    # Save a record
    res = test_client.post(
        "/api/farm/advice/saved/user_api_del",
        json={"content": "Temporary advisory to test deletion."},
    )
    advice_id = res.json()["data"]["advice_id"]

    # Delete it
    del_res = test_client.delete(f"/api/farm/advice/saved/user_api_del/{advice_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Deleting again should return 404
    del_res2 = test_client.delete(f"/api/farm/advice/saved/user_api_del/{advice_id}")
    assert del_res2.status_code == 404


def test_api_cross_user_isolation(test_client):
    # Save for user_alpha
    res = test_client.post(
        "/api/farm/advice/saved/user_alpha",
        json={"content": "Alpha confidential advice."},
    )
    alpha_id = res.json()["data"]["advice_id"]

    # User beta cannot delete alpha's advice
    del_res = test_client.delete(f"/api/farm/advice/saved/user_beta/{alpha_id}")
    assert del_res.status_code == 404

    # User beta's advice list does not show alpha's advice
    get_res = test_client.get("/api/farm/advice/saved/user_beta")
    beta_ids = [a["advice_id"] for a in get_res.json()["advice"]]
    assert alpha_id not in beta_ids


# ── 3. AI / RAG Isolation Test ────────────────────────────────────────────────

def test_saved_advice_does_not_invoke_ai_pipeline(test_client):
    """
    Ensure saving advice does not trigger GeminiClient or ResponseGenerator.
    """
    with patch("app.llm.gemini_client.GeminiClient.generate") as mock_gemini, \
         patch("app.rag.retriever.Retriever.retrieve") as mock_retriever:

        payload = {
            "user_query": "Is Gemini invoked when saving?",
            "content": "No, Saved Advice is purely storage.",
        }
        res = test_client.post("/api/farm/advice/saved/user_ai_isolation", json=payload)
        assert res.status_code == 200

        get_res = test_client.get("/api/farm/advice/saved/user_ai_isolation")
        assert get_res.status_code == 200

        # Verify zero calls to AI/RAG
        mock_gemini.assert_not_called()
        mock_retriever.assert_not_called()


# ── 4. Storage Corruption & Data Preservation Tests ───────────────────────────

def test_corrupted_storage_get_raises_storage_corrupted_error(tmp_path):
    """
    Ensure GET on corrupted JSON raises StorageCorruptedError instead of returning {}.
    """
    corrupt_db = tmp_path / "saved_advice.json"
    corrupt_db.write_text("{ this is completely invalid JSON content [[[", encoding="utf-8")

    mgr = AdviceManager(db_path=corrupt_db)
    with pytest.raises(StorageCorruptedError, match="corrupted"):
        mgr.get_saved_advice("user_corrupt_test")


def test_corrupted_storage_post_preserves_file_and_raises(tmp_path):
    """
    CRITICAL TEST: Ensure POST on corrupted JSON fails safely and DOES NOT overwrite
    or truncate the corrupted file.
    """
    corrupt_db = tmp_path / "saved_advice.json"
    original_corrupt_content = '{"user_1": [{"advice_id": "123", "content": "previous data... BUT MALFORMED'
    corrupt_db.write_text(original_corrupt_content, encoding="utf-8")

    mgr = AdviceManager(db_path=corrupt_db)

    # Attempt to save should raise StorageCorruptedError
    with pytest.raises(StorageCorruptedError):
        mgr.save_advice("user_1", {"content": "New advice attempt that must not overwrite"})

    # Verify that file contents are 100% UNCHANGED
    content_after = corrupt_db.read_text(encoding="utf-8")
    assert content_after == original_corrupt_content


def test_corrupted_storage_delete_raises_storage_corrupted_error(tmp_path):
    """
    Ensure DELETE on corrupted JSON raises StorageCorruptedError rather than falsely
    returning False/404 as if the storage were empty.
    """
    corrupt_db = tmp_path / "saved_advice.json"
    corrupt_db.write_text("NOT_JSON_DATA_AT_ALL", encoding="utf-8")

    mgr = AdviceManager(db_path=corrupt_db)
    with pytest.raises(StorageCorruptedError):
        mgr.delete_advice("user_1", "some_id")


def test_storage_recovery_after_manual_repair(tmp_path):
    """
    Ensure that after replacing corrupted file content with valid JSON, normal
    operations resume properly.
    """
    db_file = tmp_path / "saved_advice.json"
    db_file.write_text("CORRUPTED", encoding="utf-8")

    mgr = AdviceManager(db_path=db_file)
    with pytest.raises(StorageCorruptedError):
        mgr.get_saved_advice("user_1")

    # Manual repair: replace with valid JSON object
    db_file.write_text(json.dumps({}), encoding="utf-8")

    # Normal operations should work again
    saved = mgr.save_advice("user_1", {"content": "Recovered advice."})
    assert saved["content"] == "Recovered advice."
    records = mgr.get_saved_advice("user_1")
    assert len(records) == 1


def test_api_corrupted_storage_returns_http_500(test_client):
    """
    Ensure API returns HTTP 500 Internal Server Error when StorageCorruptedError is raised.
    """
    with patch("app.api.routes.farm.advice_manager.get_saved_advice", side_effect=StorageCorruptedError("simulated corruption")), \
         patch("app.api.routes.farm.advice_manager.save_advice", side_effect=StorageCorruptedError("simulated corruption")), \
         patch("app.api.routes.farm.advice_manager.delete_advice", side_effect=StorageCorruptedError("simulated corruption")):

        # GET returns 500
        get_res = test_client.get("/api/farm/advice/saved/user_test")
        assert get_res.status_code == 500
        assert "unavailable" in get_res.json()["detail"].lower()

        # POST returns 500
        post_res = test_client.post("/api/farm/advice/saved/user_test", json={"content": "Test content"})
        assert post_res.status_code == 500
        assert "unavailable" in post_res.json()["detail"].lower()

        # DELETE returns 500
        del_res = test_client.delete("/api/farm/advice/saved/user_test/some_advice_id")
        assert del_res.status_code == 500
        assert "unavailable" in del_res.json()["detail"].lower()

