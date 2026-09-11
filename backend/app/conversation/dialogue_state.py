"""
dialogue_state.py — Dialogue State Tracker

WHAT IT DOES:
Tracks specific agricultural details extracted from the conversation, 
such as the crop name, symptoms, season, and region. It continuously 
updates this state as the farmer provides more information.

WHY IT EXISTS:
Helps the system understand the *context* of a problem. Instead of 
treating every message as a separate search, the state tracker 
accumulates knowledge to provide more accurate diagnosis and 
targeted follow-up questions.

CONNECTIONS:
- Managed by 'MemoryManager' inside each session.
- Used by 'follow_up.py' to determine what information is missing.
- Used by 'retriever.py' to perform more precise, context-aware searches.
"""

from dataclasses import dataclass, field
from typing import Optional
from app.utils.text_utils import extract_crop_from_text, detect_language


@dataclass
class DialogueState:
    """
    Stores what the assistant knows about the current agricultural problem.

    Fields are set progressively as the farmer provides more information.
    None means the field is still unknown.
    """

    # Core agricultural context
    crop_name: Optional[str] = None       # e.g. "ಟೊಮ್ಯಾಟೊ"
    crop_type: Optional[str] = None       # e.g. "vegetable", "cereal"
    season: Optional[str] = None          # e.g. "kharif", "ರಾಗಿ ಕಾಲ"
    region: Optional[str] = None          # e.g. "North Karnataka"
    location: Optional[str] = None        # e.g. "Mandya", "Tumkur"

    # Problem context
    problem_type: Optional[str] = None    # e.g. "disease", "pest", "irrigation"
    symptoms: list[str] = field(default_factory=list)
    severity: Optional[str] = None        # e.g. "mild", "severe"
    
    # Deep Diagnostic Context
    crop_stage: Optional[str] = None      # e.g. "flowering", "seedling"
    affected_part: Optional[str] = None   # e.g. "leaves", "lower leaves", "stem"
    duration: Optional[str] = None        # e.g. "3 days", "since yesterday"
    pest_visible: Optional[str] = None    # e.g. "yes", "no", "white insects"
    soil_condition: Optional[str] = None  # e.g. "dry", "wet"
    soil_type: Optional[str] = None       # e.g. "red soil", "black cotton"
    irrigation_method: Optional[str] = None # e.g. "drip", "rainfed"
    risk_assessment: Optional[str] = None # e.g. "LOW", "MEDIUM", "HIGH"

    # Conversation meta
    detected_language: str = "kn"         # Language of the farmer's messages
    turn_count: int = 0                   # How many turns in this session

    # Flags
    crop_confirmed: bool = False          # Farmer explicitly confirmed crop
    problem_confirmed: bool = False       # Problem type identified
    awaiting_llm_permission: bool = False # Flag to track if waiting for LLM permission
    pending_llm_query: str = ""           # Pending query to fetch from LLM
    pending_question: Optional[str] = None # Tracks original user question when follow-up is asked

    # Conversational entity slots & intent tracking
    intent: Optional[str] = None          # e.g. "control", "symptoms", "fertilizer_recommendation", etc.
    pest_name: Optional[str] = None       # e.g. "ಕಾಂಡ ಕೊರಕ"
    disease_name: Optional[str] = None    # e.g. "ಡೌನಿ ಮಿಲ್ಡ್ಯೂ"
    fertilizer_name: Optional[str] = None # e.g. "ಯೂರಿಯಾ"
    pesticide_name: Optional[str] = None  # e.g. "ಕ್ಲೋರ್‌ಪೈರಿಫಾಸ್"

    # Farmer identity
    farmer_name: Optional[str] = None     # e.g. "Karan" — extracted when farmer introduces themselves

    # ── Update Methods ────────────────────────────────────────────────────────

    def reset_for_new_crop(self, new_crop: str):
        """
        Reset problem-specific slots when the farmer switches to a different crop.
        Prevents carrying over pests/diseases from the old crop.
        """
        self.crop_name = new_crop
        self.crop_confirmed = True
        self.problem_type = None
        self.symptoms = []
        self.severity = None
        self.problem_confirmed = False
        self.intent = None
        self.pest_name = None
        self.disease_name = None
        self.fertilizer_name = None
        self.pesticide_name = None

    def update_from_text(self, text: str):
        """
        Attempt to extract known fields from the farmer's text.

        This is a heuristic — the LLM handles complex extraction.
        Here we do simple pattern matching for common cases.

        Args:
            text: Farmer's latest message
        """
        self.turn_count += 1

        # Detect language
        self.detected_language = detect_language(text)

        # Try to extract crop name
        # We MUST update it even if it's already set, so the farmer can change crops!
        extracted_crop = extract_crop_from_text(text)
        if extracted_crop:
            if self.crop_name and self.crop_name.strip().lower() != extracted_crop.strip().lower():
                # Farmer switched crops! Reset old crop problem context
                self.reset_for_new_crop(extracted_crop)
            else:
                self.crop_name = extracted_crop
                self.crop_confirmed = True

        import re
        text_lower = text.lower()

        # Look for crop age / duration (e.g. "40 days", "45 ದಿನಗಳು")
        age_match = re.search(r'(\d+)\s*(days?|ದಿನಗಳು|ದಿನ|months?|ತಿಂಗಳು|weeks?|ವಾರ)', text_lower)
        if age_match:
            self.duration = age_match.group(0)

        # Look for symptom keywords (Kannada & English)
        symptom_keywords = {
            "ಹಳದಿ": "ಹಳದಿ ಎಲೆ (yellowing)",
            "yellow": "yellowing leaves (ಹಳದಿ ಎಲೆ)",
            "ಒಣಗು": "ಒಣಗುವಿಕೆ (wilting/drying)",
            "wilt": "wilting (ಒಣಗುವಿಕೆ)",
            "dry": "drying (ಒಣಗುವಿಕೆ)",
            "ಕಲೆ": "ಕಲೆಗಳು (spots/patches)",
            "spot": "spots (ಕಲೆಗಳು)",
            "ರಂಧ್ರ": "ರಂಧ್ರಗಳು (holes)",
            "hole": "holes (ರಂಧ್ರಗಳು)",
            "ಕೀಟ": "ಕೀಟ (insect damage)",
            "bug": "insect damage (ಕೀಟ)",
            "ರೋಗ": "ರೋಗ (disease)",
            "ಬಾಡು": "ಬಾಡುವಿಕೆ (drooping)",
            "curl": "leaf curl (ಎಲೆ ಮುದುರುವಿಕೆ)",
            "rot": "rotting (ಕೊಳೆತ)",
        }
        for keyword, symptom in symptom_keywords.items():
            if keyword in text_lower and symptom not in self.symptoms:
                self.symptoms.append(symptom)

        # Detect problem type and agricultural intent from keywords
        if not self.problem_type:
            if any(w in text_lower for w in ["ಕೀಟ", "ಹುಳ", "bug", "insect", "pest"]):
                self.problem_type = "pest"
                if not self.intent:
                    self.intent = "pest"
            elif any(w in text_lower for w in ["ರೋಗ", "disease", "ಶಿಲೀಂಧ್ರ", "fungus"]):
                self.problem_type = "disease"
                if not self.intent:
                    self.intent = "disease"
            elif any(w in text_lower for w in ["ನೀರು", "irrigation", "ನೀರಾವರಿ", "water"]):
                self.problem_type = "irrigation"
                if not self.intent:
                    self.intent = "irrigation"
            elif any(w in text_lower for w in ["ಗೊಬ್ಬರ", "fertilizer", "ಪೋಷಕಾಂಶ", "manure"]):
                self.problem_type = "fertilizer"
                if not self.intent:
                    self.intent = "fertilizer"

        # Detect high-level intents
        if not self.intent and any(w in text_lower for w in ["ಯೋಜನೆ", "ಸಹಾಯಧನ", "scheme", "subsidy", "subsidies", "ಬೆಂಬಲ ಬೆಲೆ", "msp"]):
            self.intent = "government_scheme"

        crisis_words = ["ಸಾಯಲು", "ಸಾಯಬೇಕು", "ಜೀವ ಕಳೆದುಕೊಳ್ಳ", "ಆತ್ಮಹತ್ಯೆ", "ಬದುಕಲು ಇಷ್ಟವಿಲ್ಲ", "ಬದುಕೋದು ಬೇಡ", "suicide", "kill myself", "end my life", "want to die"]
        if any(w in text_lower for w in crisis_words):
            self.intent = "crisis"
        elif any(w in text_lower for w in ["ಬೇಸರ", "ಟೆನ್ಶನ್", "ಒತ್ತಡ", "ಕಷ್ಟ", "ಸಾಧ್ಯವಿಲ್ಲ", "ಧೈರ್ಯ ಇಲ್ಲ", "ನೋವಾಗಿದೆ", "ಬೆಳೆ ಹಾಳಾಗಿದೆ", "stressed", "sad", "worried", "giving up", "feel down", "depressed"]):
            self.intent = "emotional_support"
        elif any(w in text_lower for w in ["ಧೈರ್ಯ ಹೇಳಿ", "motivation", "motivate me", "ಸ್ಫೂರ್ತಿ"]):
            self.intent = "motivation"
        elif any(w in text_lower for w in ["ಮುಂದುವರಿಸಬೇಕಾ", "ಬೇರೆ ಕೆಲಸ", "ಸಾಲ ಹೇಗೆ", "ಸಾಲ ತೀರಿಸ", "debt", "loan", "should i continue", "continue farming"]):
            self.intent = "personal_advice"
        elif any(w in text_lower for w in ["photosynthesis", "soil ph", "what is ai", "ai ಎಂದರೇನು", "ದ್ಯುತಿಸಂಶ್ಲೇಷಣೆ"]):
            self.intent = "agri_general_science"

        # Karnataka Districts Mapping for live weather & market location detection
        if not self.location:
            districts_map = {
                "ವಿಜಯಪುರ": "Vijayapura", "ಬಿಜಾಪುರ": "Vijayapura", "bijapur": "Vijayapura", "vijayapura": "Vijayapura",
                "ಬಾಗಲಕೋಟೆ": "Bagalkote", "bagalkot": "Bagalkote", "bagalkote": "Bagalkote",
                "ಬೆಳಗಾವಿ": "Belagavi", "belgaum": "Belagavi", "belagavi": "Belagavi",
                "ಬಳ್ಳಾರಿ": "Ballari", "bellary": "Ballari", "ballari": "Ballari",
                "ಬೀದರ್": "Bidar", "bidar": "Bidar",
                "ಕಲಬುರಗಿ": "Kalaburagi", "ಗುಲ್ಬರ್ಗ": "Kalaburagi", "gulbarga": "Kalaburagi", "kalaburagi": "Kalaburagi",
                "ಯಾದಗಿರಿ": "Yadgir", "yadgir": "Yadgir",
                "ರಾಯಚೂರು": "Raichur", "raichur": "Raichur",
                "ಕೊಪ್ಪಳ": "Koppal", "koppal": "Koppal",
                "ಗದಗ": "Gadag", "gadag": "Gadag",
                "ಧಾರವಾಡ": "Dharwad", "ಹುಬ್ಬಳ್ಳಿ": "Dharwad", "dharwad": "Dharwad", "hubli": "Dharwad", "hubballi": "Dharwad",
                "ಉತ್ತರ ಕನ್ನಡ": "Uttara Kannada", "ಕಾರವಾರ": "Uttara Kannada", "karwar": "Uttara Kannada", "uttara kannada": "Uttara Kannada",
                "ಹಾವೇರಿ": "Haveri", "haveri": "Haveri",
                "ಶಿವಮೊಗ್ಗ": "Shivamogga", "shimoga": "Shivamogga", "shivamogga": "Shivamogga",
                "ಉಡುಪಿ": "Udupi", "udupi": "Udupi",
                "ಚಿಕ್ಕಮಗಳೂರು": "Chikkamagaluru", "chikmagalur": "Chikkamagaluru", "chikkamagaluru": "Chikkamagaluru",
                "ದಕ್ಷಿಣ ಕನ್ನಡ": "Dakshina Kannada", "ಮಂಗಳೂರು": "Dakshina Kannada", "mangalore": "Dakshina Kannada", "mangaluru": "Dakshina Kannada",
                "ಹಾಸನ": "Hassan", "hassan": "Hassan",
                "ಕೊಡಗು": "Kodagu", "ಮಡಿಕೇರಿ": "Kodagu", "coorg": "Kodagu", "madikeri": "Kodagu", "kodagu": "Kodagu",
                "ಮೈಸೂರು": "Mysuru", "mysore": "Mysuru", "mysuru": "Mysuru",
                "ಚಾಮರಾಜನಗರ": "Chamarajanagar", "chamarajanagar": "Chamarajanagar",
                "ಮಂಡ್ಯ": "Mandya", "mandya": "Mandya",
                "ರಾಮನಗರ": "Ramanagara", "ramanagara": "Ramanagara", "ramanagar": "Ramanagara",
                "ಬೆಂಗಳೂರು": "Bengaluru", "bangalore": "Bengaluru", "bengaluru": "Bengaluru",
                "ಕೋಲಾರ": "Kolar", "kolar": "Kolar",
                "ಚಿಕ್ಕಬಳ್ಳಾಪುರ": "Chikkaballapura", "chikkaballapur": "Chikkaballapura", "chikkaballapura": "Chikkaballapura",
                "ತುಮಕೂರು": "Tumakuru", "tumkur": "Tumakuru", "tumakuru": "Tumakuru",
                "ಚಿತ್ರದುರ್ಗ": "Chitradurga", "chitradurga": "Chitradurga",
                "ದಾವಣಗೆರೆ": "Davanagere", "davangere": "Davanagere", "davanagere": "Davanagere",
                "ವಿಜಯನಗರ": "Vijayanagara", "ಹೊಸಪೇಟೆ": "Vijayanagara", "hospet": "Vijayanagara", "vijayanagara": "Vijayanagara",
            }
            for d_name, d_val in districts_map.items():
                if d_name in text_lower:
                    self.location = d_val
                    break

        # Detect weather intent (live weather / rain forecast / spray safety)
        weather_trigger_phrases = [
            "ಹವಾಮಾನ", "ಮುನ್ಸೂಚನೆ", "weather", "forecast", "ತಾಪಮಾನ",
            "ಮಳೆ ಬರುವ", "ಮಳೆಯಾಗುವ", "ಮಳೆ ಬರುತ್ತಾ", "ಮಳೆ ಬರಬಹುದಾ", "ಮಳೆ ಸಾಧ್ಯತೆ",
            "ಮಳೆ ಪ್ರಮಾಣ", "ಇಂದು ಮಳೆ", "ನಾಳೆ ಮಳೆ", "ಗಂಟೆಗಳಲ್ಲಿ ಮಳೆ", "ಮಳೆಯಾಗಲಿದೆಯೇ",
            "will it rain", "chance of rain", "rain forecast", "rain prediction", "rain today", "rain tomorrow"
        ]
        is_agronomic_query = any(k in text_lower for k in [
            "ಯಾವ ಹವಾಮಾನ", "ಸೂಕ್ತ ಹವಾಮಾನ", "ಬೆಳೆಯಲು ಹವಾಮಾನ", "climate requirement",
            "ಮಳೆಗಾಲದಲ್ಲಿ ರೋಗ", "ಮಳೆಗಾಲದ ಬೆಳೆ", "ಮಳೆಗಾಲದಲ್ಲಿ ಗೊಬ್ಬರ", "ಮಳೆಗಾಲದ ಕೀಟ",
            "ನೀರಾವರಿ ನಿರ್ವಹಣೆ", "ನಿರ್ವಹಣೆ ಹೇಗೆ", "ನೀರು ಹೇಗೆ", "ಹೇಗೆ ಮಾಡಬೇಕು", "ಏನು ಮಾಡಬೇಕು",
            "ಕ್ರಮಗಳು", "ಪರಿಹಾರ ಕ್ರಮ", "ಬೆಳೆಗಳಿಗೆ ನೀರಾವರಿ", "ತೋಟಗಾರಿಕಾ ಬೆಳೆ"
        ])
        if any(p in text_lower for p in weather_trigger_phrases) and not is_agronomic_query:
            self.intent = "weather"
        elif is_agronomic_query and any(k in text_lower for k in ["ನೀರಾವರಿ", "ನೀರು", "water", "irrigation"]):
            self.problem_type = "irrigation"
            self.intent = "irrigation"

    def update_from_llm(self, extracted: dict):
        """
        Update state from LLM-extracted entities.

        The LLM can extract structured information from complex text.
        This method merges those extractions into the state.

        Args:
            extracted: Dict with optional keys:
                       crop_name, season, region, symptoms, problem_type, intent,
                       pest_name, disease_name, fertilizer_name, pesticide_name
        """
        new_crop = extracted.get("crop_name")
        if new_crop and isinstance(new_crop, str) and new_crop.strip():
            new_crop = new_crop.strip()
            if self.crop_name and self.crop_name.strip().lower() != new_crop.lower():
                self.reset_for_new_crop(new_crop)
            else:
                self.crop_name = new_crop
                self.crop_confirmed = True

        if extracted.get("season") and not self.season:
            self.season = extracted["season"]

        if extracted.get("region") and not self.region:
            self.region = extracted["region"]
            
        if extracted.get("location"):
            self.location = extracted["location"]

        if extracted.get("symptoms"):
            for s in extracted["symptoms"]:
                if s not in self.symptoms:
                    self.symptoms.append(s)

        if extracted.get("problem_type") and not self.problem_type:
            self.problem_type = extracted["problem_type"]
            self.problem_confirmed = True

        # Conversational entity slots & intent updates
        if extracted.get("farmer_name") and isinstance(extracted["farmer_name"], str) and extracted["farmer_name"].strip():
            self.farmer_name = extracted["farmer_name"].strip().capitalize()

        if extracted.get("intent"):
            self.intent = extracted["intent"]
        if extracted.get("pest_name"):
            self.pest_name = extracted["pest_name"]
        if extracted.get("disease_name"):
            self.disease_name = extracted["disease_name"]
        if extracted.get("fertilizer_name"):
            self.fertilizer_name = extracted["fertilizer_name"]
        if extracted.get("pesticide_name"):
            self.pesticide_name = extracted["pesticide_name"]
            
        # Diagnostic deep-dive updates
        if extracted.get("crop_stage"):
            self.crop_stage = extracted["crop_stage"]
        if extracted.get("affected_part"):
            self.affected_part = extracted["affected_part"]
        if extracted.get("duration"):
            self.duration = extracted["duration"]
        if extracted.get("pest_visible"):
            self.pest_visible = extracted["pest_visible"]
        if extracted.get("soil_condition"):
            self.soil_condition = extracted["soil_condition"]
        if extracted.get("soil_type"):
            self.soil_type = extracted["soil_type"]
        if extracted.get("irrigation_method"):
            self.irrigation_method = extracted["irrigation_method"]

    # ── Query Methods ─────────────────────────────────────────────────────────

    def get_missing_fields(self) -> list[str]:
        """
        Return a list of key fields that are still unknown.

        Used by the follow-up question generator to decide
        what to ask the farmer next.

        Returns:
            List of field names that are None/empty
        """
        missing = []
        if not self.crop_name:
            missing.append("crop_name")
        if not self.symptoms and not self.problem_type:
            missing.append("symptoms")
        if not self.season:
            missing.append("season")
        if not self.region:
            missing.append("region")
        return missing

    def is_sufficient_for_retrieval(self) -> bool:
        """
        Check if enough context is available for meaningful retrieval.

        We need at least a crop name OR symptoms to retrieve relevant results.

        Returns:
            True if retrieval can be meaningfully performed
        """
        return bool(self.crop_name or self.symptoms or self.problem_type)

    def to_retrieval_query(self) -> str:
        """
        Build a rich retrieval query string from the current state.

        This enriches the farmer's raw query with known context
        for better FAISS retrieval accuracy.

        Returns:
            Enhanced query string
        """
        parts = []
        if self.crop_name:
            parts.append(self.crop_name)
        if self.problem_type:
            parts.append(self.problem_type)
        if self.symptoms:
            parts.extend(self.symptoms[:3])
        if self.season:
            parts.append(self.season)
        return " ".join(parts)

    def to_dict(self) -> dict:
        """Serialise state to a plain dict for storage in session memory."""
        return {
            "crop_name": self.crop_name,
            "crop_type": self.crop_type,
            "season": self.season,
            "region": self.region,
            "problem_type": self.problem_type,
            "symptoms": self.symptoms,
            "severity": self.severity,
            "detected_language": self.detected_language,
            "turn_count": self.turn_count,
            "crop_confirmed": self.crop_confirmed,
            "problem_confirmed": self.problem_confirmed,
            "awaiting_llm_permission": self.awaiting_llm_permission,
            "pending_llm_query": self.pending_llm_query,
            "intent": self.intent,
            "pest_name": self.pest_name,
            "disease_name": self.disease_name,
            "fertilizer_name": self.fertilizer_name,
            "crop_stage": self.crop_stage,
            "affected_part": self.affected_part,
            "duration": self.duration,
            "pest_visible": self.pest_visible,
            "soil_condition": self.soil_condition,
            "soil_type": self.soil_type,
            "irrigation_method": self.irrigation_method,
            "risk_assessment": self.risk_assessment
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DialogueState":
        """Restore state from a previously serialised dict."""
        state = cls()
        for key, value in data.items():
            if hasattr(state, key):
                setattr(state, key, value)
        return state
