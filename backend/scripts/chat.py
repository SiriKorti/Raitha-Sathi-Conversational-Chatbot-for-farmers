r"""
chat.py — Conversational Terminal Chat for Kannada Agricultural Assistant
=========================================================================
Full conversational pipeline matching the production API:
  1. Session-aware DialogueState (crop / pest / intent memory across turns)
  2. LLM-based entity & intent extraction (pronoun resolution)
  3. Crop-locked DB search with LLM semantic verification
  4. FAISS semantic retrieval fallback
  5. Gemini → Ollama LLM generation fallback

Usage:
    ./venv/bin/python3 -X utf8 scripts/chat.py
"""

import sys
import os
import json
import asyncio
import io

# Force UTF-8 encoding on standard streams to prevent Kannada diacritics overlapping in terminal
try:
    if hasattr(sys.stdout, 'reconfigure'):
        getattr(sys.stdout, 'reconfigure')(encoding='utf-8')
    if hasattr(sys.stdin, 'reconfigure'):
        getattr(sys.stdin, 'reconfigure')(encoding='utf-8')
except Exception:
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

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("DATABASE_PATH", "database")

from app.rag.database_searcher import DatabaseSearcher
from app.rag.retriever import Retriever
from app.conversation.session_manager import SessionManager
from app.conversation.dialogue_state import DialogueState
from app.conversation.follow_up import FollowUpGenerator
from app.rag.context_builder import ContextBuilder
from app.llm.prompt_builder import PromptBuilder
from app.config import settings
from app.utils.speech import record_speech, transcribe_speech, speak_text, stop_speech, is_speaking


# ── Known crops in the database (Kannada + English keywords) ─────────────────
KNOWN_CROPS = {
    # Arecanut
    "ಅಡಿಕೆ": "ಅಡಿಕೆ (Arecanut)",
    "ಅಡಿಕೆಯ": "ಅಡಿಕೆ (Arecanut)",
    "ಅಡಿಕೆಗೆ": "ಅಡಿಕೆ (Arecanut)",
    "arecanut": "ಅಡಿಕೆ (Arecanut)",
    "areca": "ಅಡಿಕೆ (Arecanut)",
    "adike": "ಅಡಿಕೆ (Arecanut)",
    "adikey": "ಅಡಿಕೆ (Arecanut)",
    "adikege": "ಅಡಿಕೆ (Arecanut)",

    # Pearl Millet
    "ಸಜ್ಜೆ": "ಸಜ್ಜೆ (Pearl Millet)",
    "ಸಜ್ಜೆಯ": "ಸಜ್ಜೆ (Pearl Millet)",
    "ಸಜ್ಜೆಗೆ": "ಸಜ್ಜೆ (Pearl Millet)",
    "bajra": "ಸಜ್ಜೆ (Pearl Millet)",
    "pearl millet": "ಸಜ್ಜೆ (Pearl Millet)",
    "sajje": "ಸಜ್ಜೆ (Pearl Millet)",
    "sajjey": "ಸಜ್ಜೆ (Pearl Millet)",
    "sajjege": "ಸಜ್ಜೆ (Pearl Millet)",

    # Chickpea
    "ಕಡಲೆ": "ಕಡಲೆ (Chickpea)",
    "ಕಡಲೆಯ": "ಕಡಲೆ (Chickpea)",
    "ಕಡಲೆಗೆ": "ಕಡಲೆ (Chickpea)",
    "chickpea": "ಕಡಲೆ (Chickpea)",
    "bengal gram": "ಕಡಲೆ (Chickpea)",
    "chana": "ಕಡಲೆ (Chickpea)",
    "kadale": "ಕಡಲೆ (Chickpea)",
    "kadaley": "ಕಡಲೆ (Chickpea)",
    "kadalege": "ಕಡಲೆ (Chickpea)",

    # Coconut
    "ತೆಂಗು": "ತೆಂಗು (Coconut)",
    "ತೆಂಗಿನ": "ತೆಂಗು (Coconut)",
    "ತೆಂಗಿಗೆ": "ತೆಂಗು (Coconut)",
    "coconut": "ತೆಂಗು (Coconut)",
    "tengu": "ತೆಂಗು (Coconut)",
    "tengina": "ತೆಂಗು (Coconut)",
    "tengige": "ತೆಂಗು (Coconut)",
    "thengu": "ತೆಂಗು (Coconut)",

    # Coffee
    "ಕಾಫಿ": "ಕಾಫಿ (Coffee)",
    "ಕಾಫಿಯ": "ಕಾಫಿ (Coffee)",
    "ಕಾಫಿಗೆ": "ಕಾಫಿ (Coffee)",
    "coffee": "ಕಾಫಿ (Coffee)",
    "kafi": "ಕಾಫಿ (Coffee)",

    # Cotton
    "ಹತ್ತಿ": "ಹತ್ತಿ (Cotton)",
    "ಹತ್ತಿಯ": "ಹತ್ತಿ (Cotton)",
    "ಹತ್ತಿಗೆ": "ಹತ್ತಿ (Cotton)",
    "cotton": "ಹತ್ತಿ (Cotton)",
    "hatti": "ಹತ್ತಿ (Cotton)",
    "hattige": "ಹತ್ತಿ (Cotton)",

    # Groundnut
    "ಶೇಂಗಾ": "ಶೇಂಗಾ (Groundnut)",
    "ಶೇಂಗಾದ": "ಶೇಂಗಾ (Groundnut)",
    "ಶೇಂಗಾಗೆಗೆ": "ಶೇಂಗಾ (Groundnut)",
    "groundnut": "ಶೇಂಗಾ (Groundnut)",
    "peanut": "ಶೇಂಗಾ (Groundnut)",
    "shenga": "ಶೇಂಗಾ (Groundnut)",
    "shengad": "ಶೇಂಗಾ (Groundnut)",

    # Sorghum
    "ಜೋಳ": "ಜೋಳ (Sorghum)",
    "ಜೋಳದ": "ಜೋಳ (Sorghum)",
    "ಜೋಳಕ್ಕೆ": "ಜೋಳ (Sorghum)",
    "jowar": "ಜೋಳ (Sorghum)",
    "sorghum": "ಜೋಳ (Sorghum)",
    "jola": "ಜೋಳ (Sorghum)",
    "jolada": "ಜೋಳ (Sorghum)",

    # Maize
    "ಮೆಕ್ಕೆಜೋಳ": "ಮೆಕ್ಕೆಜೋಳ (Maize)",
    "ಮೆಕ್ಕೆಜೋಳದ": "ಮೆಕ್ಕೆಜೋಳ (Maize)",
    "ಮೆಕ್ಕೆಜೋಳಕ್ಕೆ": "ಮೆಕ್ಕೆಜೋಳ (Maize)",
    "maize": "ಮೆಕ್ಕೆಜೋಳ (Maize)",
    "corn": "ಮೆಕ್ಕೆಜೋಳ (Maize)",
    "mekkejola": "ಮೆಕ್ಕೆಜೋಳ (Maize)",
    "mekke jola": "ಮೆಕ್ಕೆಜೋಳ (Maize)",

    # Finger Millet
    "ರಾಗಿ": "ರಾಗಿ (Finger Millet)",
    "ರಾಗಿಯ": "ರಾಗಿ (Finger Millet)",
    "ರಾಗಿಗೆ": "ರಾಗಿ (Finger Millet)",
    "ragi": "ರಾಗಿ (Finger Millet)",
    "finger millet": "ರಾಗಿ (Finger Millet)",

    # Pigeon Pea
    "ತೊಗರಿ": "ತೊಗರಿ (Pigeon Pea)",
    "ತೊಗರಿಯ": "ತೊಗರಿ (Pigeon Pea)",
    "ತೊಗರಿಗೆ": "ತೊಗರಿ (Pigeon Pea)",
    "redgram": "ತೊಗರಿ (Pigeon Pea)",
    "pigeon pea": "ತೊಗರಿ (Pigeon Pea)",
    "togari": "ತೊಗರಿ (Pigeon Pea)",

    # Rice / Paddy
    "ಭತ್ತ": "ಭತ್ತ (Rice / Paddy)",
    "ಭತ್ತದ": "ಭತ್ತ (Rice / Paddy)",
    "ಭತ್ತಕ್ಕೆ": "ಭತ್ತ (Rice / Paddy)",
    "rice": "ಭತ್ತ (Rice / Paddy)",
    "paddy": "ಭತ್ತ (Rice / Paddy)",
    "bhatta": "ಭತ್ತ (Rice / Paddy)",
    "bhattada": "ಭತ್ತ (Rice / Paddy)",

    # Sugarcane
    "ಕಬ್ಬು": "ಕಬ್ಬು (Sugarcane)",
    "ಕಬ್ಬಿನ": "ಕಬ್ಬು (Sugarcane)",
    "ಕಬ್ಬಿಗೆ": "ಕಬ್ಬು (Sugarcane)",
    "ಕಬ್ಬಿನಲ್ಲಿ": "ಕಬ್ಬು (Sugarcane)",
    "sugarcane": "ಕಬ್ಬು (Sugarcane)",
    "kabbu": "ಕಬ್ಬು (Sugarcane)",
    "kabbina": "ಕಬ್ಬು (Sugarcane)",

    # Sunflower
    "ಸೂರ್ಯಕಾಂತಿ": "ಸೂರ್ಯಕಾಂತಿ (Sunflower)",
    "ಸೂರ್ಯಕಾಂತಿಯ": "ಸೂರ್ಯಕಾಂತಿ (Sunflower)",
    "ಸೂರ್ಯಕಾಂತಿಗೆ": "ಸೂರ್ಯಕಾಂತಿ (Sunflower)",
    "sunflower": "ಸೂರ್ಯಕಾಂತಿ (Sunflower)",
    "suryakanthi": "ಸೂರ್ಯಕಾಂತಿ (Sunflower)",
    "suryakanti": "ಸೂರ್ಯಕಾಂತಿ (Sunflower)",

    # Turmeric
    "ಅರಿಶಿನ": "ಅರಿಶಿನ (Turmeric)",
    "ಅರಿಶಿನದ": "ಅರಿಶಿನ (Turmeric)",
    "ಅರಿಶಿನಕ್ಕೆ": "ಅರಿಶಿನ (Turmeric)",
    "turmeric": "ಅರಿಶಿನ (Turmeric)",
    "haldi": "ಅರಿಶಿನ (Turmeric)",
    "arishina": "ಅರಿಶಿನ (Turmeric)",
    "arisina": "ಅರಿಶಿನ (Turmeric)",
}


