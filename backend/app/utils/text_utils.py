"""
text_utils.py — Text Processing Utilities

WHAT IT DOES:
Provides a toolbox of functions for cleaning text, detecting if a 
user is speaking Kannada or English, and formatting conversation 
history for the LLM. It handles the nuances of Kannada Unicode script.

WHY IT EXISTS:
Centralizes repetitive text tasks. Instead of writing logic to 
clean whitespace or format history in multiple places, we put it 
here to ensure consistency across the entire app.

CONNECTIONS:
- Used by 'retriever.py' to clean queries.
- Used by 'prompt_builder.py' to format chat history.
- Used by 'dataset_loader.py' to clean raw data during ingestion.
"""

import re
import unicodedata
from typing import Optional


# ── Kannada Unicode Range ─────────────────────────────────────────────────────
# Kannada characters are in Unicode range U+0C80 to U+0CFF
KANNADA_UNICODE_RANGE = range(0x0C80, 0x0D00)


def clean_text(text: str) -> str:
    """
    Clean raw text for embedding or display.

    Removes extra whitespace, normalizes Unicode, and strips
    control characters — while preserving Kannada script.

    Args:
        text: Raw input text (may contain Kannada + English)

    Returns:
        Cleaned, normalized text string
    """
    if not text or not isinstance(text, str):
        return ""

    # Normalize Unicode (NFC is standard for Indic scripts)
    text = unicodedata.normalize("NFC", text)

    # Remove control characters (except newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Collapse multiple whitespace into a single space
    text = re.sub(r"\s+", " ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def detect_language(text: str) -> str:
    """
    Detect whether input text is primarily Kannada or English.

    Uses character-level heuristic based on Unicode ranges.
    This avoids external API calls for fast, offline detection.

    Args:
        text: Input text to analyze

    Returns:
        "kn" for Kannada, "en" for English, "mixed" for both
    """
    if not text:
        return "unknown"

    kannada_chars = sum(
        1 for ch in text if ord(ch) in KANNADA_UNICODE_RANGE
    )
    total_chars = len([ch for ch in text if not ch.isspace()])

    if total_chars == 0:
        return "unknown"

    kannada_ratio = kannada_chars / total_chars

    if kannada_ratio > 0.6:
        return "kn"   # Primarily Kannada
    elif kannada_ratio > 0.2:
        return "mixed"  # Mix of Kannada and English
    else:
        return "en"   # Primarily English


def truncate_text(text: str, max_chars: int = 512) -> str:
    """
    Truncate text to a maximum character limit.

    Truncation happens at a word boundary to avoid cutting
    Kannada characters mid-sequence.

    Args:
        text:      Input text
        max_chars: Maximum allowed character count

    Returns:
        Truncated text with ellipsis if shortened
    """
    if len(text) <= max_chars:
        return text

    # Find last space before the limit to avoid mid-word cuts
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")

    if last_space > max_chars * 0.8:  # Only use space if it's reasonably close
        truncated = truncated[:last_space]

    return truncated + "..."


def build_retrieval_text(entry: dict) -> str:
    """
    Build the retrieval_text string from a dataset entry.

    This combines the question, keywords, symptoms, and short answer
    into a single searchable string used for FAISS embedding.

    If the entry already has a 'retrieval_text' field, it is returned directly.

    Args:
        entry: A dataset entry dict following the agricultural schema

    Returns:
        A rich combined text string for embedding
    """
    # Use existing retrieval_text if already populated
    if entry.get("retrieval_text"):
        return clean_text(entry["retrieval_text"])

    parts = []

    # Add question and its variants
    if entry.get("question"):
        parts.append(entry["question"])

    if entry.get("question_variants"):
        parts.extend(entry["question_variants"])

    # Add keywords
    if entry.get("keywords"):
        parts.append(" ".join(entry["keywords"]))

    # Add crop name and topic for domain context
    if entry.get("crop_name"):
        parts.append(entry["crop_name"])

    if entry.get("topic"):
        parts.append(entry["topic"])

    # Add symptoms for diagnostic queries
    if entry.get("symptoms"):
        parts.extend(entry["symptoms"])

    # Add the short answer as a summary signal
    solution = entry.get("solution", {})
    if solution.get("short_answer"):
        parts.append(solution["short_answer"])

    combined = " | ".join(filter(None, parts))
    return clean_text(combined)


def format_conversation_history(history: list[dict]) -> str:
    """
    Format conversation history into a readable string for the LLM prompt.

    Args:
        history: List of {"role": "farmer"/"assistant", "content": "..."} dicts

    Returns:
        Formatted multi-line conversation string
    """
    if not history:
        return ""

    lines = []
    for turn in history:
        role = "ರೈತ" if turn["role"] == "farmer" else "ಸಹಾಯಕ"  # Kannada labels
        lines.append(f"{role}: {turn['content']}")

    return "\n".join(lines)


def extract_crop_from_text(text: str, known_crops: list[str] = None) -> Optional[str]:
    """
    Try to extract a crop name mentioned in the user's text and return its standard root form.
    
    This prevents matching issues where a grammatical suffix (e.g., "ತೆಂಗಿನ") 
    fails to match the DB's canonical name ("ತೆಂಗು").
    """
    # Map of all variants (Kannada & English) to the exact standard Kannada name used in DB
    crop_mappings = {
        # Rice
        "ಅಕ್ಕಿ": "ಭತ್ತ", "ಭತ್ತದ": "ಭತ್ತ", "ಭತ್ತ": "ಭತ್ತ", "ಧಾನ್ಯ": "ಭತ್ತ", "paddy": "ಭತ್ತ", "rice": "ಭತ್ತ",
        # Ragi
        "ರಾಗಿಯ": "ರಾಗಿ", "ರಾಗಿ": "ರಾಗಿ", "finger millet": "ರಾಗಿ", "ragi": "ರಾಗಿ", "ragiya": "ರಾಗಿ", "mandua": "ರಾಗಿ",
        # Maize
        "ಮೆಕ್ಕೆಜೋಳದ": "ಮೆಕ್ಕೆಜೋಳ", "ಮೆಕ್ಕೆಜೋಳ": "ಮೆಕ್ಕೆಜೋಳ", "ಮೆಕ್ಕೆ": "ಮೆಕ್ಕೆಜೋಳ", "maize": "ಮೆಕ್ಕೆಜೋಳ", "corn": "ಮೆಕ್ಕೆಜೋಳ",
        # Jowar
        "ಜೋಳದ": "ಜೋಳ", "ಜೋಳ": "ಜೋಳ", "jowar": "ಜೋಳ", "sorghum": "ಜೋಳ",
        # Bajra
        "ಸಜ್ಜೆಯ": "ಸಜ್ಜೆ", "ಸಜ್ಜೆ": "ಸಜ್ಜೆ", "bajra": "ಸಜ್ಜೆ", "pearl millet": "ಸಜ್ಜೆ",
        # Cotton
        "ಹತ್ತಿಯ": "ಹತ್ತಿ", "ಹತ್ತಿ": "ಹತ್ತಿ", "cotton": "ಹತ್ತಿ",
        # Groundnut
        "ಶೇಂಗಾದ": "ಶೇಂಗಾ", "ಶೇಂಗಾ": "ಶೇಂಗಾ", "ಕಡಲೆಕಾಯಿ": "ಶೇಂಗಾ", "groundnut": "ಶೇಂಗಾ", "peanut": "ಶೇಂಗಾ",
        # Sunflower
        "ಸೂರ್ಯಕಾಂತಿಯ": "ಸೂರ್ಯಕಾಂತಿ", "ಸೂರ್ಯಕಾಂತಿ": "ಸೂರ್ಯಕಾಂತಿ", "sunflower": "ಸೂರ್ಯಕಾಂತಿ",
        # Sugarcane
        "ಕಬ್ಬಿನ": "ಕಬ್ಬು", "ಕಬ್ಬು": "ಕಬ್ಬು", "sugarcane": "ಕಬ್ಬು",
        # Turmeric
        "ಅರಿಶಿನದ": "ಅರಿಶಿನ", "ಅರಿಶಿನ": "ಅರಿಶಿನ", "turmeric": "ಅರಿಶಿನ", "haldi": "ಅರಿಶಿನ",
        # Chickpea
        "ಕಡಲೆಯ": "ಕಡಲೆ", "ಕಡಲೇ": "ಕಡಲೆ", "ಕಡಲೆ": "ಕಡಲೆ", "chickpea": "ಕಡಲೆ", "gram": "ಕಡಲೆ", "chana": "ಕಡಲೆ", "bengal gram": "ಕಡಲೆ",
        # Redgram
        "ತೊಗರಿಯ": "ತೊಗರಿ", "ತೊಗರಿ": "ತೊಗರಿ", "redgram": "ತೊಗರಿ", "pigeon pea": "ತೊಗರಿ", "tur dal": "ತೊಗರಿ", "toor dal": "ತೊಗರಿ", "red gram": "ತೊಗರಿ", "arhar": "ತೊಗರಿ",
        # Arecanut
        "ಅಡಿಕೆಯ": "ಅಡಿಕೆ", "ಅಡಿಕೆ": "ಅಡಿಕೆ", "arecanut": "ಅಡಿಕೆ", "areca": "ಅಡಿಕೆ", "betel nut": "ಅಡಿಕೆ", "supari": "ಅಡಿಕೆ",
        # Coconut
        "ತೆಂಗಿನ": "ತೆಂಗು", "ತೆಂಗು": "ತೆಂಗು", "coconut": "ತೆಂಗು",
        # Coffee
        "ಕಾಫಿಯ": "ಕಾಫಿ", "ಕಾಫಿ": "ಕಾಫಿ", "coffee": "ಕಾಫಿ",
        
        # Apple / ಸೇಬು
        "ಆಪಲ್": "ಸೇಬು", "ಆಪಲ್‌ನ": "ಸೇಬು", "ಆಪಲ್‌": "ಸೇಬು", "ಆಪಲ್‌ನಲ್ಲಿ": "ಸೇಬು", "ಆ್ಯಪಲ್": "ಸೇಬು", "ಸೇಬು": "ಸೇಬು", "ಸೇಬಿನ": "ಸೇಬು", "apple": "ಸೇಬು",
        # Dragon Fruit
        "ಡ್ರ್ಯಾಗನ್ ಫ್ರೂಟ್": "ಡ್ರ್ಯಾಗನ್ ಫ್ರೂಟ್", "ಡ್ರ್ಯಾಗನ್‌ಫ್ರೂಟ್": "ಡ್ರ್ಯಾಗನ್ ಫ್ರೂಟ್", "ಡ್ರ್ಯಾಗನ್": "ಡ್ರ್ಯಾಗನ್ ಫ್ರೂಟ್", "dragon fruit": "ಡ್ರ್ಯಾಗನ್ ಫ್ರೂಟ್", "dragonfruit": "ಡ್ರ್ಯಾಗನ್ ಫ್ರೂಟ್",
        # Avocado
        "ಅವಕಾಡೊ": "ಅವಕಾಡೊ", "ಆವಕಾಡೊ": "ಅವಕಾಡೊ", "ಬೆಣ್ಣೆಹಣ್ಣು": "ಅವಕಾಡೊ", "avocado": "ಅವಕಾಡೊ", "butter fruit": "ಅವಕಾಡೊ",
        # Hydroponics / Greens
        "ಹೈಡ್ರೋಪೋನಿಕ್ಸ್": "ಹೈಡ್ರೋಪೋನಿಕ್ಸ್", "hydroponics": "ಹೈಡ್ರೋಪೋನಿಕ್ಸ್",
        "ಲೆಟ್ಯೂಸ್": "ಲೆಟ್ಯೂಸ್", "lettuce": "ಲೆಟ್ಯೂಸ್",
        "ಪಾಲಕ್": "ಪಾಲಕ್", "spinach": "ಪಾಲಕ್", "palak": "ಪಾಲಕ್",
        # Papaya
        "ಪಪಾಯ": "ಪಪಾಯ", "ಪಪ್ಪಾಯಿ": "ಪಪಾಯ", "papaya": "ಪಪಾಯ",
        # Watermelon
        "ಕಲ್ಲಂಗಡಿ": "ಕಲ್ಲಂಗಡಿ", "watermelon": "ಕಲ್ಲಂಗಡಿ",
        # Orange / Citrus
        "ಕಿತ್ತಳೆ": "ಕಿತ್ತಳೆ", "orange": "ಕಿತ್ತಳೆ", "citrus": "ಕಿತ್ತಳೆ", "ಲಿಂಬೆ": "ನಿಂಬೆ", "ನಿಂಬೆ": "ನಿಂಬೆ", "lemon": "ನಿಂಬೆ", "lime": "ನಿಂಬೆ",
        # Pomegranate
        "ದಾಳಿಂಬೆ": "ದಾಳಿಂಬೆ", "pomegranate": "ದಾಳಿಂಬೆ",
        # Guava
        "ಸೀಬೆ": "ಸೀಬೆ", "ಪೇರಲ": "ಸೀಬೆ", "guava": "ಸೀಬೆ",
        # Tomato
        "ಟೊಮ್ಯಾಟೊ": "ಟೊಮೆಟೊ", "ಟೊಮೇಟೊ": "ಟೊಮೆಟೊ", "ಟೊಮೆಟೊ": "ಟೊಮೆಟೊ", "tomato": "ಟೊಮೆಟೊ",
        # Chilli
        "ಮೆಣಸಿನಕಾಯಿ": "ಮೆಣಸಿನಕಾಯಿ", "ಮೆಣಸಿನ ಕಾಯಿ": "ಮೆಣಸಿನಕಾಯಿ", "chilli": "ಮೆಣಸಿನಕಾಯಿ", "chili": "ಮೆಣಸಿನಕಾಯಿ",
        # Onion
        "ಈರುಳ್ಳಿ": "ಈರುಳ್ಳಿ", "onion": "ಈರುಳ್ಳಿ",
        # Potato
        "ಆಲೂಗಡ್ಡೆ": "ಆಲೂಗಡ್ಡೆ", "ಆಲೂಗೆಡ್ಡೆ": "ಆಲೂಗಡ್ಡೆ", "potato": "ಆಲೂಗಡ್ಡೆ", "aloo": "ಆಲೂಗಡ್ಡೆ",
        # Garlic
        "ಬೆಳ್ಳುಳ್ಳಿ": "ಬೆಳ್ಳುಳ್ಳಿ", "garlic": "ಬೆಳ್ಳುಳ್ಳಿ",
        # Ginger
        "ಶುಂಠಿ": "ಶುಂಠಿ", "ginger": "ಶುಂಠಿ",
        # Mango
        "ಮಾವು": "ಮಾವು", "ಮಾವಿನ": "ಮಾವು", "mango": "ಮಾವು",
        # Banana
        "ಬಾಳೆ": "ಬಾಳೆ", "ಬಾಳೆಹಣ್ಣು": "ಬಾಳೆ", "banana": "ಬಾಳೆ",
        # Grape
        "ದ್ರಾಕ್ಷಿ": "ದ್ರಾಕ್ಷಿ", "grape": "ದ್ರಾಕ್ಷಿ",
        # Betel Vine
        "ಅರಟ": "ಅರಟ", "betel": "ಅರಟ",
        # Wheat
        "ಗೋಧಿ": "ಗೋಧಿ", "wheat": "ಗೋಧಿ",
        # Cashew
        "ಗೇರು": "ಗೇರು", "cashew": "ಗೇರು",
        # Brinjal
        "ಬದನೆ": "ಬದನೆ", "brinjal": "ಬದನೆ",
        # Okra / Lady's Finger
        "ಬೆಂಡೆಕಾಯಿ": "ಬೆಂಡೆಕಾಯಿ", "ಬೆಂಡಿಕಾಯಿ": "ಬೆಂಡೆಕಾಯಿ", "ಬೆಂಡೆ": "ಬೆಂಡೆಕಾಯಿ", "okra": "ಬೆಂಡೆಕಾಯಿ", "lady's finger": "ಬೆಂಡೆಕಾಯಿ", "lady finger": "ಬೆಂಡೆಕಾಯಿ",
        # Temperate & Stone Fruits
        "peach": "ಪೀಚ್", "peaches": "ಪೀಚ್", "ಪೀಚ್": "ಪೀಚ್",
        "plum": "ಪ್ಲಮ್", "plums": "ಪ್ಲಮ್", "ಪ್ಲಮ್": "ಪ್ಲಮ್",
        "cherry": "ಚೆರ್ರಿ", "cherries": "ಚೆರ್ರಿ", "ಚೆರ್ರಿ": "ಚೆರ್ರಿ",
        "pear": "ಪೇರಳೆ", "pears": "ಪೇರಳೆ", "ಪೇರಳೆ": "ಪೇರಳೆ",
        "apricot": "ಆಪ್ರಿಕಾಟ್", "apricots": "ಆಪ್ರಿಕಾಟ್", "ಆಪ್ರಿಕಾಟ್": "ಆಪ್ರಿಕಾಟ್",
        "fig": "ಅಂಜೂರ", "figs": "ಅಂಜೂರ", "ಅಂಜೂರ": "ಅಂಜೂರ",
        "custard apple": "ಸೀತಾಫಲ", "ಸೀತಾಫಲ": "ಸೀತಾಫಲ", "sitaphal": "ಸೀತಾಫಲ",
        "mulberry": "ಹಿಪ್ಪುನೇರಳೆ", "ಹಿಪ್ಪುನೇರಳೆ": "ಹಿಪ್ಪುನೇರಳೆ",
        "strawberry": "ಸ್ಟ್ರಾಬೆರಿ", "strawberries": "ಸ್ಟ್ರಾಬೆರಿ", "ಸ್ಟ್ರಾಬೆರಿ": "ಸ್ಟ್ರಾಬೆರಿ",
        "blueberry": "ಬ್ಲೂಬೆರ್ರಿ", "blueberries": "ಬ್ಲೂಬೆರ್ರಿ", "ಬ್ಲೂಬೆರ್ರಿ": "ಬ್ಲೂಬೆರ್ರಿ",
        "almond": "ಬಾದಾಮಿ", "almonds": "ಬಾದಾಮಿ", "ಬಾದಾಮಿ": "ಬಾದಾಮಿ",
        "walnut": "ಅಕ್ರೋಟ", "walnuts": "ಅಕ್ರೋಟ", "ಅಕ್ರೋಟ": "ಅಕ್ರೋಟ",
        "pistachio": "ಪಿಸ್ತಾ", "pista": "ಪಿಸ್ತಾ", "ಪಿಸ್ತಾ": "ಪಿಸ್ತಾ",
        "lychee": "ಲಿಚಿ", "litchi": "ಲಿಚಿ", "ಲಿಚಿ": "ಲಿಚಿ",
        "cocoa": "ಕೋಕೋ", "cacao": "ಕೋಕೋ", "ಕೋಕೋ": "ಕೋಕೋ",
        "mushroom": "ಅಣಬೆ", "mushrooms": "ಅಣಬೆ", "ಅಣಬೆ": "ಅಣಬೆ",
        "broccoli": "ಬ್ರೊಕೊಲಿ", "capsicum": "ದಪ್ಪ ಮೆಣಸಿನಕಾಯಿ",
        "mint": "ಪುದೀನಾ", "pudina": "ಪುದೀನಾ", "ಪುದೀನಾ": "ಪುದೀನಾ",
        "tulsi": "ತುಳಸಿ", "basil": "ತುಳಸಿ", "ತುಳಸಿ": "ತುಳಸಿ",
        "aloevera": "ಲೋಳೆಸರ", "aloe vera": "ಲೋಳೆಸರ", "aloe": "ಲೋಳೆಸರ", "ಲೋಳೆಸರ": "ಲೋಳೆಸರ",
        "sandalwood": "ಶ್ರೀಗಂಧ", "ಶ್ರೀಗಂಧ": "ಶ್ರೀಗಂಧ",
        "teak": "ತೇಗ", "ತೇಗ": "ತೇಗ",
        "bamboo": "ಬಿದಿರು", "ಬಿದಿರು": "ಬಿದಿರು",
        # Tamarind / ಹುಣಸೆ
        "ಹುಣಸೆಹಣ್ಣನ್ನ": "ಹುಣಸೆ", "ಹುಣಸೆಹಣ್ಣನ್ನು": "ಹುಣಸೆ", "ಹುಣಸೆಹಣ್ಣು": "ಹುಣಸೆ", "ಹುಣಸೆ": "ಹುಣಸೆ", "ಹುಣಸೆಯ": "ಹುಣಸೆ", "tamarind": "ಹುಣಸೆ", "imli": "ಹುಣಸೆ",
        # Jackfruit / ಹಲಸು
        "ಹಲಸಿನ": "ಹಲಸು", "ಹಲಸು": "ಹಲಸು", "ಹಲಸಿನಹಣ್ಣು": "ಹಲಸು", "jackfruit": "ಹಲಸು",
        # Drumstick / ನುಗ್ಗೆ
        "ನುಗ್ಗೆಕಾಯಿ": "ನುಗ್ಗೆ", "ನುಗ್ಗೆ": "ನುಗ್ಗೆ", "ನುಗ್ಗೆ ಸೊಪ್ಪು": "ನುಗ್ಗೆ", "drumstick": "ನುಗ್ಗೆ", "moringa": "ನುಗ್ಗೆ",
        # Sapota / ಚಿಕ್ಕು
        "ಸಪೋಟ": "ಸಪೋಟ", "ಚಿಕ್ಕು": "ಸಪೋಟ", "sapota": "ಸಪೋಟ", "chiku": "ಸಪೋಟ",
        # Flowers
        "ಮಲ್ಲಿಗೆ": "ಮಲ್ಲಿಗೆ", "jasmine": "ಮಲ್ಲಿಗೆ",
        # Other Vegetables & Spices
        "ಕ್ಯಾರೆಟ್": "ಕ್ಯಾರೆಟ್", "carrot": "ಕ್ಯಾರೆಟ್",
        "ಬೀಟ್‌ರೂಟ್": "ಬೀಟ್‌ರೂಟ್", "beetroot": "ಬೀಟ್‌ರೂಟ್",
        "ಎಲೆಕೋಸು": "ಎಲೆಕೋಸು", "cabbage": "ಎಲೆಕೋಸು",
        "ಹೂಕೋಸು": "ಹೂಕೋಸು", "cauliflower": "ಹೂಕೋಸು",
        "ಸೌತೆಕಾಯಿ": "ಸೌತೆಕಾಯಿ", "cucumber": "ಸೌತೆಕಾಯಿ",
        "ಕೊತ್ತಂಬರಿ": "ಕೊತ್ತಂಬರಿ", "coriander": "ಕೊತ್ತಂಬರಿ",
        "ಮೆಂತ್ಯ": "ಮೆಂತ್ಯ", "fenugreek": "ಮೆಂತ್ಯ",
        "ಸಾಸಿವೆ": "ಸಾಸಿವೆ", "mustard": "ಸಾಸಿವೆ",
        "ಎಳ್ಳು": "ಎಳ್ಳು", "sesame": "ಎಳ್ಳು",
        "ಏಲಕ್ಕಿ": "ಏಲಕ್ಕಿ", "cardamom": "ಏಲಕ್ಕಿ",
        "ದಾಲ್ಚಿನ್ನಿ": "ದಾಲ್ಚಿನ್ನಿ", "cinnamon": "ದಾಲ್ಚಿನ್ನಿ",
        "ಲವಂಗ": "ಲವಂಗ", "clove": "ಲವಂಗ",
        "ಕಾಳುಮೆಣಸು": "ಕಾಳುಮೆಣಸು", "black pepper": "ಕಾಳುಮೆಣಸು", "pepper": "ಕಾಳುಮೆಣಸು",
        "ವೆನಿಲ್ಲಾ": "ವೆನಿಲ್ಲಾ", "vanilla": "ವೆನಿಲ್ಲಾ",
        "ರಬ್ಬರ್": "ರಬ್ಬರ್", "rubber": "ರಬ್ಬರ್",
        "ಚಹಾ": "ಚಹಾ", "tea": "ಚಹಾ",
        # Radish / ಮೂಲಂಗಿ
        "ಮೂಲಂಗಿ ಕಾಯಿಯನ್ನು": "ಮೂಲಂಗಿ", "ಮೂಲಂಗಿ ಕಾಯಿಯನ್ನ": "ಮೂಲಂಗಿ", "ಮೂಲಂಗಿ ಕಾಯಿ": "ಮೂಲಂಗಿ",
        "ಮೂಲಂಗಿಕಾಯಿಯನ್ನು": "ಮೂಲಂಗಿ", "ಮೂಲಂಗಿಕಾಯಿಯನ್ನ": "ಮೂಲಂಗಿ", "ಮೂಲಂಗಿಕಾಯಿ": "ಮೂಲಂಗಿ",
        "ಮೂಲಂಗಿಯನ್ನು": "ಮೂಲಂಗಿ", "ಮೂಲಂಗಿಯನ್ನ": "ಮೂಲಂಗಿ", "ಮೂಲಂಗಿಯ": "ಮೂಲಂಗಿ", "ಮೂಲಂಗಿಗೆ": "ಮೂಲಂಗಿ",
        "ಮೂಲಂಗಿ": "ಮೂಲಂಗಿ", "radish": "ಮೂಲಂಗಿ", "mooli": "ಮೂಲಂಗಿ",
        # Gourds
        "ಹೀರೇಕಾಯಿ": "ಹೀರೇಕಾಯಿ", "ಹೀರೆಕಾಯಿ": "ಹೀರೇಕಾಯಿ", "ಹೀರೆ": "ಹೀರೇಕಾಯಿ", "ridge gourd": "ಹೀರೇಕಾಯಿ", "turai": "ಹೀರೇಕಾಯಿ",
        "ಹಾಗಲಕಾಯಿ": "ಹಾಗಲಕಾಯಿ", "ಹಾಗಲ": "ಹಾಗಲಕಾಯಿ", "bitter gourd": "ಹಾಗಲಕಾಯಿ", "karela": "ಹಾಗಲಕಾಯಿ",
        "ಸೋರೆಕಾಯಿ": "ಸೋರೆಕಾಯಿ", "ಸೋರೆ": "ಸೋರೆಕಾಯಿ", "bottle gourd": "ಸೋರೆಕಾಯಿ", "lauki": "ಸೋರೆಕಾಯಿ",
        "ಕುಂಬಳಕಾಯಿ": "ಕುಂಬಳಕಾಯಿ", "ಕುಂಬಳ": "ಕುಂಬಳಕಾಯಿ", "pumpkin": "ಕುಂಬಳಕಾಯಿ",
        "ಬೂದುಕುಂಬಳ": "ಬೂದುಕುಂಬಳ", "ಬೂದು ಕುಂಬಳಕಾಯಿ": "ಬೂದುಕುಂಬಳ", "ash gourd": "ಬೂದುಕುಂಬಳ",
        "ಪಡುವಲಕಾಯಿ": "ಪಡುವಲಕಾಯಿ", "snake gourd": "ಪಡುವಲಕಾಯಿ",
        "ತೊಂಡೆಕಾಯಿ": "ತೊಂಡೆಕಾಯಿ", "ತೊಂಡೆ": "ತೊಂಡೆಕಾಯಿ", "ivy gourd": "ತೊಂಡೆಕಾಯಿ", "tindora": "ತೊಂಡೆಕಾಯಿ",
        # Pulses & Others
        "ಅವರೆಕಾಯಿ": "ಅವರೆ", "ಅವರೆ": "ಅವರೆ", "field beans": "ಅವರೆ", "hyacinth bean": "ಅವರೆ",
        "ಹೆಸರುಕಾಳು": "ಹೆಸರು", "ಹೆಸರು": "ಹೆಸರು", "green gram": "ಹೆಸರು", "moong": "ಹೆಸರು",
        "ಉದ್ದಿನಕಾಳು": "ಉದ್ದು", "ಉದ್ದು": "ಉದ್ದು", "black gram": "ಉದ್ದು", "urad": "ಉದ್ದು",
        "ಹುರುಳಿಕಾಳು": "ಹುರುಳಿ", "ಹುರುಳಿ": "ಹುರುಳಿ", "horse gram": "ಹುರುಳಿ",
        "ಸೋಯಾಬೀನ್": "ಸೋಯಾ", "ಸೋಯಾ": "ಸೋಯಾ", "soybean": "ಸೋಯಾ",
        "ಅಲಸಂದೆ": "ಅಲಸಂದೆ", "cowpea": "ಅಲಸಂದೆ", "lobia": "ಅಲಸಂದೆ",
        "ನವಿಲುಕೋಸು": "ನವಿಲುಕೋಸು", "knol khol": "ನವಿಲುಕೋಸು", "kohlrabi": "ನವಿಲುಕೋಸು",
        "ಗೆಣಸು": "ಗೆಣಸು", "sweet potato": "ಗೆಣಸು",
        "ಸುವರ್ಣಗಡ್ಡೆ": "ಸುವರ್ಣಗಡ್ಡೆ", "yam": "ಸುವರ್ಣಗಡ್ಡೆ",
    }

    text_lower = text.lower()
    
    # Sort keys by length descending to match longest phrases first (e.g. "ತೆಂಗಿನ" before "ತೆಂಗು")
    sorted_variants = sorted(crop_mappings.keys(), key=len, reverse=True)
    
    for variant in sorted_variants:
        v_lower = variant.lower()
        if variant.isascii():
            # Check whole word boundary for English crop names to avoid false positive substring matches
            if re.search(r'\b' + re.escape(v_lower) + r'\b', text_lower):
                return crop_mappings[variant]
        else:
            if v_lower in text_lower or variant in text:
                return crop_mappings[variant]

    # Regex fallback checks
    # 1. Check for "<Crop> ಬೆಳೆ/crop/ಗಿಡ/ಮರ/ತೋಟ" patterns
    pattern1 = re.search(r'([\u0C80-\u0CFFa-zA-Z]+)\s+(ಬೆಳೆಗೆ|ಬೆಳೆಯ|ಬೆಳೆಯಲ್ಲಿ|ಬೆಳೆ|crop|ಗಿಡ|ಮರ|ತೋಟ)(?:\s|$|[.,!?])', text_lower)
    if pattern1:
        candidate = pattern1.group(1).strip()
        non_crop_words = [
            "ಯಾವ", "ಯಾವುದೇ", "ನಿಮ್ಮ", "ನನ್ನ", "ಈ", "ಆ", "ಪ್ರತಿಯೊಂದು", "ಅಥವಾ", "ಮತ್ತು", 
            "which", "your", "my", "this", "that", "any", "ಬೆಳೆ", "crop", "ಒಂದು", "ಒಳ್ಳೆಯ",
            "ಗೊಬ್ಬರ", "ಯೂರಿಯಾ", "ಔಷಧ", "ಔಷಧಿ", "ಕೀಟನಾಶಕ", "ನೀರು", "ಕೃಷಿ", "ವಿಷ", "ಸ್ಪ್ರೇ",
            "ಬೆಲೆ", "ದರ", "ಕಳೆ", "ಹುಳು", "ರೋಗ", "ಕಾಯಿಲೆ", "ಎಕರೆಗೆ", "ಎಕರೆ", "ಗುಂಟೆ", "ಹೆಕ್ಟೇರ್",
            "fertilizer", "urea", "pesticide", "water", "spray", "medicine"
        ]
        if len(candidate) > 1 and candidate not in non_crop_words:
            return candidate

    # 2. Check for "ನಾನು/ನನಗೆ <Crop> ಬೆಳೆಯುವುದಿದೆ / ಹಾಕಬೇಕು" patterns (Kannada)
    pattern2 = re.search(
        r'(?:(?:ನನಗೆ|ನಾನು|ನಮ್ಮಲ್ಲಿ|ನಮ್ಮ|ನಾವು)\s+)?([\u0C80-\u0CFFa-zA-Z]+)'
        r'(?:\s*(?:ಕಾಯಿಯನ್ನು|ಕಾಯಿಯನ್ನ|ಕಾಯಿ|ಹಣ್ಣನ್ನು|ಹಣ್ಣನ್ನ|ಹಣ್ಣು|ಸೊಪ್ಪನ್ನು|ಸೊಪ್ಪು|ಅನ್ನು|ಅನ್ನ|ಯನ್ನು|ಯನ್ನ|ಬೆಳೆಯನ್ನು|ಬೆಳೆಯನ್ನ|ಬೆಳೆ))?'
        r'\s+(?:ಬೆಳೆಯುವುದಿದೆ|ಬೆಳೆಯೋದಿದೆ|ಬೆಳೆಯೋದು|ಬೆಳೆಯುವುದು|ಬೆಳೆಯಲು|ಬೆಳೆಯಬೇಕು|ಬೆಳೆಯುತ್ತಿದ್ದೇನೆ|ಹಾಕುವುದಿದೆ|ಹಾಕೋದು|ಹಾಕಬೇಕು|ಹಾಕಿದ್ದೇನೆ|ಮಾಡಿದ್ದೇನೆ)',
        text_lower
    )
    if pattern2:
        candidate = pattern2.group(1).strip()
        non_crop_words = [
            "ಯಾವ", "ಯಾವುದೇ", "ಈ", "ಆ", "ಒಂದು", "ಎರಡು", "ಹೊಸ", "ನನಗೆ", "ನಾನು", "ನಮ್ಮ", "ನಾವು",
            "ಗೊಬ್ಬರ", "ಯೂರಿಯಾ", "ಔಷಧ", "ಔಷಧಿ", "ಕೀಟನಾಶಕ", "ನೀರು", "ಬೆಳೆ", "ಕೃಷಿ", "ವಿಷ", "ಸ್ಪ್ರೇ",
            "ಬೆಲೆ", "ದರ", "ಕಳೆ", "ಹುಳು", "ರೋಗ", "ಕಾಯಿಲೆ", "ಎಕರೆಗೆ", "ಎಕರೆ", "ಗುಂಟೆ", "ಹೆಕ್ಟೇರ್",
            "fertilizer", "urea", "pesticide", "water", "spray", "medicine"
        ]
        if len(candidate) > 1 and candidate not in non_crop_words:
            return candidate

    # 3. Check for English "grow/plant/cultivate/about <Crop>" patterns
    pattern3 = re.search(r'(?:want to grow|grow|growing|plant|planting|cultivate|cultivating|about|farming of|cultivation of|produce|harvest|seeds of|requirements (?:for|to grow))\s+([a-zA-Z]+)', text_lower)
    if pattern3:
        cand = pattern3.group(1).strip()
        eng_stop = {
            "more", "it", "this", "that", "these", "those", "crops", "plants", "trees", "fruits", 
            "vegetables", "some", "well", "better", "best", "good", "new", "in", "on", "at", "to",
            "and", "or", "a", "an", "the", "my", "your", "our", "their", "here", "there"
        }
        if len(cand) > 2 and cand not in eng_stop:
            return cand

    return None
