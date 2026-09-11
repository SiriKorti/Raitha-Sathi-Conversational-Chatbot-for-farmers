"""
Official Case 1 Behavior Lock Regression Test.
Tests exact database match retrieval, Gold Standard structure, grounding, and metadata.
"""
import sys, os
sys.path.insert(0, os.path.abspath("."))
import asyncio
import pytest
from app.conversation.session_manager import SessionManager
from app.rag.retriever import Retriever
from app.llm.response_generator import ResponseGenerator

@pytest.mark.asyncio
async def test_case1_exact_match_coconut():
    sm = SessionManager()
    retriever = Retriever()
    rg = ResponseGenerator(retriever, sm)
    
    q = "ಕರ್ನಾಟಕದಲ್ಲಿ ತೆಂಗು ಬೆಳೆಯಲು ಸೂಕ್ತವಾದ ಮಣ್ಣು ಯಾವುದು?"
    res = await rg.generate("test_case1_coconut", q, language="kn")
    
    assert res.get("source") == "database", f"Expected source='database', got {res.get('source')}"
    assert res.get("provider") == "database", f"Expected provider='database', got {res.get('provider')}"
    
    resp_text = res.get("response", "")
    assert rg._DB_MATCH_SENTINEL not in resp_text, "Sentinel leaked in response text"
    assert "ನಮಸ್ಕಾರ" in resp_text, "Missing polite greeting"
    assert "ತೆಂಗು" in resp_text, "Missing crop reference"
    assert "ಮಣ್ಣು ನಿರ್ವಹಣೆ" in resp_text, "Missing Kannada topic"
    assert "Soil Management" not in resp_text, "English subtopic leaked into Kannada text"
    assert "Sandy Loam / Laterite" in resp_text, "Missing soil type from context"
    assert "Source:" in resp_text, "Missing metadata source"
    assert "Verified Evidence" in resp_text, "Missing verified evidence badge"

@pytest.mark.asyncio
async def test_case1_exact_match_maize():
    sm = SessionManager()
    retriever = Retriever()
    rg = ResponseGenerator(retriever, sm)
    
    q = "ಮೆಕ್ಕೆಜೋಳದ ಬೆಳೆಗೆ ನೀರು ಹಾಯಿಸಲು ಸೂಕ್ತ ಸಮಯ ಯಾವುದು?"
    res = await rg.generate("test_case1_maize", q, language="kn")
    
    assert res.get("source") == "database"
    resp_text = res.get("response", "")
    assert rg._DB_MATCH_SENTINEL not in resp_text
    assert "ನಮಸ್ಕಾರ" in resp_text
    assert "ಮೆಕ್ಕೆಜೋಳ" in resp_text
    assert "ಹಂತ ಹಂತವಾಗಿ" in resp_text
    assert "2026-06-14" in resp_text

@pytest.mark.asyncio
async def test_case1_exact_match_chickpea_pod_borer():
    sm = SessionManager()
    retriever = Retriever()
    rg = ResponseGenerator(retriever, sm)
    
    q = "ಕಡಲೆ ಕಾಯಿಕೊರಕ ಹುಳು ಲಕ್ಷಣಗಳೇನು?"
    res = await rg.generate("test_case1_pod_borer", q, language="kn")
    
    assert res.get("source") == "database", f"Expected source='database', got {res.get('source')}"
    assert res.get("provider") == "database", f"Expected provider='database', got {res.get('provider')}"
    resp_text = res.get("response", "")
    assert rg._DB_MATCH_SENTINEL not in resp_text
    assert "ನಮಸ್ಕಾರ" in resp_text
    assert "ಕಡಲೆ" in resp_text
    assert "ಕಾಯಿಕೊರಕ ಹುಳು" in resp_text
    assert "30-40" in resp_text
    assert "UAS Dharwad" in resp_text