def detect_crop(query: str) -> tuple[str | None, bool]:
    """
    Detect if the query mentions a crop.
    Returns (crop_full_name, is_in_database).
    If no crop detected, returns (None, True).
    """
    q_lower = query.lower()

    # Check known crops first
    for keyword, full_name in KNOWN_CROPS.items():
        if keyword.lower() in q_lower:
            return full_name, True

    # Check for crops NOT in the database (common Karnataka crops)
    unknown_crops = {
        "ಮೆಣಸಿನಕಾಯಿ": "ಮೆಣಸಿನಕಾಯಿ (Chilli)",
        "ಮೆಣಸಿನ ಕಾಯಿ": "ಮೆಣಸಿನಕಾಯಿ (Chilli)",
        "chilli": "Chilli",
        "chili": "Chilli",
        "capsicum": "Capsicum",
        "ಟೊಮ್ಯಾಟೊ": "ಟೊಮ್ಯಾಟೊ (Tomato)",
        "ಟೊಮೇಟೊ": "ಟೊಮ್ಯಾಟೊ (Tomato)",
        "ಟೊಮೆಟೊ": "ಟೊಮ್ಯಾಟೊ (Tomato)",
        "tomato": "Tomato",
        "ಈರುಳ್ಳಿ": "ಈರುಳ್ಳಿ (Onion)",
        "onion": "Onion",
        "ಬದನೆ": "ಬದನೆ (Brinjal)",
        "brinjal": "Brinjal",
        "eggplant": "Eggplant",
        "ಆಲೂಗಡ್ಡೆ": "ಆಲೂಗಡ್ಡೆ (Potato)",
        "ಆಲೂಗೆಡ್ಡೆ": "ಆಲೂಗಡ್ಡೆ (Potato)",
        "potato": "Potato",
        "ಬೆಳ್ಳುಳ್ಳಿ": "ಬೆಳ್ಳುಳ್ಳಿ (Garlic)",
        "garlic": "Garlic",
        "ಶುಂಠಿ": "ಶುಂಠಿ (Ginger)",
        "ginger": "Ginger",
        "ಮಾವು": "ಮಾವು (Mango)",
        "mango": "Mango",
        "ಬಾಳೆ": "ಬಾಳೆ (Banana)",
        "banana": "Banana",
        "ದ್ರಾಕ್ಷಿ": "ದ್ರಾಕ್ಷಿ (Grape)",
        "grape": "Grape",
        "ಅರಟ": "ಅರಟ (Betel Vine)",
        "betel": "Betel Vine",
        "ಗೋಧಿ": "ಗೋಧಿ (Wheat)",
        "wheat": "Wheat",
        "ಸೋಯಾ": "ಸೋಯಾ (Soybean)",
        "soybean": "Soybean",
        "soya": "Soybean",
        "ಖರ್ಜೂರ": "ಖರ್ಜೂರ (Dates)",
        "dates": "Dates",
        "date palm": "Dates",
        "ಗೇರು": "ಗೇರು (Cashew)",
        "cashew": "Cashew",
        "cashewnut": "Cashew",
        "ಅವಕಾಡೊ": "ಅವಕಾಡೊ (Avocado)",
        "avocado": "Avocado",
        "butter fruit": "Avocado",
        "ಕಿವಿ": "ಕಿವಿ (Kiwi)",
        "ಕಿವಿಯ": "ಕಿವಿ (Kiwi)",
        "ಕಿವಿಗೆ": "ಕಿವಿ (Kiwi)",
        "kiwi": "Kiwi",
        "ಸೇಬು": "ಸೇಬು (Apple)",
        "apple": "Apple",
        "ಪಪಾಯ": "ಪಪಾಯ (Papaya)",
        "papaya": "Papaya",
        "ಕಲ್ಲಂಗಡಿ": "ಕಲ್ಲಂಗಡಿ (Watermelon)",
        "watermelon": "Watermelon",
    }
    for keyword, full_name in unknown_crops.items():
        if keyword.lower() in q_lower:
            return full_name, False

    from app.utils.text_utils import extract_crop_from_text
    extracted = extract_crop_from_text(query)
    if extracted:
        is_known = any(extracted.lower() in k.lower() or k.lower() in extracted.lower() for k in KNOWN_CROPS.keys())
        return extracted, is_known

    return None, True  # No specific crop detected → search all


def print_banner():
    print_clean("\n" + "=" * 60)
    print_clean("   ಕನ್ನಡ ಕೃಷಿ ಸಹಾಯಕ  (Kannada Agri Assistant)")
    print_clean("=" * 60)
    print_clean("  Database: 1500 Q&A | 15 crops | Karnataka")
    print_clean("  Type your question in Kannada or English")
    print_clean("  Interactive Commands:")
    print_clean("    '1' or 'text'  = Switch to Text Mode ⌨️")
    print_clean("    '2' or 'voice' = Switch to Voice Mode 🎙️")
    print_clean("    'q' or 'exit'  = End conversation 🚪")
    print_clean("    'list'         = Show supported crops 🌾")
    print_clean("=" * 60)


def print_crops():
    crops = sorted(KNOWN_CROPS.values())
    unique = sorted(set(crops))
    print_clean("\n  Crops in database:")
    for i, c in enumerate(unique, 1):
        print_clean(f"   {i:2}. {c}")
    print_clean()


def extract_farmer_name(text: str) -> str | None:
    """
    Detect if the farmer is introducing themselves and extract their name.
    Handles patterns like: 'I am Karan', 'my name is Ravi', 'I'm Priya',
    'hello I'm Suresh', 'hi I am Ganesh', 'nanna hesaru Ramesh', 'namaskara nanu Isha'.
    Returns the capitalized name, or None if not detected.
    """
    import re
    text = text.strip()

    stopwords = {
        "a", "an", "the", "farmer", "here", "there", "ok", "fine", "good", "great", "from", "new", "doing",
        "afraid", "facing", "having", "trying", "growing", "planning", "looking", "suffering",
        "getting", "using", "asking", "wondering", "thinking", "worried", "confused", "interested",
        "ready", "happy", "sad", "curious", "searching", "scared", "sure", "unsure", "able", "unable",
        "sorry", "glad", "just", "also", "very", "so", "too", "not", "going"
    }

    # 1. Explicit English name introduction phrases
    patterns_explicit = [
        r"(?:my name is|call me|this is|it's me,?)\s+([A-Za-z]{2,20})\b",
    ]
    for pat in patterns_explicit:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip().capitalize()
            if name.lower() not in stopwords and len(name) >= 2:
                return name

    # 2. English "I am [Name]" / "I'm [Name]" / "im [Name]" (handles 'hello there,im sia', 'hi there im karan', etc.)
    patterns_en_intro = [
        r"(?:hello|hi|hey|good morning|good evening|good afternoon)?\s*(?:there)?[,!\s]*(?:i am|i'm|im)\s+([A-Za-z]{2,20})\b(?!\s+(?:to|facing|having|trying|growing|planning|looking|suffering|getting|using|asking|wondering|thinking|about|worried|afraid|doing|from))",
    ]
    for pat in patterns_en_intro:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip().capitalize()
            if name.lower() not in stopwords and len(name) >= 2:
                return name

    # 3. Kannada name introduction patterns
    patterns_kn = [
        r"(?:ನನ್ನ ಹೆಸರು|ನನ್ನ ಹೆಸರು:?)\s+([\u0C80-\u0CFF]{2,20}|[A-Za-z]{2,20})",
        r"^(?:ನಮಸ್ಕಾರ|ಹಲೋ|ಹಾಯ್)[,!\s]+ನಾನು\s+([\u0C80-\u0CFF]{2,20}|[A-Za-z]{2,20})",
        r"^ನಾನು\s+([\u0C80-\u0CFF]{2,20}|[A-Za-z]{2,20})$",
    ]
    for pat in patterns_kn:
        m = re.search(pat, text)
        if m:
            name = m.group(1).strip().capitalize()
            if name.lower() not in stopwords and len(name) >= 2:
                return name

    return None


