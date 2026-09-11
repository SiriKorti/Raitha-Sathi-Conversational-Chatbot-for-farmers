import asyncio
from app.rag.retriever import Retriever
from app.conversation.session_manager import SessionManager
from app.llm.response_generator import ResponseGenerator

async def run():
    retriever = Retriever()
    retriever.load()
    session_manager = SessionManager()
    gen = ResponseGenerator(retriever, session_manager)
    
    query = "ಕಳೆದ 15 ದಿನಗಳಿಂದ ಮಳೆ ಸರಿಯಾಗಿ ಆಗಿಲ್ಲ. ಭತ್ತದ ಎಲೆಗಳ ತುದಿ ಒಣಗುತ್ತಿದೆ ಮತ್ತು ಕೆಳಗಿನ ಎಲೆಗಳು ಹಳದಿಯಾಗುತ್ತಿವೆ. ಇದು ನೀರಿನ ಕೊರತೆಯೇ ಅಥವಾ ಪೋಷಕಾಂಶದ ಕೊರತೆಯೇ ಎಂದು ಹೇಗೆ ಗುರುತಿಸುವುದು?"
    
    session_id = session_manager.new_session()
    
    result = await gen.generate(
        session_id=session_id,
        user_query=query,
        is_voice_mode=False
    )
    
    print("\n--- RESULT ---")
    print(f"Source: {result.get('source')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Response:\n{result.get('response')}")

asyncio.run(run())
