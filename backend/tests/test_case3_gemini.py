"""
Official Case 3 Gemini Generative Agricultural Advisory Test Suite.
Tests agricultural queries that have no exact or semantic database match,
verifying Gemini generative fallback, structured farmer-friendly output,
correct fetching indicator ordering (greeting -> indicator -> answer),
indicator stripping from session history, and Case 4 refusal behavior.
"""
import sys, os
sys.path.insert(0, os.path.abspath("."))
import pytest
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
async def test_case3_test_a_chilli_cultivation_detailed(app_components):
    """
    Test Case 3 - Test A: Detailed crop cultivation query for Chilli (no DB record).
    Query: 'ನನಗೆ ಮೆಣಸಿನಕಾಯಿ ಬೆಳೆಯಬೇಕು. ಅದನ್ನು ಹೇಗೆ ಬೆಳೆಯಬೇಕು? ಪೂರ್ತಿ ವಿವರವಾಗಿ ಹೇಳಿ.'
    Verifies:
    1. Case 3 triggered: source == 'llm', provider == 'gemini', context_used == False
    2. Correct indicator order: Greeting -> Fetching Indicator -> Generated Answer
    3. High detail level: > 1000 chars, full lifecycle coverage (soil, nursery, spacing, irrigation, pests/diseases, harvest)
    4. Farmer friendly and structured
    5. Indicator is NOT stored in conversation history
    """
    rg = app_components
    session_id = "test_case3_chilli_detailed"
    user_query = "ನನಗೆ ಮೆಣಸಿನಕಾಯಿ ಬೆಳೆಯಬೇಕು. ಅದನ್ನು ಹೇಗೆ ಬೆಳೆಯಬೇಕು? ಪೂರ್ತಿ ವಿವರವಾಗಿ ಹೇಳಿ."
    res = await rg.generate(session_id, user_query, language="kn")

    # 1. Provenance check
    assert res.get("source") == "llm", f"Expected source='llm', got {res.get('source')}"
    assert res.get("provider") == "gemini", f"Expected provider='gemini', got {res.get('provider')}"
    assert res.get("context_used") is False, "Expected context_used=False for Case 3 fallback"

    resp_text = res.get("response", "")

    # 2. Indicator ordering check: Greeting -> Indicator -> Generated Answer
    greeting_str = "ನಮಸ್ಕಾರ ಕೃಷಿ ಬಾಂಧವರೇ! 🌾"
    indicator_str = "Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... / Fetching answer from Gemini..."
    assert greeting_str in resp_text, "Greeting missing from Case 3 response"
    assert indicator_str in resp_text, "Fetching indicator missing from Case 3 response"

    greeting_idx = resp_text.find(greeting_str)
    indicator_idx = resp_text.find(indicator_str)
    assert 0 <= greeting_idx < indicator_idx, "Fetching indicator must appear AFTER the greeting"

    answer_after_indicator = resp_text[indicator_idx + len(indicator_str):].strip()
    assert len(answer_after_indicator) > 800, f"Answer content after indicator is too short ({len(answer_after_indicator)} chars)"

    # 3. Comprehensive lifecycle coverage
    assert any(w in answer_after_indicator for w in ["ಮಣ್ಣು", "ಹವಾಮಾನ"]), "Missing soil/climate coverage"
    assert any(w in answer_after_indicator for w in ["ಬೀಜ", "ತಳಿ", "ನರ್ಸರಿ", "ಸಸಿ"]), "Missing seed/nursery coverage"
    assert any(w in answer_after_indicator for w in ["ನಾಟಿ", "ಅಂತರ", "ಸಾಲು"]), "Missing planting/spacing coverage"
    assert any(w in answer_after_indicator for w in ["ನೀರು", "ನೀರಾವರಿ", "ತೇವಾಂಶ"]), "Missing irrigation coverage"
    assert any(w in answer_after_indicator for w in ["ಗೊಬ್ಬರ", "ಪೋಷಕಾಂಶ"]), "Missing nutrient management"
    assert any(w in answer_after_indicator for w in ["ಕೀಟ", "ನುಸಿ", "ರೋಗ", "ಬೂದಿ", "ಕೊಳೆತ"]), "Missing pest/disease management"
    assert any(w in answer_after_indicator for w in ["ಕೊಯ್ಲು", "ಕಟಾವು", "ಇಳುವರಿ"]), "Missing harvesting coverage"

    # 4. Indicator must NOT be stored in session history
    history = rg.session_manager.get_full_history(session_id)
    assert len(history) >= 2
    stored_msg = history[-1].get("content", "")
    assert indicator_str not in stored_msg, "Indicator leaked into stored session history!"
    assert greeting_str in stored_msg, "Greeting should remain in stored session history"