# ── Gemini models to try in order ────────────────────────────────────────────
GEMINI_MODELS = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-flash-latest"]


def ask_gemini(query: str, crop_name: str = "", farmer_name: str = "", is_voice_mode: bool = False, history: list = None) -> tuple[str, str]:
    """
    Fetch answer from Gemini AI using strict Krishi Mitra persona.
    Step 1: Classify if the query is agriculture-related.
    Step 2: If YES → answer with mandatory disclaimer.
    Step 3: If NO  → return hardcoded language-appropriate rejection message.
    Returns (answer_text, model_name_used).
    """
    from google import genai
    from google.genai import types

    if not settings.GEMINI_API_KEY:
        return "⚠️ GEMINI_API_KEY is not configured.", "none"

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    target_model = settings.GEMINI_MODEL

    # ── Detect language & define messages ────────────────────────────────────
    is_english = any(ord(c) < 128 and c.isalpha() for c in query)
    
    if is_english:
        REJECTION_MESSAGE = (
            "Hello dear farmer! 🌾 I am Raitha Sathi, your personal agricultural AI assistant. "
            "I am specialized in helping with farming practices, crops, pests, diseases, fertilizers, "
            "irrigation, and soil health. Please ask any agriculture-related question, and I will be glad to help you!"
        )
        disclaimer = "🌐 *This topic is not in our verified database — here is what Raitha Sathi knows from general agricultural knowledge:*\n\n"
    else:
        REJECTION_MESSAGE = (
            "ನಮಸ್ಕಾರ ರೈತ ಬಾಂಧವರೇ! 🌾 ನಾನು ನಿಮ್ಮ 'ರೈತ ಸಾಥಿ' ವೈಯಕ್ತಿಕ ಕೃಷಿ ಸಹಾಯಕ. "
            "ನಾನು ಕೇವಲ ಕೃಷಿ, ಬೆಳೆಗಳ ರಕ್ಷಣೆ, ರೋಗ ನಿಯಂತ್ರಣ, ಮಣ್ಣು ಮತ್ತು ನೀರಾವರಿ ವಿಷಯಗಳಲ್ಲಿ ಸಹಾಯ ಮಾಡಲು ಇರುವುದು. "
            "ದಯವಿಟ್ಟು ಕೃಷಿಗೆ ಸಂಬಂಧಿಸಿದ ಯಾವುದೇ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ, ನಾನು ಅತ್ಯಂತ ಪ್ರೀತಿಯಿಂದ ಉತ್ತರಿಸುತ್ತೇನೆ!"
        )
        disclaimer = "🌐 *ಈ ವಿಷಯ ನಮ್ಮ ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ನೇರವಾಗಿ ಇಲ್ಲ — ರೈತ ಸಾಥಿ ತನ್ನ ಸಾಮಾನ್ಯ ಕೃಷಿ ಜ್ಞಾನದಿಂದ ಉತ್ತರ ನೀಡುತ್ತಿದ್ದಾನೆ:*\n\n"

    # ── Step 1: Strict YES/NO topic classification ───────────────────────────
    non_agri_keywords = [
        "python", "java", "coding", "programmer", "code", "software", "script", "movie", "cinema",
        "actor", "actress", "film", "song", "music", "cricket", "football", "match", "ipl",
        "politics", "minister", "president", "prime minister", "election", "capital of",
        "who is", "who was", "math", "formula", "equation", "calculator", "recipe", "cake",
        "pizza", "burger", "joke", "tell me a joke", "game", "gaming", "html", "css", "javascript",
        "c++", "c#", "react", "node", "angular", "hero", "heroine", "modi", "rahul",
        "drink", "beverage", "cook", "cooking", "how to make coffee", "how to make tea", "how to prepare coffee",
        "ವಿಮಾನ", "ಸಿನಿಮಾ", "ರಾಜಕೀಯ", "ನಟ", "ನಟಿ", "ಆಟ", "ಕ್ರಿಕೆಟ್", "ಖಾತೆ", "ಪಾಸ್‌ವರ್ಡ್", "ಹಾಡು",
        "ಚಿತ್ರ", "ಕಥೆ", "ಮಂತ್ರಿ", "ಮುಖ್ಯಮಂತ್ರಿ", "ಪ್ರಧಾನಿ", "ಚುನಾವಣೆ", "ಕಾರು", "ಬೈಕ್", "ಮೊಬೈಲ್", "ಫೋನ್",
        "ತಯಾರಿಸುವುದು ಹೇಗೆ", "ತಯಾರಿಸಬೇಕು", "ಪಾಕವಿಧಾನ", "ಅಡುಗೆ", "ಕುಡಿಯಲು", "ಕಾಫಿ ಮಾಡುವುದು ಹೇಗೆ", "ಟೀ ಮಾಡುವುದು ಹೇಗೆ", "ಜ್ಯೂಸ್"
    ]
    agri_keywords = [
        "cultivat", "plant", "grow", "agri", "farm", "soil", "pest", "disease", "fertiliz",
        "water", "yield", "seed", "nursery", "sapling", "graft", "propagat", "harvest",
        "fruit", "vegetable", "field", "irrigation", "crop", "paddy", "arecanut", "maize",
        "rice", "ragi", "cotton", "coffee", "coconut", "sugarcane", "turmeric", "jowar",
        "bajra", "groundnut", "chickpea", "pigeon", "pigeonpea", "sunflower",
        "grape", "grapes", "mango", "banana", "chilli", "chili", "tomato", "onion", "potato",
        "garlic", "ginger", "wheat", "cashew", "apple", "papaya", "pineapple", "lemon", "betel",
        "avocado", "pomegranate", "dragon", "dragonfruit", "sweet", "color", "colour",
        "ಬೆಳೆ", "ಕೃಷಿ", "ಮಣ್ಣು", "ಕೀಟ", "ರೋಗ", "ಗೊಬ್ಬರ", "ಬೀಜ", "ಅಡಿಕೆ", "ರಾಗಿ", "ಭತ್ತ",
        "ಕಬ್ಬು", "ಕಬ್ಬಿನಲ್ಲಿ", "ಕಬ್ಬಿನ", "ಕಬ್ಬಿಗೆ", "ತೆಂಗು", "ತೆಂಗಿನಲ್ಲಿ", "ತೆಂಗಿನ", "ತೆಂಗಿಗೆ",
        "ಹತ್ತಿ", "ಹತ್ತಿಯಲ್ಲಿ", "ಹತ್ತಿಯ", "ಹತ್ತಿಗೆ", "ಕಾಫಿ", "ಕಾಫಿಯಲ್ಲಿ", "ಕಾಫಿಯ", "ಕಾಫಿಗೆ",
        "ಶೇಂಗಾ", "ಶೇಂಗಾದಲ್ಲಿ", "ಶೇಂಗಾದ", "ಮೆಕ್ಕೆಜೋಳ", "ಮೆಕ್ಕೆಜೋಳದಲ್ಲಿ", "ಮೆಕ್ಕೆಜೋಳದ",
        "ಅರಿಶಿನ", "ಅರಿಶಿನದಲ್ಲಿ", "ಅರಿಶಿನದ", "ಸಜ್ಜೆ", "ಸಜ್ಜೆಯಲ್ಲಿ", "ಸಜ್ಜೆಯ",
        "ಕಡಲೆ", "ಕಡಲೆಯಲ್ಲಿ", "ಕಡಲೆಯ", "ತೊಗರಿ", "ತೊಗರಿಯಲ್ಲಿ", "ತೊಗರಿಯ",
        "ಜೋಳ", "ಜೋಳದಲ್ಲಿ", "ಜೋಳದ", "ಸೂರ್ಯಕಾಂತಿ", "ಸೂರ್ಯಕಾಂತಿಯಲ್ಲಿ", "ಸೂರ್ಯಕಾಂತಿಯ",
        "ಸಸಿ", "ನರ್ಸರಿ", "ಕಸಿ", "ಉತ್ಪಾದನೆ", "ತೋಟ", "ಬೇಸಾಯ", "ಇಳುವರಿ", "ಕೊಯ್ಲು", "ಸಾಗುವಳಿ", "ಹಣ್ಣು", "ತರಕಾರಿ",
        "ದ್ರಾಕ್ಷಿ", "ಮಾವು", "ಬಾಳೆ", "ಮೆಣಸಿನಕಾಯಿ", "ಟೊಮ್ಯಾಟೊ", "ಈರುಳ್ಳಿ", "ಆಲೂಗಡ್ಡೆ", "ಬೆಳ್ಳುಳ್ಳಿ",
        "ಶುಂಠಿ", "ಗೋಧಿ", "ಗೇರು", "ಸೇಬು", "ಪಪ್ಪಾಯಿ", "ಅನಾನಸ್", "ನಿಂಬೆ", "ಅರಟ", "ದಾಳಿಂಬೆ", "ಬದನೆ", "ಕೊತ್ತಂಬರಿ",
        "ನೀರಾವರಿ", "ಹನಿ", "ಸಬ್ಸಿಡಿ", "ಸಾಲು", "ಪೋಷಕಾಂಶ",
        # Market / APMC / trade keywords
        "ಎಪಿಎಂಸಿ", "ಮಾರುಕಟ್ಟೆ", "ಮಾರಾಟ", "ಧಾನ್ಯ", "ಬೆಲೆ", "ಖರೀದಿ", "ಸಂಗ್ರಹ", "ಗೋದಾಮು",
        "apmc", "market", "selling", "grain", "storage", "price", "msp",
    ]
    q_lower = query.lower()
    has_non_agri = any(kw in q_lower for kw in non_agri_keywords)
    has_agri = any(akw in q_lower for akw in agri_keywords)

    if has_non_agri and not has_agri:
        return REJECTION_MESSAGE, "rule"

    classification_prompt = (
        "You are a strict topic classifier. Respond with ONLY the single word YES or NO.\n\n"
        "Is the following question related to agriculture, farming, crops, "
        "plant diseases, pests, fertilizers, irrigation, soil, livestock, "
        "or agricultural market practices?\n\n"
        f"Question: \"{query}\"\n\n"
        "Answer (YES or NO only):"
    )

    # Optimization: Skip LLM classification API call if query clearly lacks non-agricultural keywords
    is_agriculture = True
    if has_non_agri:
        try:
            cls_resp = client.models.generate_content(
                model=target_model,
                contents=classification_prompt,
                config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=5)
            )
            if cls_resp and cls_resp.text:
                text_resp = cls_resp.text.strip().upper()
                if "NO" in text_resp:
                    is_agriculture = False
        except Exception:
            pass

    # ── Step 2: Reject non-agriculture immediately ───────────────────────────
    if not is_agriculture:
        return REJECTION_MESSAGE, "classifier"

    # ── Step 3: Agriculture query → answer with prompt ────────────────────────
    crop_ctx = f"Target Crop: {crop_name}." if crop_name else ""
    name_ctx = f"Farmer's Name: {farmer_name}." if farmer_name else ""
    
    target_lang = "English" if is_english else "Kannada"

    base_persona = (
        "You are Raitha Sathi (ರೈತ ಸಾಥಿ) — a sweet, warm, caring personal agricultural assistant for Karnataka farmers. "
        "Speak with exceptional intelligence, kindness, and meticulous adherence to these behaviors:\n\n"
        "1. TONE & EMPATHY: Be warm, respectful, patient, and encouraging. ALWAYS address the user strictly as 'Dear Farmer' (or 'ರೈತ ಬಾಂಧವರೇ' in Kannada). DO NOT use familial or regional terms like 'Anna' (ಅಣ್ಣ), 'Akka' (ಅಕ್ಕ), etc. Do NOT include conversational filler like 'I am happy to help you' or 'It is nice you showed interest'—just get straight to the agricultural point with warmth. If they express distress (crop loss, debt, weather stress), ALWAYS start with a brief genuine empathetic line before giving practical steps. Be humble about your limits.\n"
        "2. CONVERSATIONAL STYLE: Never be robotic. Avoid jargon. Ask ONE clarifying question at a time if the query is ambiguous. Celebrate their small wins. Always end practical answers with a caring check-in (e.g., 'Does this help? Let me know how it goes.').\n"
        "3. STRUCTURE: Explain simply: what to do, how much, when, and safety cautions—in that order.\n"
        "4. LANGUAGE BEHAVIOR: Mirror their language. If they mix Kannada and English, mirror that code-switching. Use everyday spoken Kannada vocabulary (like a friendly local extension officer), NOT stiff formal Kannada. If translating, preserve all dosages and facts exactly.\n"
        "5. SAFETY BOUNDARIES: NEVER recommend banned chemicals. ALWAYS include safety cautions (protective gear, keeping away from children) when discussing chemicals. Recommend local officers for severe disease diagnosis. Do not give financial, legal, or land-dispute advice. For serious personal crises or self-harm risks, respond with extreme warmth and urgently suggest human helplines.\n"
        "6. SCOPE RULES: Naturally answer greetings and personal queries (e.g., 'how are you', 'thank you'). However, if asked ANY out-of-context or non-agricultural question (politics, movies, tech), kindly and sweetly decline, steering back to agriculture.\n"
    )

    if is_voice_mode:
        system_instruction = base_persona + (
            "\nCRITICAL VOICE RULES:\n"
            "- Speak in short, natural spoken rhythm (2-4 sentences max per turn). Avoid long compound sentences.\n"
            "- DO NOT read out symbols (*, #, etc.), bullet points, or markdown. Convert lists into flowing spoken phrases ('First, do this. Then, do that.').\n"
            "- State numbers, prices, and dates clearly since they are read aloud.\n"
            f"- Speak fluently in {target_lang} (mirroring code-switching if present).\n"
        )
        max_tokens = 250
    else:
        system_instruction = base_persona + (
            "\nCRITICAL TEXT RULES:\n"
            "- Keep the response short, sweet, kind, and strictly under 4-5 sentences max, using simple structure.\n"
            "- You may use light formatting (short bullet points, bold key terms) since this will be read, not heard. Break into short, scannable lines.\n"
            f"- Write fluently in {target_lang} (mirroring code-switching if present).\n"
        )
        max_tokens = 300

    history_block = ""
    if history:
        for turn in history:
            role = "Farmer" if turn.get('role') == 'user' else "Raitha Sathi"
            history_block += f"{role}: {turn.get('content')}\n"

    if is_english:
        prompt = f"Context: {crop_ctx} {name_ctx}\n"
        if history_block:
            prompt += f"Recent Conversation History:\n{history_block}\n"
        prompt += f"Farmer's Question: \"{query}\"\nResponse:"
    else:
        prompt = f"ಸಂದರ್ಭ: {crop_ctx} {name_ctx}\n"
        if history_block:
            prompt += f"ಇತ್ತೀಚಿನ ಸಂಭಾಷಣೆ:\n{history_block}\n"
        prompt += f"ರೈತರ ಪ್ರಶ್ನೆ: \"{query}\"\nಉತ್ತರ:"

    if is_english:
        disclaimer = "⚠️ *This question is not in our database. The following answer is generated by AI based on general agricultural knowledge:*\n\n"
    else:
        disclaimer = "⚠️ *ಈ ಪ್ರಶ್ನೆಗೆ ನಮ್ಮ ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ನೇರ ಉತ್ತರ ಲಭ್ಯವಿಲ್ಲ. ಕೆಳಗಿನ ಉತ್ತರವನ್ನು ಸಾಮಾನ್ಯ ಕೃಷಿ ಜ್ಞಾನದ ಆಧಾರದ ಮೇಲೆ AI ಮೂಲಕ ನೀಡಲಾಗಿದೆ:*\n\n"

    def strip_response(raw_ans: str) -> str:
        """Strip any duplicate disclaimer lines from a model response."""
        ans = raw_ans.strip()
        disclaimer_clean_kn = "⚠️ ಈ ಪ್ರಶ್ನೆಗೆ ನಮ್ಮ ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ನೇರ ಉತ್ತರ ಲಭ್ಯವಿಲ್ಲ."
        disclaimer_clean_en = "⚠️ This question is not directly available in our database."
        if ans.startswith(disclaimer_clean_kn) or ans.startswith(disclaimer_clean_en):
            lines = ans.splitlines()
            ans = "\n".join(lines[1:]).strip()
        elif ans.startswith("⚠️"):
            lines = ans.splitlines()
            if lines and ("ಡೇಟಾಬೇಸ್" in lines[0] or "database" in lines[0].lower()):
                ans = "\n".join(lines[1:]).strip()
        return ans

    def clean_response(raw_ans: str) -> str:
        """Strip duplicate disclaimers and return the clean text."""
        return strip_response(raw_ans)

    import time, re
    for attempt in range(4):
        try:
            res = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2, 
                    max_output_tokens=max_tokens
                )
            )
            if res and res.candidates:
                raw_text = ""
                first_cand = res.candidates[0]
                if hasattr(first_cand, "content") and first_cand.content and hasattr(first_cand.content, "parts"):
                    raw_text = "".join(p.text for p in first_cand.content.parts if hasattr(p, "text") and p.text)
                if not raw_text and hasattr(res, "text"):
                    try:
                        raw_text = res.text
                    except Exception:
                        pass
                if raw_text and raw_text.strip():
                    return clean_response(raw_text or ""), f"Gemini ({target_model})"
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str, re.IGNORECASE)
                wait_sec = min(float(match.group(1)) if match else 5.0, 15.0)
                wait_sec = max(wait_sec, 2.0)
                if attempt < 3:
                    print(f"   [Gemini rate limited — waiting {int(wait_sec)}s before retry {attempt+1}/3...]", flush=True)
                    time.sleep(wait_sec)
                    continue
            else:
                print(f"   [Gemini call notice: {e}]", flush=True)
            break

    # ── Step 4: Offline / Gemini Exhausted Fallback → Local Ollama ────────────
    print("   [Gemini API unavailable or rate-limited — falling back to local Ollama...]", flush=True)

    def _ask_ollama(ollama_prompt: str) -> str:
        """Send a prompt to local Ollama and return the response text, or empty string."""
        try:
            import urllib.request
            ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
            payload = json.dumps({
                "model": settings.OLLAMA_MODEL,
                "prompt": ollama_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "repeat_penalty": 1.1,
                    "top_p": 0.90,
                    "top_k": 40,
                    "num_predict": 400
                }
            }).encode("utf-8")
            req = urllib.request.Request(ollama_url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return res_data.get("response", "").strip()
        except Exception:
            return ""

    is_kannada_query = not is_english

    if not is_kannada_query:
        # English query — just ask Ollama directly
        ollama_ans = _ask_ollama(prompt)
        if ollama_ans:
            return clean_response(ollama_ans), f"Ollama ({settings.OLLAMA_MODEL})"
    else:
        # Kannada query — try Kannada prompt, then validate quality strictly
        ollama_ans = _ask_ollama(prompt)
        if ollama_ans:
            kannada_chars = sum(1 for c in ollama_ans if '\u0C80' <= c <= '\u0CFF')
            total_alpha = sum(1 for c in ollama_ans if c.isalpha())
            # Strict checks: >60% Kannada chars, >50 chars total, no zero-width/math junk
            has_enough_kannada = total_alpha > 0 and (kannada_chars / total_alpha) >= 0.60
            is_long_enough = len(ollama_ans.strip()) >= 50
            has_junk = '\u200d' in ollama_ans or '\u200c' in ollama_ans or '=(3' in ollama_ans or '*1000' in ollama_ans
            if has_enough_kannada and is_long_enough and not has_junk:
                return strip_response(ollama_ans), f"Ollama ({settings.OLLAMA_MODEL})"

        # Kannada model failed — use a keyword map to extract English topic from Kannada query
        # Categories: SUBJECT (what the question is about) and ATTRIBUTE (what aspect is asked)
        SUBJECT_MAP = {
            "ಡ್ರೋನ್": "agricultural drone",
            "ಕ್ರಿಮಿನಾಶಕ": "pesticide spraying",
            "ಕೀಟನಾಶಕ": "insecticide application",
            "ನೀರಾವರಿ": "irrigation system",
            "ಬಿತ್ತನೆ": "seed sowing",
            "ಕಟಾವು": "crop harvesting",
            "ಸಂಗ್ರಹ": "post-harvest storage",
            "ಗೊಬ್ಬರ": "manure and composting",
            "ಸಾವಯವ": "organic farming",
            "ಮಿಶ್ರ ಬೆಳೆ": "mixed cropping",
            "ಅಂತರ ಬೆಳೆ": "intercropping",
            "ಮಣ್ಣು ಪರೀಕ್ಷೆ": "soil testing",
            "ಹಿಟ್ಟು": "flour milling from millets",
            "ಸಂಸ್ಕರಣೆ": "crop processing and value addition",
            "ವಿಮೆ": "crop insurance",
            "ಸಾಲ": "agricultural loans",
            "ಕಸಿ": "plant grafting technique",
        }
        ATTRIBUTE_MAP = {
            "ರಸಗೊಬ್ಬರ": "fertilizer application",
            "ಸಿಂಪಡಿಸು": "spraying method",
            "ನಿಯಮ": "rules and government regulations",
            "ಮುನ್ನೆಚ್ಚರಿಕೆ": "safety precautions",
            "ರೋಗ": "disease management",
            "ಕೀಟ": "pest control",
            "ಇಳುವರಿ": "yield improvement",
            "ಮಣ್ಣು": "soil health management",
            "ಹವಾಮಾನ": "climate adaptation",
            "ಬರ": "drought management",
            "ಬೆಲೆ": "market pricing",
            "ಬೀಜ": "seed selection",
            "ತಳಿ": "variety selection",
            "ಯಂತ್ರ": "machinery and equipment use",
        }

        subjects = [v for k, v in SUBJECT_MAP.items() if k in query]
        attributes = [v for k, v in ATTRIBUTE_MAP.items() if k in query]

        if subjects and attributes:
            english_question = (
                f"What are the {' and '.join(attributes)} guidelines, "
                f"rules, and safety precautions for using {' and '.join(subjects)} "
                f"in Karnataka agriculture?"
            )
        elif subjects:
            english_question = f"What are the best practices, regulations, and safety guidelines for {' and '.join(subjects)} in Karnataka agriculture?"
        elif attributes:
            english_question = f"What are the detailed {' and '.join(attributes)} guidelines and safety precautions for Karnataka farmers?"
        else:
            english_question = "What are the important guidelines, rules, and safety precautions that Karnataka farmers should follow for this agricultural activity?"

        # Ask Ollama in English using the specific reconstructed question
        english_prompt = (
            f"You are an expert agricultural advisor for Karnataka, India.\n"
            f"Answer ONLY the following specific question. Do not change the topic.\n"
            f"Provide step-by-step methods, rules, timing, dosage, and safety precautions.\n"
            f"Do NOT ask any clarifying questions. Give a complete direct answer.\n\n"
            f"Question: {english_question}\n\n"
            f"Answer:"
        )
        ollama_ans_en = _ask_ollama(english_prompt)
        if ollama_ans_en:
            # Strip any leaked disclaimer lines from Ollama output
            clean_lines = [
                line for line in ollama_ans_en.splitlines()
                if not line.strip().startswith("\u26a0\ufe0f") and "\u0ca1\u0cc7\u0c9f\u0cbe\u0cac\u0cc7\u0cb8\u0ccd" not in line
            ]
            ollama_ans_en = "\n".join(clean_lines).strip()
        if ollama_ans_en:
            note = (
                "\U0001f4cc *\u0c95\u0ca8\u0ccd\u0ca8\u0ca1 AI \u0cb8\u0cc7\u0cb5\u0cc6 \u0ca4\u0cbe\u0ca4\u0ccd\u0c95\u0cbe\u0cb2\u0cbf\u0c95\u0cb5\u0cbe\u0c97\u0cbf \u0cb2\u0cad\u0ccd\u0caf\u0cb5\u0cbf\u0cb2\u0ccd\u0cb2. \u0c95\u0cc6\u0cb3\u0c97\u0cbf\u0ca8 \u0c89\u0ca4\u0ccd\u0ca4\u0cb0 \u0c87\u0c82\u0c97\u0ccd\u0cb2\u0cbf\u0cb7\u0ccd\u200c\u0ca8\u0cb2\u0ccd\u0cb2\u0cbf \u0c92\u0ca6\u0c97\u0cbf\u0cb8\u0cb2\u0cbe\u0c97\u0cbf\u0ca6\u0cc6:*\n"
                "*(Kannada AI temporarily unavailable. Answer provided in English below:)*\n\n"
            )
            return note + ollama_ans_en, f"Ollama ({settings.OLLAMA_MODEL})"

    return "ಕ್ಷಮಿಸಿ, ಈ ಸಮಯದಲ್ಲಿ AI ಸೇವೆ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.", "none"


def fetch_and_print_ai(query: str, crop_name: str = "", farmer_name: str = "", speak: bool = False, history: list = None):
    # Determine if it is an English query
    is_english = any(ord(c) < 128 and c.isalpha() for c in query)
    # Show a fetching notice immediately before waiting for the model
    if is_english:
        print_clean("\n🌐 [Question not in database. Fetching answer from AI model...]\n", flush=True)
    else:
        print_clean("\n🌐 [ಪ್ರಶ್ನೆಯು ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ಲಭ್ಯವಿಲ್ಲ. AI ಮಾದರಿ ಮೂಲಕ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ...]\n", flush=True)

    ans, model_used = ask_gemini(query, crop_name, farmer_name, is_voice_mode=speak, history=history)

    if model_used in ["classifier", "rule"]:
        print_clean(f"\n{ans}\n")
        if speak:
            speak_text(ans)
    elif model_used == "none":
        if is_english:
            notice = "⚠️ [AI Model services are currently unavailable or rate-limited. Please check your internet connection or try again in a moment.]"
        else:
            notice = "⚠️ [AI ಮಾದರಿ ಸೇವೆಗಳು ಪ್ರಸ್ತುತ ಲಭ್ಯವಿಲ್ಲ ಅಥವಾ ಸಿಮಿತವಾಗಿವೆ. ದಯವಿಟ್ಟು ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.]"
        print_clean(f"\n{notice}\n")
    else:
        if is_english:
            notice = f"✅ [Answer fetched from {model_used}]"
        else:
            notice = f"✅ [{model_used} ಮೂಲಕ ಉತ್ತರ ಪಡೆಯಲಾಗಿದೆ]"
        print_clean(f"{notice}\n")
        print_clean(f"{ans}\n")
        if speak:
            speak_text(ans)


# ── Pronoun Resolution (mirrors response_generator.py) ────────────────────────
def _resolve_pronouns_cli(query: str, state: DialogueState) -> str:
    """
    Prepend the known crop / pest context for short or pronoun-containing queries.
    """
    pronouns = ["ಇದಕ್ಕೆ", "ಅದನ್ನು", "ಅದರ", "ಅದು", "it", "this", "that", "its", "them"]
    query_lower = query.lower()
    has_pronoun = any(p in query_lower for p in pronouns) or len(query.split()) <= 3

    if has_pronoun:
        additions = []
        if state.crop_name:
            additions.append(state.crop_name)
        if state.pest_name:
            additions.append(state.pest_name)
        elif state.disease_name:
            additions.append(state.disease_name)
        elif state.problem_type:
            additions.append(state.problem_type)
        if additions:
            resolved = f"{' '.join(additions)} {query}"
            print(f"   [Context: resolved '{query}' → '{resolved}']", flush=True)
            return resolved
    return query


# ── LLM entity extraction (async, for crop/intent resolution) ─────────────────
async def _extract_entities_cli(query: str, history: list[dict], gemini_client=None) -> dict:
    """
    Call Gemini to extract crop_name, intent, pest_name, disease_name, etc.
    Returns {} on failure.
    """
    formatted_history = ""
    if history:
        formatted_history = "\n".join(
            f"{'User' if h['role'] == 'farmer' else 'Assistant'}: {h['content']}"
            for h in history[-4:]
        )

    prompt = (
        "You are an expert agricultural language parser.\n"
        "Analyze the User Query contextually based on the Conversation History (if any) and extract agricultural slots in JSON format.\n"
        "If the user is using pronouns like 'it', 'this', 'that', or 'ಅದು', 'ಇದಕ್ಕೆ', 'ಅದನ್ನು' to refer to a previously mentioned crop, pest, or disease in the conversation, resolve it using the history.\n\n"
        "=== Conversation History ===\n"
        f"{formatted_history}\n\n"
        "=== User Query ===\n"
        f"\"{query}\"\n\n"
        "Response MUST be a JSON object ONLY with the following keys:\n"
        "- \"farmer_name\": Farmer's name if the user introduces themselves in query (e.g. 'im sia', 'my name is Ramesh', 'I am Priya', 'ನನ್ನ ಹೆಸರು ರಮೇಶ್', 'ನಾನು ಇಶಾ'), else null.\n"
        "- \"crop_name\": Crop name in Kannada or English if mentioned in query or context (e.g. ಕಿವಿ, ಮೆಕ್ಕೆಜೋಳ, ತೆಂಗು, ದ್ರಾಕ್ಷಿ, ಬಾಳೆ, ಸೇಬು, Kiwi, Tomato, etc.), else null.\n"
        "- \"intent\": One of: soil, sowing, fertilizer, irrigation, control, symptoms, identification, harvesting, spacing, disease_management, pesticide, greeting, general_advisory, or null. (If asking about soil, soil selection, pH, or ground type, extract 'soil').\n"
        "- \"pest_name\": Specific insect/pest name if mentioned, else null.\n"
        "- \"disease_name\": Specific disease name if mentioned, else null.\n"
        "- \"fertilizer_name\": Specific fertilizer name if mentioned, else null.\n"
        "- \"pesticide_name\": Specific pesticide/chemical name if mentioned, else null.\n"
        "- \"symptoms\": List of symptoms mentioned else empty list.\n\n"
        "Do not include markdown tags like ```json or any explanation, just return the JSON object."
    )
    try:
        if gemini_client:
            result = await gemini_client.generate(prompt)
        else:
            return {}
        cleaned = result.strip()
        import re
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        return json.loads(cleaned)
    except Exception:
        return {}


# ── LLM-based semantic verification ──────────────────────────────────────────
async def _verify_match_cli(user_query: str, db_question: str, gemini_client=None) -> bool:
    """
    Use Gemini to verify the DB question really answers the user's query.
    Enforces true semantic match with same intent, crop, and context.
    """
    prompt = (
        "You are an expert agricultural semantic match verifier.\n\n"
        f"User Query: \"{user_query}\"\n"
        f"Database Candidate Question: \"{db_question}\"\n\n"
        "Your task: Determine if the Database Candidate covers the same specific topic for the same crop and can be used to directly answer the User Query.\n\n"
        "RULES:\n"
        "1. SAME CROP: Both must refer to the same crop (or both be general agricultural queries).\n"
        "2. RELATED INTENT: The database question must address the same user intent (e.g. both ask about pest control, both ask about sowing, or both ask about fertilizer dosage).\n"
        "3. KANGLISH/TRANSLITERATION: Treat English, Kannada, and transliterated Kannada (Kanglish, e.g., 'suryakanthi' and 'ಸೂರ್ಯಕಾಂತಿ') as equivalent.\n"
        "4. ACCEPT if the database question answers the user query, even if the phrasing is slightly different or the database question is broader.\n"
        "5. Output EXACTLY 'YES' or 'NO' and nothing else."
    )
    try:
        if gemini_client:
            res = await gemini_client.generate(prompt)
            return "YES" in res.strip().upper()
    except Exception:
        pass
    return False  # Fail closed — do NOT trust unverified loose matches


async def _format_db_answer_cli(user_query: str, db_answer: str, farmer_name: str, is_english: bool, gemini_client=None, is_voice_mode: bool = False) -> str:
    """
    Format the database answer conversationally using Gemini (or fallback).
    """
    if not gemini_client:
        name_part = f"ನಮಸ್ಕಾರ {farmer_name} ಅವರೇ! 🌾 " if farmer_name else ""
        if is_english and farmer_name:
            name_part = f"Dear {farmer_name}! 🌾 "
        return f"{name_part}{db_answer}"

    if is_voice_mode:
        rules = (
            "1. Speak in short, natural spoken sentences—not written-style paragraphs with list tags or headers. Say things exactly as you would say them out loud.\n"
            "2. DO NOT use markdown bold (*), headers (#), bullet points (-), or list numbers (1., 2.). If listing steps, write 'First...', 'Second...' naturally in a continuous paragraph.\n"
            "3. Keep the response very concise (2-4 sentences max).\n"
            "4. Numbers, prices, and units must be written out fully as words (e.g. say '500 rupees' instead of '₹500', '10 kilograms' instead of '10kg') so they are clean when read aloud.\n"
            "5. Address the farmer warmly and politely. Speak sweetly and respectfully.\n"
            "6. STRICTLY ground your answer in the provided database text. Do NOT add external facts or hallucinate."
        )
    else:
        rules = (
            "1. You may use light formatting (short bullet points, bold key terms) since this will be read, not heard.\n"
            "2. Keep it visually clean, highly scannable, and extremely concise (max 3-4 sentences, or 2-3 short bullet points). Avoid long paragraphs.\n"
            "3. Address the farmer warmly and respectfully.\n"
            "4. STRICTLY ground your answer in the provided database text. Do NOT add external facts or hallucinate."
        )

    prompt = (
        "You are \"Raitha Sathi\" (🌾 ರೈತ ಸಾಥಿ) — a sweet, warm, caring personal agricultural assistant for Karnataka farmers.\n\n"
        "The farmer asked:\n"
        f"\"{user_query}\"\n\n"
        "Here is the verified FACTUAL solution from our database:\n"
        "---------------------------------------\n"
        f"{db_answer}\n"
        "---------------------------------------\n\n"
        "Your task is to rephrase and format this database answer following these formatting rules:\n"
        f"{rules}\n\n"
        f"Address the farmer by name if known (e.g. \"ನಮಸ್ಕಾರ {farmer_name} ಅವರೇ!\" or \"Dear {farmer_name}!\"). If name is not known, address them as \"ಕೃಷಿ ಬಾಂಧವರೇ\" or \"Dear Farmer\".\n"
        f"Respond in natural, polite, and fluent {'English' if is_english else 'Kannada'}.\n"
        "Response:"
    )
    try:
        res = await gemini_client.generate(prompt)
        if res and len(res.strip()) > 20:
            return res.strip()
    except Exception:
        pass
    
    name_part = f"ನಮಸ್ಕಾರ {farmer_name} ಅವರೇ! 🌾 " if farmer_name else ""
    if is_english and farmer_name:
        name_part = f"Dear {farmer_name}! 🌾 "
    return f"{name_part}{db_answer}"


async def _run_chat():
    """Async entry point for the full conversational chat loop."""
    # ── Load Database & FAISS Index ──────────────────────────────────────────
    print_clean("\nLoading database & FAISS index...", end=" ", flush=True)
    db = DatabaseSearcher()
    retriever = None
    context_builder = ContextBuilder()
    prompt_builder = PromptBuilder()
    session_mgr = SessionManager()
    follow_up_gen = FollowUpGenerator()

    try:
        retriever = Retriever()
        retriever.load()
        vectors_count = retriever.faiss_index.total_vectors
        print_clean(f"OK — {db.get_entry_count()} DB entries, {vectors_count} FAISS vectors, 15 crops.")
    except Exception as e:
        print_clean(f"\n[Note: FAISS index not loaded ({e}). Using keyword search only.]")
        print_clean(f"OK — {db.get_entry_count()} DB entries, 15 crops.")

    # ── Lazily initialise Gemini client ──────────────────────────────────────
    gemini_client = None
    try:
        from app.llm.gemini_client import GeminiClient
        gemini_client = GeminiClient()
        print_clean("[Gemini client ready]")
    except Exception as e:
        print_clean(f"[Gemini client unavailable: {e}]")

    print_banner()
    print_crops()

    # ── Create a new session for this terminal session ────────────────────────
    session_id = session_mgr.new_session()
    
    print_clean("\nWelcome to Raitha Sathi! 🌾")
    print_clean("Please select your preferred interaction mode:")
    print_clean("  [1] ⌨️  Text Mode (Type your questions)")
    print_clean("  [2] 🎙️  Voice Mode (Speak your questions, listen to answers)")
    
    chat_mode = "1"
    try:
        chat_mode = input("Enter choice (1 or 2, default 1): ").strip()
    except (KeyboardInterrupt, EOFError):
        stop_speech()
        print("\n\nGoodbye! / ಧನ್ಯವಾದ!")
        return

    if chat_mode == "2":
        speech_mode = True
        voice_input_default = True
        print_clean("\n📢 [Voice Mode Activated!]")
        print_clean("- Speak your questions in Kannada or English when prompted.")
        print_clean("- Every answer will be spoken aloud in the correct language.\n")
    else:
        speech_mode = False
        voice_input_default = False
        print_clean("\n⌨️ [Text Mode Activated!]")
        print_clean("- Type your questions in Kannada or English.")
        print_clean("- Type 'speech' at any time to toggle Voice Output ON/OFF.\n")

    print_clean(f"[Session: {session_id[:8]}...] Type 'new' to start a fresh conversation.\n")

    # ── Chat Loop ────────────────────────────────────────────────────────────
    while True:
        used_voice = False
        try:
            print("-" * 60)
            if voice_input_default:
                used_voice = True
                audio_file = "user_input.wav"
                record_res = record_speech(audio_file)
                if record_res == "record":
                    print("Transcribing your speech using Gemini...")
                    query = await transcribe_speech(audio_file)
                    if query:
                        print(f"You said: \"{query}\"\n")
                        # Handle exit command within speech
                        if is_exit_command(query):
                            stop_speech()
                            print("\nGoodbye! / ಧನ್ಯವಾದ!")
                            break
                    else:
                        print("⚠️ Sorry, I could not understand the audio. Please try again.")
                        continue
                elif record_res == "fallback":
                    # Fallback to manual text input if recording failed
                    query = input("You (Type your question): ").strip()
                    stop_speech()
                else:
                    # User typed their question directly at the prompt!
                    query = record_res
                    used_voice = False
            else:
                if is_speaking():
                    prompt_text = "You (AI is speaking... type question, or '2' for Voice Mode): "
                else:
                    prompt_text = "You (type question, or '2' for Voice Mode, 'exit' to quit): " if not speech_mode else "You [Voice Output ON] (type question, or '2' for Voice Mode, 'exit' to quit): "
                query = input(prompt_text).strip()
                stop_speech()
                
                # If input is empty, trigger speech-to-text recording
                if not query:
                    used_voice = True
                    audio_file = "user_input.wav"
                    record_res = record_speech(audio_file)
                    if record_res == "record":
                        print("Transcribing your speech using Gemini...")
                        query = await transcribe_speech(audio_file)
                        if query:
                            print(f"You said: \"{query}\"\n")
                        else:
                            print("⚠️ Sorry, I could not understand the audio. Please speak clearly or type.")
                            continue
                    elif record_res == "fallback":
                        continue
                    else:
                        # User typed their question directly
                        query = record_res
                        used_voice = False
        except (KeyboardInterrupt, EOFError):
            stop_speech()
            print("\n\nGoodbye! / ಧನ್ಯವಾದ!")
            break

        if not query:
            continue

        # Mode switching commands
        if query.lower() in ["text", "keyboard", "1"]:
            voice_input_default = False
            speech_mode = False
            print_clean("\n⌨️ [Switched to Text Mode!]")
            print_clean("- Type your questions in Kannada or English.")
            print_clean("- Type 'speech' at any time to toggle Voice Output ON/OFF.\n")
            continue

        if query.lower() in ["voice", "speak", "2"]:
            voice_input_default = True
            speech_mode = True
            print_clean("\n📢 [Switched to Voice Mode!]")
            print_clean("- Speak your questions in Kannada or English when prompted.")
            print_clean("- Every answer will be spoken aloud in the correct language.\n")
            continue

        if is_exit_command(query) or query.strip().lower() == "q":
            stop_speech()
            print("\nGoodbye! / ಧನ್ಯವಾದ!")
            break

        if query.lower() in ["crops", "list", "ಬೆಳೆಗಳು", "help"]:
            print_crops()
            continue

        if query.lower() == "speech":
            speech_mode = not speech_mode
            status = "ON" if speech_mode else "OFF"
            print_clean(f"\n📢 [Voice Output Mode turned {status}]\n")
            continue

        if query.lower() == "new":
            session_mgr.close_session(session_id)
            session_id = session_mgr.new_session()
            print(f"\n[New session started: {session_id[:8]}...]\n")
            continue

        # ── Step 1: Record farmer's message & get session state ───────────────
        session_mgr.add_user_turn(session_id, query)
        state = session_mgr.get_state(session_id)
        history = session_mgr.get_recent_history(session_id, n=5)

        # ── Step 1.0: Name extraction — always update if user re-introduces themselves ──
        detected_name = extract_farmer_name(query)
        if detected_name and detected_name != state.farmer_name:
            state.farmer_name = detected_name
            session_mgr.memory.update_state(session_id, state)

        # ── Step 1.1: Entity & intent extraction via LLM ──────────────────────
        print("   [Extracting entities & intent...]", end=" ", flush=True)
        extracted = await _extract_entities_cli(query, history[:-1], gemini_client)
        if extracted:
            session_mgr.update_state_from_llm(session_id, extracted)
            state = session_mgr.get_state(session_id)
            crop_show = state.crop_name or "—"
            intent_show = state.intent or "—"
            print(f"crop={crop_show} | intent={intent_show}")
        else:
            print("(skipped)")

        # ── Step 1.2: Pronoun resolution ──────────────────────────────────────
        effective_query = _resolve_pronouns_cli(query, state)

        # ── Step 2: Pre-filter non-agricultural / greeting queries ────────────
        is_english = any(ord(c) < 128 and c.isalpha() for c in query)
        state.detected_language = "en" if is_english else "kn"
        session_mgr.memory.update_state(session_id, state)
        non_agri_keywords = [
            "python", "java", "coding", "programmer", "code", "software", "script", "movie", "cinema",
            "actor", "actress", "film", "song", "music", "cricket", "football", "match", "ipl",
            "politics", "minister", "president", "prime minister", "election", "capital of",
            "who is", "who was", "math", "formula", "equation", "calculator", "recipe", "cake",
            "pizza", "burger", "joke", "tell me a joke", "game", "gaming", "html", "css", "javascript",
            "c++", "c#", "react", "node", "angular", "song", "hero", "heroine", "modi", "rahul",
            "ವಿಮಾನ", "ಸಿನಿಮಾ", "ರಾಜಕೀಯ", "ನಟ", "ನಟಿ", "ಆಟ", "ಕ್ರಿಕೆಟ್", "ಖಾತೆ", "ಪಾಸ್‌ವರ್ಡ್", "ಹಾಡು",
            "ಚಿತ್ರ", "ಕಥೆ", "ಮಂತ್ರಿ", "ಮುಖ್ಯಮಂತ್ರಿ", "ಪ್ರಧಾನಿ", "ಚುನಾವಣೆ", "ಕಾರು", "ಬೈಕ್", "ಮೊಬೈಲ್", "ಫೋನ್",
            "ತಯಾರಿಸುವುದು ಹೇಗೆ", "ತಯಾರಿಸಬೇಕು", "ಅಡುಗೆ", "ಪಾಕವಿಧಾನ", "ಕುಡಿಯಲು", "ಕಾಫಿ ಮಾಡುವುದು ಹೇಗೆ", "ಟೀ ಮಾಡುವುದು ಹೇಗೆ", "ಜ್ಯೂಸ್"
        ]
        agri_keywords = [
            "cultivat", "plant", "grow", "agri", "farm", "soil", "pest", "disease", "fertiliz",
            "water", "yield", "seed", "nursery", "sapling", "graft", "propagat", "harvest",
            "fruit", "vegetable", "field", "irrigation", "crop", "paddy", "arecanut", "maize",
            "rice", "ragi", "cotton", "coffee", "coconut", "sugarcane", "turmeric", "jowar",
            "bajra", "groundnut", "chickpea", "pigeon", "pigeonpea", "sunflower",
            "ಬೆಳೆ", "ಕೃಷಿ", "ಮಣ್ಣು", "ಕೀಟ", "ರೋಗ", "ಗೊಬ್ಬರ", "ಬೀಜ", "ಅಡಿಕೆ", "ರಾಗಿ", "ಭತ್ತ",
            "ಕಬ್ಬು", "ಕಬ್ಬಿನಲ್ಲಿ", "ಕಬ್ಬಿನ", "ಕಬ್ಬಿಗೆ", "ತೆಂಗು", "ತೆಂಗಿನಲ್ಲಿ", "ತೆಂಗಿನ", "ತೆಂಗಿಗೆ",
            "ಹತ್ತಿ", "ಹತ್ತಿಯಲ್ಲಿ", "ಹತ್ತಿಯ", "ಹತ್ತಿಗೆ", "ಕಾಫಿ", "ಕಾಫಿಯಲ್ಲಿ", "ಕಾಫಿಯ", "ಕಾಫಿಗೆ",
            "ಶೇಂಗಾ", "ಶೇಂಗಾದಲ್ಲಿ", "ಶೇಂಗಾದ", "ಮೆಕ್ಕೆಜೋಳ", "ಮೆಕ್ಕೆಜೋಳದಲ್ಲಿ", "ಮೆಕ್ಕೆಜೋಳದ",
            "ಅರಿಶಿನ", "ಅರಿಶಿನದಲ್ಲಿ", "ಅರಿಶಿನದ", "ಸಜ್ಜೆ", "ಸಜ್ಜೆಯಲ್ಲಿ", "ಸಜ್ಜೆಯ",
            "ಕಡಲೆ", "ಕಡಲೆಯಲ್ಲಿ", "ಕಡಲೆಯ", "ತೊಗರಿ", "ತೊಗರಿಯಲ್ಲಿ", "ತೊಗರಿಯ",
            "ಜೋಳ", "ಜೋಳದಲ್ಲಿ", "ಜೋಳದ", "ಸೂರ್ಯಕಾಂತಿ", "ಸೂರ್ಯಕಾಂತಿಯಲ್ಲಿ", "ಸೂರ್ಯಕಾಂತಿಯ",
            "ಸಸಿ", "ನರ್ಸರಿ", "ಕಸಿ", "ಉತ್ಪಾದನೆ", "ತೋಟ", "ಬೇಸಾಯ", "ಇಳುವರಿ", "ಕೊಯ್ಲು", "ಸಾಗುವಳಿ", "ಹಣ್ಣು", "ತರಕಾರಿ",
            "ನೀರಾವರಿ", "ಹನಿ", "ಸಬ್ಸಿಡಿ", "ಸಾಲು", "ಪೋಷಕಾಂಶ",
            "ಎಪಿಎಂಸಿ", "ಮಾರುಕಟ್ಟೆ", "ಮಾರಾಟ", "ಧಾನ್ಯ", "ಬೆಲೆ", "ಖರೀದಿ", "ಸಂಗ್ರಹ", "ಗೋದಾಮು",
            "apmc", "market", "selling", "grain", "storage", "price", "msp",
        ]
        q_lower = query.lower()
        has_non_agri = any(kw in q_lower for kw in non_agri_keywords)
        has_agri = any(akw in q_lower for akw in agri_keywords)

        # Let the AI fallback naturally handle greetings and thank yous

        # Let the AI fallback naturally handle greetings and thank yous

        # ── Step 2.6: Check if follow-up is needed when crop context is missing ───
        if follow_up_gen.needs_followup(state):
            follow_q = follow_up_gen.generate(state, effective_query)
            if follow_q:
                session_mgr.add_assistant_turn(session_id, follow_q)
                print_clean(f"\n🌾 ರೈತ ಸಾಥಿ: {follow_q}\n")
                if speech_mode or used_voice:
                    speak_text(follow_q)
                continue

        # ── Step 3: Detect if crop is in our DB ───────────────────────────────
        # Prefer the LLM-extracted crop if available (already set in state),
        # else fall back to simple keyword detect_crop().
        detected_crop_simple, is_in_db = detect_crop(effective_query)
        if state.crop_name:
            # Cross-check: is the LLM-detected crop actually in our DB?
            _, is_in_db = detect_crop(state.crop_name)

        # ── Step 4: Crop NOT in DB → use AI directly ─────────────────────────
        if not is_in_db:
            crop_label = state.crop_name or detected_crop_simple or ""
            fetch_and_print_ai(effective_query, crop_label, state.farmer_name or "", speak=(speech_mode or used_voice))
            session_mgr.add_assistant_turn(session_id, "[AI-generated answer provided]")
            continue

        crop_filter = state.crop_name or (detected_crop_simple if detected_crop_simple else None)

        # ── Step 5: Tier 1 — Direct DB search (crop-locked, intent-aware) ─────
        db_res = db.search(
            effective_query,
            crop_name=crop_filter,
            intent=state.intent,
            return_matched_question=True,
        )
        if db_res:
            db_answer, matched_question = db_res
            # Step 5.1: Semantic verification
            print_clean("   [Verifying DB match...]", end=" ", flush=True)
            verified = await _verify_match_cli(effective_query, matched_question, gemini_client)
            if verified:
                print_clean("✓ Match verified")
                formatted_answer = await _format_db_answer_cli(query, db_answer, state.farmer_name, is_english, gemini_client, is_voice_mode=(speech_mode or used_voice))
                session_mgr.add_assistant_turn(session_id, formatted_answer)
                print_clean("\n📂 ✅ [ಉತ್ತರ ನಮ್ಮ ಡೇಟಾಬೇಸ್‌ನಿಂದ ನೇರವಾಗಿ ಬಂದಿದೆ / Answer from our verified database]\n")
                print_clean(f"🌾 ರೈತ ಸಾಥಿ: {formatted_answer}\n")
                if speech_mode or used_voice:
                    speak_text(formatted_answer)
                continue
            else:
                print_clean("✗ Rejected (cross-crop or intent mismatch)")

        # ── Step 6: Tier 2 — FAISS semantic retrieval ─────────────────────────
        context_text = ""
        top_confidence = 0.0
        if retriever:
            try:
                enriched_query = f"{effective_query} {state.to_retrieval_query()}"
                results = retriever.retrieve(
                    enriched_query,
                    top_k=settings.FAISS_TOP_K,
                    crop_name=crop_filter,
                    season=state.season,
                    region=state.region,
                )
                if results:
                    top_confidence = results[0].get("_score", 0.0)
                    context_text = context_builder.build(results)
                    print_clean(f"   [FAISS: {len(results)} entries | top score={top_confidence:.2f}]")

                    # Iterate through top 3 FAISS candidates to find a verified match
                    found_verified = False
                    for candidate in results[:3]:
                        cand_q = candidate.get("question", "")
                        if not cand_q:
                            continue
                        print_clean(f"   [Verifying FAISS candidate: '{cand_q[:45]}...']", end=" ", flush=True)
                        verified = await _verify_match_cli(effective_query, cand_q, gemini_client)
                        if verified:
                            db_ans = db.extract_answer(candidate)
                            if db_ans:
                                print_clean("✓ Match verified")
                                formatted_answer = await _format_db_answer_cli(query, db_ans, state.farmer_name, is_english, gemini_client, is_voice_mode=(speech_mode or used_voice))
                                session_mgr.add_assistant_turn(session_id, formatted_answer)
                                print_clean("\n📂 ✅ [ಉತ್ತರ ನಮ್ಮ ಡೇಟಾಬೇಸ್‌ನಿಂದ ನೇರವಾಗಿ ಬಂದಿದೆ / Answer from our verified database]\n")
                                print_clean(f"🌾 ರೈತ ಸಾಥಿ: {formatted_answer}\n")
                                if speech_mode or used_voice:
                                    speak_text(formatted_answer)
                                found_verified = True
                                break
                            else:
                                print_clean("✗ No answer text")
                        else:
                            print_clean("✗ Rejected")

                    if found_verified:
                        continue
            except Exception as e:
                print_clean(f"   [FAISS retrieval error: {e}]")

        # ── Step 7: Fast LLM generation Fallback ─────────────────
        fetch_and_print_ai(effective_query, crop_filter or "", state.farmer_name or "", speak=(speech_mode or used_voice), history=history[:-1])
        session_mgr.add_assistant_turn(session_id, "[AI-generated fallback answer]")


def is_exit_command(query: str) -> bool:
    """
    Check if the user input contains any Kannada or English exit commands.
    """
    query_clean = query.strip().lower().replace(".", "").replace("?", "")
    exit_words = [
        "exit", "quit", "bye", "goodbye", "stop", "end", 
        "ಯಾವುದೂ ಇಲ್ಲ", "ಬೇಡ", "ಸಾಕು", "ಮುಕ್ತಾಯ"
    ]
    return any(word in query_clean for word in exit_words)


def main():
    """Entry point — runs the async chat loop."""
    try:
        asyncio.run(_run_chat())
    except (KeyboardInterrupt, SystemExit):
        stop_speech()
        print_clean("\nGoodbye! / ಧನ್ಯವಾದ!")
        sys.exit(0)


if __name__ == "__main__":
    main()
