import asyncio
import os
import sys

# Ensure the app module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm.response_generator import ResponseGenerator
from app.conversation.session_manager import SessionManager
from app.rag.retriever import Retriever

async def test_integrations():
    print("Initializing components...")
    # Initialize basic mocks for testing intent extraction and service routing
    session_manager = SessionManager()
    
    class MockRetriever:
        def retrieve(self, query, top_k=3, crop_filter=None, intent_filter=None):
            return []
            
    retriever = MockRetriever()
    generator = ResponseGenerator(retriever, session_manager)

    session_id = "test_session_1"

    queries = [
        "What is the market price of Ragi in Mandya today?",
        "Will it rain in Tumkur today? I want to spray pesticides.",
        "I need a subsidy to build a farm pond, is there any government scheme?"
    ]

    for q in queries:
        print(f"\n=============================================")
        print(f"USER QUERY: {q}")
        print(f"=============================================")
        
        try:
            res = await generator.generate(session_id, q)
            print(f"\nBOT RESPONSE (Intent: {res.get('intent', 'Unknown')}):")
            print(res.get("response"))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_integrations())
