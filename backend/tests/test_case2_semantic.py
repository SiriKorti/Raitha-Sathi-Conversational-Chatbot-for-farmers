"""
Official Case 2 Semantic Match RAG Response Test Suite.
Tests semantic database retrieval, Gold Standard structure, grounding, and metadata.
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
async def test_case2_maize_irrigation(app_components):
    rg = app_components
    user_query = "When should I water maize crop?"
    res = await rg.generate("test_case2_maize", user_query, language="en")
    
    assert res.get("source") == "database", f"Expected source='database', got {res.get('source')}"
    assert res.get("provider") == "database", f"Expected provider='database', got {res.get('provider')}"
    resp_text = res.get("response", "")
    
    # 1. Greeting
    assert any(g in resp_text for g in ["Dear Farmer", "Hello Farmer", "Dear"]), "Missing greeting"
    
    # 2. Maize irrigation grounding (germination, flowering/cob, milking stages)
    resp_lower = resp_text.lower()
    assert "maize" in resp_lower, "Missing maize reference"
    assert any(w in resp_lower for w in ["stage", "germination", "flowering", "milking", "cob"]), "Missing critical irrigation stages"
    
    # 3. Explainability footer
    assert "Source:" in resp_text, "Missing Source in footer"
    assert "Verified Evidence" in resp_text, "Missing Verified Evidence"
    assert "Confidence:" in resp_text, "Missing Confidence"

@pytest.mark.asyncio
async def test_case2_ragi_fertilizer(app_components):
    rg = app_components
    user_query = "What fertilizer should I use for ragi?"
    res = await rg.generate("test_case2_ragi", user_query, language="en")
    
    assert res.get("source") == "database", f"Expected source='database', got {res.get('source')}"
    assert res.get("provider") == "database", f"Expected provider='database', got {res.get('provider')}"
    resp_text = res.get("response", "")
    
    # 1. Greeting
    assert any(g in resp_text for g in ["Dear Farmer", "Hello Farmer", "Dear"]), "Missing greeting"
    
    # 2. Ragi fertilizer grounding (NPK / nitrogen / phosphorus / potash dosage)
    resp_lower = resp_text.lower()
    assert "ragi" in resp_lower or "finger millet" in resp_lower, "Missing ragi reference"
    assert any(w in resp_lower for w in ["npk", "fertilizer", "kg", "dose", "nitrogen"]), "Missing fertilizer dosage details"
    
    # 3. Not a spurious bio-fertilizer seed treatment or sulphur recommendation
    assert "bio-fertilizer seed treatment" not in resp_lower, "Spurious biofertilizer treated as primary answer"
    
    # 4. Explainability footer
    assert "Source:" in resp_text, "Missing Source in footer"
    assert "Verified Evidence" in resp_text, "Missing Verified Evidence"

@pytest.mark.asyncio
async def test_case2_chickpea_msp(app_components):
    rg = app_components
    user_query = "ಕರ್ನಾಟಕದಲ್ಲಿ ಕಡಲೆಗೆ ಸರ್ಕಾರ ನೀಡುವ ಕನಿಷ್ಠ ಬೆಂಬಲ ಬೆಲೆ ಎಷ್ಟು?"
    res = await rg.generate("test_case2_chickpea", user_query, language="kn")
    
    assert res.get("source") == "database", f"Expected source='database', got {res.get('source')}"
    assert res.get("provider") == "database", f"Expected provider='database', got {res.get('provider')}"
    resp_text = res.get("response", "")
    
    # 1. Greeting
    assert "ನಮಸ್ಕಾರ" in resp_text, "Missing Kannada greeting"
    
    # 2. Chickpea & MSP grounding
    assert "ಕಡಲೆ" in resp_text, "Missing chickpea reference"
    assert any(w in resp_text for w in ["ಬೆಂಬಲ ಬೆಲೆ", "MSP", "ಖರೀದಿ", "ಯೋಜನೆ"]), "Missing MSP information"
    
    # 3. Explainability footer
    assert "Source:" in resp_text, "Missing Source in footer"
    assert "Verified Evidence" in resp_text, "Missing Verified Evidence"

@pytest.mark.asyncio
async def test_case2_general_government_subsidies(app_components):
    rg = app_components
    user_query = "What government subsidies are available for farmers?"
    res = await rg.generate("test_case2_subsidies", user_query, language="en")
    
    assert res.get("source") == "database", f"Expected source='database', got {res.get('source')}"
    assert res.get("provider") == "database", f"Expected provider='database', got {res.get('provider')}"
    resp_text = res.get("response", "")
    
    # 1. Greeting
    assert any(g in resp_text for g in ["Dear Farmer", "Hello Farmer", "Dear"]), "Missing greeting"
    
    # 2. Key government schemes present
    resp_lower = resp_text.lower()
    assert any(s in resp_lower for s in ["krishi bhagya", "pm-kisan", "pmfby", "fasal bima", "subsidy"]), "Missing verified schemes"
    
    # 3. Explainability footer
    assert "Source:" in resp_text, "Missing Source in footer"
    assert "Verified Evidence" in resp_text, "Missing Verified Evidence"

@pytest.mark.asyncio
async def test_case2_turmeric_earthing_up(app_components):
    rg = app_components
    user_query = "ಅರಿಶಿನ ಬೆಳೆಗೆ ಮಣ್ಣೇರಿಸುವಿಕೆ ಮಾಡುವುದರಿಂದ ಏನು ಪ್ರಯೋಜನ?"
    res = await rg.generate("test_case2_turmeric", user_query, language="kn")
    
    assert res.get("source") == "database", f"Expected source='database', got {res.get('source')}"
    assert res.get("provider") == "database", f"Expected provider='database', got {res.get('provider')}"
    resp_text = res.get("response", "")
    assert "ನಮಸ್ಕಾರ" in resp_text
    assert "ಅರಿಶಿನ" in resp_text
    assert any(w in resp_text for w in ["ಮಣ್ಣೇರಿಸು", "ಗೆಡ್ಡೆ", "ಬೆಳವಣಿಗೆ"]), "Missing earthing up information"

@pytest.mark.asyncio
async def test_case2_chickpea_organic_weed(app_components):
    rg = app_components
    user_query = "ಸಾವಯವವಾಗಿ ಬೆಳೆದ ಕಡಲೆಯಲ್ಲಿ ಕಳೆ ನಿಯಂತ್ರಣಕ್ಕೆ ಯಾವ ವಿಧಾನಗಳನ್ನು ಅನುಸರಿಸಬೇಕು?"
    res = await rg.generate("test_case2_chickpea_organic", user_query, language="kn")
    
    assert res.get("source") == "database", f"Expected source='database', got {res.get('source')}"
    assert res.get("provider") == "database", f"Expected provider='database', got {res.get('provider')}"
    resp_text = res.get("response", "")
    assert "ನಮಸ್ಕಾರ" in resp_text
    assert "ಕಡಲೆ" in resp_text
    assert any(w in resp_text for w in ["ಕಳೆ", "ಕೈ ಕಳೆ", "ಸ್ಟೇಲ್"]), "Missing weed control information"
