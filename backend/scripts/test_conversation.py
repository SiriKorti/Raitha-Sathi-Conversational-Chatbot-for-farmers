"""
test_conversation.py — Interactive Conversational Pipeline Test

WHAT IT DOES:
Provides a terminal-based chat interface to test the full "brain" of the 
assistant. It initializes the retriever and response generator and allows 
you to type Kannada questions and see the AI's response in real-time.

WHY IT EXISTS:
Speeds up development. Instead of launching the full FastAPI server and 
a web frontend, developers can use this script to instantly verify 
if a change in the RAG pipeline or LLM prompt improved the answers.

CONNECTIONS:
- Imports and orchestrates 'Retriever', 'SessionManager', and 
  'ResponseGenerator'.
"""

import sys
import io
import asyncio
import argparse
from pathlib import Path

# Force UTF-8 encoding on standard streams to prevent Kannada diacritics overlapping in terminal
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')
except AttributeError:
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stdin, 'buffer'):
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

def print_clean(*args, end="\n", flush=False):
    """Prints text by stripping markdown formatting and adding padding to emojis to prevent terminal overlap."""
    processed_args = []
    for arg in args:
        if isinstance(arg, str):
            # Remove markdown bold/italic tags that can interfere with combining characters
            cleaned = arg.replace("**", "").replace("*", "")
            # Pad emojis to create space for combining Kannada diacritics
            emojis = ["📂", "⚠️", "🌐", "✅", "🦙", "📌", "🌾", "🧠", "🤖"]
            for emoji in emojis:
                cleaned = cleaned.replace(emoji, f"{emoji}  ")
            processed_args.append(cleaned)
        else:
            processed_args.append(arg)
    print(*processed_args, end=end, flush=flush)

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all app modules first (they register loguru handlers during import)
from app.rag.retriever import Retriever
from app.conversation.session_manager import SessionManager
from app.llm.response_generator import ResponseGenerator
from app.utils.speech import record_speech, transcribe_speech, speak_text

# Logging is handled by app.utils.logger setup_logger() automatically.
# We keep standard console logging enabled so we can see internal logs during verification.


async def run_test_conversation(session_id: str = None):
    """
    Run a simulated multi-turn agricultural conversation.

    Tests:
    1. Session creation
    2. Follow-up question generation (missing crop name)
    3. Context accumulation across turns
    4. RAG retrieval and LLM response generation
    5. Conversation memory continuity

    Args:
        session_id: Optional fixed session ID (useful for debugging)
    """
    print("Starting up... please wait.")

    session_manager = SessionManager()
    retriever = Retriever()

    try:
        retriever.load()
    except Exception:
        pass

    gen = ResponseGenerator(retriever, session_manager)

    if session_id:
        session_manager.memory.create_session(session_id)
    else:
        session_id = session_manager.new_session()

    # ── Choose Interaction Mode ───────────────────────────────────────────────
    print("\nHow would you like to interact with Raitha Sathi?")
    print("1. Text Mode (Default)")
    print("2. Voice Mode (Uses microphone and speakers)")
    choice = input("\nEnter 1 or 2: ").strip()
    is_voice_mode = (choice == "2")

    # ── Interactive Conversation ──────────────────────────────────────────────
    if is_voice_mode:
        print("\nVoice Mode Activated! 🎙️")
        print("Type 'exit' when prompted to stop.")
    else:
        print("\nReady! Type your question in Kannada. Type 'exit' to stop.\n")

    while True:
        try:
            if is_voice_mode:
                record_result = record_speech()
                
                if record_result == "fallback":
                    user_input = input("\nYou (Fallback Text): ").strip()
                elif record_result == "record":
                    print("Transcribing...")
                    user_input = await transcribe_speech("recorded_audio.wav")
                    if not user_input:
                        print("Could not understand audio. Please try again.")
                        continue
                    print(f"You (Voice): {user_input}")
                else:
                    user_input = record_result
                    print(f"You (Typed): {user_input}")
            else:
                user_input = input("\nYou: ").strip()

            if user_input.lower() in ['exit', 'quit', 'ಸಾಕು']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            result = await gen.generate(
                session_id=session_id,
                user_query=user_input,
                is_voice_mode=is_voice_mode
            )

            source   = result.get("source", "llm")
            provider = result.get("provider", "ollama")
            response = result["response"]

            # ── Print source label, then the answer ───────────────────────────
            if source == "database":
                print_clean("\n✅ Answer found in database")
            elif provider == "gemini":
                print_clean("\n🌐 Fetching answer from Gemini...")
            elif provider == "ollama":
                print_clean("\n🦙 Fetching answer from Ollama...")
            else:
                print_clean("\n🤖 AI")

            print_clean(f"\n{response}\n")

            if is_voice_mode:
                speak_text(response)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test the conversational RAG pipeline"
    )
    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="Optional fixed session ID for testing"
    )
    args = parser.parse_args()
    asyncio.run(run_test_conversation(session_id=args.session_id))
