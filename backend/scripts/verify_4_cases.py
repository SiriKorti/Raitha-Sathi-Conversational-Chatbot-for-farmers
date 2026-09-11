import os
import sys
import asyncio

try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

sys.path.insert(0, os.path.abspath("."))

from app.rag.retriever import Retriever
from app.conversation.session_manager import SessionManager
from app.llm.response_generator import ResponseGenerator

async def test_all_cases():
    retriever = Retriever()
    retriever.load()
    sm = SessionManager()
    gen = ResponseGenerator(retriever, sm)

    test_cases = [
        ("Case 1 (Direct DB Match - Ragi Blast)", "ರಾಗಿ ಬೆಳೆಗೆ ಬೆಂಕಿ ರೋಗ ಬಂದರೆ ಯಾವ ಔಷಧ ಸಿಂಪಡಿಸಬೇಕು?"),
        ("Case 2 (Missing Info / Follow-up - Symptoms with no crop)", "ನನ್ನ ಹೊಲದಲ್ಲಿ ಗಿಡಗಳಿಗೆ ಕೀಟಗಳು ಹಾನಿ ಮಾಡುತ್ತಿವೆ, ಯಾವ ಕೀಟನಾಶಕ ಬಳಸಬೇಕು?"),
        ("Case 3 (Out-of-DB Crop - Apple Farming)", "ನಾನು ಎರಡು ಎಕರೆ ಜಮೀನಿನಲ್ಲಿ ಆಪಲ್ ಹಣ್ಣನ್ನು ಬೆಳೆಯುತ್ತಿದ್ದೇನೆ, ಅದನ್ನ ಹೇಗೆ ಮತ್ತು ಯಾವಾಗ ಬೆಳೆಯಬೇಕು?"),
        ("Case 3 (Out-of-DB - Hydroponic Lettuce)", "ಹೈಡ್ರೋಪೋನಿಕ್ಸ್ ಪದ್ಧತಿಯಲ್ಲಿ ಲೆಟ್ಯೂಸ್ ಬೆಳೆಯುವುದು ಹೇಗೆ?"),
        ("Case 4 (Non-Agricultural - Prime Minister)", "Who is the PM of India?")
    ]

    for label, query in test_cases:
        sid = sm.new_session()
        print("\n" + "="*70)
        print(f"TEST: {label}")
        print(f"Query: {query}")
        print("-"*70)
        
        res = await gen.generate(sid, query)
        
        print(f"Result Source: {res.get('source')} | Provider: {res.get('provider')} | Followup: {res.get('is_followup')}")
        ans_preview = res.get('response', '').replace('\n', ' ')[:180]
        print(f"Response: {ans_preview}...")

if __name__ == "__main__":
    asyncio.run(test_all_cases())
