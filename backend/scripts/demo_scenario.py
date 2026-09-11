"""
demo_scenario.py — Interactive Demo for Raitha Sathi Enhanced Pipeline

This script runs a simulated command-line conversation to demonstrate:
1. Deep diagnostic follow-up questions
2. State-machine tracking
3. Emoji-structured actionable RAG responses
4. Farm Diary journey tracking
"""

import sys
import os
import asyncio

# Ensure app is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm.response_generator import ResponseGenerator
from app.conversation.session_manager import SessionManager
from app.rag.retriever import Retriever
from app.rag.embedder import Embedder
from app.utils.logger import logger

async def main():
    print("🌾" * 25)
    print("   RAITHA SATHI (ರೈತ ಸಾಥಿ) - INTELLIGENCE DEMO")
    print("🌾" * 25)
    
    session_manager = SessionManager()
    session_id = session_manager.new_session()
    
    retriever = Retriever()
    retriever.load()
    
    generator = ResponseGenerator(retriever, session_manager)
    
    # Pre-populate the profile
    session_manager.get_state(session_id).farmer_name = "Shraddha"
    
    print("\n[System]: Initialized new session for farmer 'Shraddha'\n")

    # Scenario: The farmer reports a generic symptom
    queries = [
        "Namaskara, I am growing Ragi. The leaves are turning yellow.",
        "It's mainly on the lower leaves. I don't see any insects.",
        "Yes, the soil is quite dry, haven't watered in 4 days.",
        "What about the same problem in Maize?"
    ]

    for i, q in enumerate(queries):
        print(f"👩🏽‍🌾 Farmer: {q}")
        print("-" * 50)
        
        response = await generator.generate(session_id, q, is_voice_mode=False)
        
        print(f"🤖 Raitha Sathi:\n{response['response']}\n")
        
        # Show internal state
        state = session_manager.get_state(session_id)
        print("🔍 [INTERNAL DIAGNOSTIC STATE]")
        print(f"Crop: {state.crop_name} | Symptoms: {state.symptoms}")
        print(f"Affected Part: {state.affected_part} | Pests Visible: {state.pest_visible}")
        print("-" * 50 + "\n")
        
        # Wait slightly to simulate realism and avoid rate limits
        await asyncio.sleep(2)
        
    print("📖 [FARM DIARY SUMMARY]")
    print(session_manager.diary.get_summary(session_id))
    print("🌾" * 25)

if __name__ == "__main__":
    asyncio.run(main())