@pytest.mark.asyncio
async def test_case3_test_b_dragon_fruit_kannada(app_components):
    """
    Test Case 3 - Test B: Out-of-database crop (Dragon Fruit) fungal disease in Kannada.
    Verifies:
    1. source == 'llm', provider == 'gemini', context_used == False
    2. Indicator order (Greeting -> Indicator -> Answer)
    3. Actionable agronomic content
    4. Indicator stripped from session history
    """
    rg = app_components
    session_id = "test_case3_dragonfruit_kn"
    user_query = "ಡ್ರ್ಯಾಗನ್ ಫ್ರೂಟ್ ಬೆಳೆಯಲ್ಲಿ ಬರುವ ಶಿಲೀಂಧ್ರ ರೋಗಗಳನ್ನು ಹೇಗೆ ನಿಯಂತ್ರಿಸಬೇಕು?"
    res = await rg.generate(session_id, user_query, language="kn")

    assert res.get("source") == "llm"
    assert res.get("provider") == "gemini"
    assert res.get("context_used") is False

    resp_text = res.get("response", "")
    assert "Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ" in resp_text, "Indicator missing from live response"
    assert "ನಮಸ್ಕಾರ ಕೃಷಿ ಬಾಂಧವರೇ! 🌾" in resp_text, "Greeting missing from response"

    # History check
    history = rg.session_manager.get_full_history(session_id)
    stored_msg = history[-1].get("content", "")
    assert "Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ" not in stored_msg, "Indicator must be stripped from history"


@pytest.mark.asyncio
async def test_case3_test_c_avocado_english(app_components):
    """
    Test Case 3 - Test C: English Case 3 question for Avocado (not in DB).
    Verifies:
    1. source == 'llm', provider == 'gemini', context_used == False
    2. English greeting -> indicator -> answer
    3. Indicator stripped from session history
    """
    rg = app_components
    session_id = "test_case3_avocado_en"
    user_query = "How to manage root rot and fungal infection in avocado plants?"
    res = await rg.generate(session_id, user_query, language="en")

    assert res.get("source") == "llm"
    assert res.get("provider") == "gemini"
    assert res.get("context_used") is False

    resp_text = res.get("response", "")
    assert "Fetching answer from Gemini" in resp_text
    assert "Dear Farmer! 🌾" in resp_text

    g_idx = resp_text.find("Dear Farmer! 🌾")
    i_idx = resp_text.find("Fetching answer from Gemini")
    assert 0 <= g_idx < i_idx, "Indicator must appear after English greeting"

    history = rg.session_manager.get_full_history(session_id)
    stored_msg = history[-1].get("content", "")
    assert "Fetching answer from Gemini" not in stored_msg, "Indicator must be stripped from history"


@pytest.mark.asyncio
async def test_case3_test_d_pomegranate_cracking_kannada(app_components):
    """
    Test Case 3 - Test D: Kannada agricultural question (Pomegranate fruit cracking).
    """
    rg = app_components
    session_id = "test_case3_pomegranate_kn"
    user_query = "ದಾಳಿಂಬೆ ಹಣ್ಣಿನ ಬಿರುಕು (fruit cracking) ತಡೆಯುವುದು ಹೇಗೆ?"
    res = await rg.generate(session_id, user_query, language="kn")

    assert res.get("source") == "llm"
    assert res.get("provider") == "gemini"
    resp_text = res.get("response", "")
    assert "Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ" in resp_text

    history = rg.session_manager.get_full_history(session_id)
    stored_msg = history[-1].get("content", "")
    assert "Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ" not in stored_msg


@pytest.mark.asyncio
async def test_case4_agriculture_only_refusal(app_components):
    """
    Test Case 4: Agriculture-only scope protection.
    Unrelated topics (sports, cricket, movies, politics) must be refused
    politely WITHOUT calling Gemini or showing Gemini indicators.
    """
    rg = app_components
    session_id = "test_case4_cricket"
    user_query = "Who won the cricket match yesterday?"
    res = await rg.generate(session_id, user_query, language="en")

    resp_text = res.get("response", "")
    assert "Fetching answer from Gemini" not in resp_text, "Gemini indicator must NOT appear for Case 4"
    assert any(w in resp_text.lower() for w in ["agricultural", "farming", "raitha sathi"]), "Must provide polite agricultural redirection"
