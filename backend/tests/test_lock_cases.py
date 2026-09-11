"""
test_lock_cases.py — Verification of Locked Behaviors for Case 2, Case 3, and Case 4.

Tests:
1. Case 2: Semantic database match -> Database Verified provenance
2. Case 3: Agricultural question with no DB record -> Gemini called, indicator before answer, clean history
3. Case 3 missing-crop follow-up: 'ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ, ಏನು ಮಾಡಬೇಕು?' -> asks for crop
4. Case 3 crop supplied: Turn 2 'ಮೆಣಸಿನಕಾಯಿ' -> fuses context, answers chilli leaf yellowing, does NOT ask crop again
5. Case 4: Non-agricultural queries -> polite refusal, Gemini NOT called, no indicator
"""
import sys, os
sys.path.insert(0, os.path.abspath("."))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
import pytest
from unittest.mock import patch
from app.conversation.session_manager import SessionManager
from app.rag.retriever import Retriever
from app.llm.response_generator import ResponseGenerator


@pytest.fixture(scope="module")
def app_components():
    sm = SessionManager()
    retriever = Retriever()
    retriever.load()
    rg = ResponseGenerator(retriever, sm)
    return rg


@pytest.mark.asyncio
async def test_case2_semantic_variant(app_components):
    """
    Case 2: User asks an agricultural question with semantic phrasing variant.
    Must retrieve database match and return source='database', context_used=True.
    """
    rg = app_components
    session_id = "test_lock_case2_semantic"
    user_query = "ಸಾವಯವವಾಗಿ ಬೆಳೆದ ಕಡಲೆಯಲ್ಲಿ ಕಳೆ ನಿಯಂತ್ರಣಕ್ಕೆ ಯಾವ ವಿಧಾನಗಳನ್ನು ಅನುಸರಿಸಬೇಕು?"
    res = await rg.generate(session_id, user_query, language="kn")

    assert res.get("source") == "database", f"Expected source='database', got {res.get('source')}"
    assert res.get("context_used") is True, "Expected context_used=True"
    assert "ಸ್ಟೇಲ್" in res.get("response", "") or "ಕಳೆ" in res.get("response", "")


@pytest.mark.asyncio
async def test_case3_gemini_agri_question(app_components):
    """
    Case 3: Agricultural question requiring Gemini fallback (no DB record).
    Indicator appears before answer, answer is detailed, indicator stripped from history.
    """
    rg = app_components
    session_id = "test_lock_case3_gemini"
    user_query = "ಡ್ರ್ಯಾಗನ್ ಫ್ರೂಟ್ ಬೆಳೆಯನ್ನು ಹೇಗೆ ಬೆಳೆಯಬೇಕು?"
    res = await rg.generate(session_id, user_query, language="kn")

    assert res.get("source") == "llm"
    assert res.get("provider") == "gemini"
    assert res.get("context_used") is False

    resp = res.get("response", "")
    greeting = "ನಮಸ್ಕಾರ ಕೃಷಿ ಬಾಂಧವರೇ! 🌾"
    indicator = "Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... / Fetching answer from Gemini..."
    assert greeting in resp
    assert indicator in resp
    assert resp.find(greeting) < resp.find(indicator)

    # Verify history is clean
    history = rg.session_manager.get_full_history(session_id)
    assert indicator not in history[-1]["content"]


@pytest.mark.asyncio
async def test_case3_multi_turn_followup_flow(app_components):
    """
    Case 3 multi-turn follow-up:
    Turn 1: 'ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ, ಏನು ಮಾಡಬೇಕು?' -> Asks which crop
    Turn 2: 'ಮೆಣಸಿನಕಾಯಿ' -> Fuses context, answers chilli yellowing, does NOT ask crop again
    """
    rg = app_components
    session_id = "test_lock_case3_multiturn"

    # Turn 1: Missing crop
    q1 = "ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ, ಏನು ಮಾಡಬೇಕು?"
    res1 = await rg.generate(session_id, q1, language="kn")
    resp1 = res1.get("response", "")
    assert "ಯಾವ ಬೆಳೆ" in resp1, f"Expected crop question, got: {resp1}"

    # Turn 2: Crop supplied
    q2 = "ಮೆಣಸಿನಕಾಯಿ"
    res2 = await rg.generate(session_id, q2, language="kn")
    resp2 = res2.get("response", "")

    # Must NOT ask "ಯಾವ ಬೆಳೆ?" again
    assert "ಯಾವ ಬೆಳೆ ಬೆಳೆಯುತ್ತಿದ್ದೀರಿ ಎಂದು ಹೇಳಿ" not in resp2, "Should NOT ask for crop again!"
    assert "ಮೆಣಸಿನಕಾಯಿ" in resp2, "Should address chilli crop"
    assert any(w in resp2 for w in ["ಹಳದಿ", "ರೋಗ", "ಕೀಟ", "ನುಸಿ", "ಥ್ರಿಪ್ಸ್", "ಪೋಷಕಾಂಶ"]), "Should address yellowing problem"


@pytest.mark.asyncio
async def test_case4_non_agri_refusals(app_components):
    """
    Case 4: Non-agricultural queries must be refused politely.
    Gemini must NOT be called, and no fetching indicator must be emitted.
    """
    rg = app_components
    test_queries = [
        "ವಿರಾಟ್ ಕೊಹ್ಲಿ ಬಗ್ಗೆ ಮಾಹಿತಿ ಕೊಡಿ.",
        "ಬೆಂಗಳೂರಿಗೆ ರೈಲು ಟಿಕೆಟ್ ಹೇಗೆ ಬುಕ್ ಮಾಡುವುದು?",
        "What is the capital of France?",
    ]

    for q in test_queries:
        session_id = f"test_lock_case4_{abs(hash(q))}"
        
        # Patch _call_llm and _stream_llm to ensure Gemini is NOT called
        with patch.object(rg, "_call_llm") as mock_call, \
             patch.object(rg, "_stream_llm") as mock_stream:
            
            res = await rg.generate(session_id, q, language="kn")
            resp = res.get("response", "")

            # Verify Gemini was never invoked
            assert mock_call.call_count == 0, f"Gemini _call_llm was invoked for Case 4 query: '{q}'"
            assert mock_stream.call_count == 0, f"Gemini _stream_llm was invoked for Case 4 query: '{q}'"

            # Verify no indicator
            assert "Fetching answer from Gemini" not in resp
            assert "Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ" not in resp

            # Verify polite agricultural refusal
            assert any(w in resp for w in ["ಕ್ಷಮಿಸಿ", "ಕೃಷಿಗೆ ಸಂಬಂಧಿಸಿದ", "Sorry", "agricultural"]), f"Expected refusal, got: {resp}"
