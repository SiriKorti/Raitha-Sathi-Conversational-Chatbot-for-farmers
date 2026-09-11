"""
follow_up.py — Follow-Up Question Generator

WHAT IT DOES:
Decides if the assistant needs more information before it can provide 
a good answer. If so, it selects a relevant follow-up question in 
Kannada (e.g., asking for the crop name or specific symptoms).

WHY IT EXISTS:
Makes the assistant act like a helpful human advisor. If a farmer says 
"my plant is dying," the AI shouldn't just guess; it should ask 
"which plant?" to ensure the final advice is correct and safe.

CONNECTIONS:
- Called by 'response_generator.py' at the start of the RAG pipeline.
- Uses 'DialogueState' to see which fields are currently empty.
"""

from app.conversation.dialogue_state import DialogueState


class FollowUpGenerator:
    """
    Generates contextual follow-up questions in Kannada based on
    what information is still missing from the dialogue state.

    Priority order for missing fields:
    1. crop_name  — We need to know which crop before anything else
    2. symptoms   — Needed for disease/pest diagnosis
    3. season     — Important for seasonal disease patterns
    4. region     — Affects pest and disease recommendations

    The generator also uses the user's query text to ask more
    specific questions (e.g., if wilting is mentioned, ask about root health).
    """

    # ── Kannada question templates ────────────────────────────────────────────
    # Each key maps to a list of questions; one is selected based on context.

    # ── Kannada & English follow-up question templates ──────────────────────────
    # Formatted to sound like a caring, personal agricultural assistant (ChatGPT style).

    CROP_QUESTIONS_KN = [
        "ಯಾವ ಬೆಳೆ ಬೆಳೆಯುತ್ತಿದ್ದೀರಿ ಎಂದು ಹೇಳಿ. ಬೆಳೆ ತಿಳಿದರೆ ಅದಕ್ಕೆ ತಕ್ಕಂತೆ ನಿಖರವಾದ ಸಲಹೆ ನೀಡುತ್ತೇನೆ.",
        "ನಿಮ್ಮ ಬೆಳೆಯ ಹೆಸರನ್ನು ದಯವಿಟ್ಟು ತಿಳಿಸುವಿರಾ? ಬೆಳೆ ತಿಳಿದರೆ ಮಾತ್ರ ಸರಿಯಾದ ಪರಿಹಾರ ನೀಡಬಹುದು.",
    ]

    CROP_QUESTIONS_EN = [
        "To give you the exact advice, could you please tell me which crop you are growing?",
        "Could you please specify which crop is affected so I can provide the right solution?",
    ]

    SYMPTOM_QUESTIONS_KN = {
        "default": [
            "ನಿಮ್ಮ ಬೆಳೆಯಲ್ಲಿ ಸಮಸ್ಯೆಯನ್ನು ನಿಖರವಾಗಿ ಗುರುತಿಸಲು ಸಹಾಯ ಬೇಕಿದೆ 🔍. ಎಲೆಗಳಲ್ಲಿ ಹಳದಿ ಕಲೆ ಇದೆಯೇ, ಕಾಂಡ ಒಣಗುತ್ತಿದೆಯೇ ಅಥವಾ ಬೇರು ಕೊಳೆಯುತ್ತಿದೆಯೇ ಎಂದು ಸ್ವಲ್ಪ ವಿವರವಾಗಿ ತಿಳಿಸುವಿರಾ?",
        ],
        "disease": [
            "ನಿಮ್ಮ ಬೆಳೆ ಅನುಭವಿಸುತ್ತಿರುವ ರೋಗದ ಬಾಧೆಗೆ ಸೂಕ್ತ ಔಷಧ ಸೂಚಿಸಲು ಬಯಸುತ್ತೇನೆ 🌿. ಎಲೆಗಳಲ್ಲಿ ಕಪ್ಪು ಕಲೆ, ಹಳದಿ ಮಚ್ಚೆ ಅಥವಾ ಬೂದಿ ರೋಗದ ಲಕ್ಷಣಗಳು ಕಾಣಿಸುತ್ತಿವೆಯೇ? ವಿವರವಾಗಿ ತಿಳಿಸಿ.",
        ],
        "pest": [
            "ಕೀಟದ ಹಾವಳಿಯನ್ನು ಪರಿಣಾಮಕಾರಿಯಾಗಿ ತಡೆಗಟ್ಟಲು 🐛 ಎಲೆಗಳಲ್ಲಿ ರಂಧ್ರಗಳಿವೆಯೇ ಅಥವಾ ಯಾವುದೇ ಹುಳುಗಳು ಕಾಣಿಸಿಕೊಳ್ಳುತ್ತಿವೆಯೇ ತಿಳಿಸುವಿರಾ?",
        ],
        "wilting": [
            "ಬೆಳೆ ಒಣಗುತ್ತಿರುವ ಸಮಸ್ಯೆಗೆ 💧 ನೀರಾವರಿ ಅಥವಾ ಬೇರು ಕೊಳೆಯುವಿಕೆ ಕಾರಣವಾಗಿರಬಹುದು. ಮಣ್ಣು ಒದ್ದೆಯಾಗಿದೆಯೇ ಮತ್ತು ಬೇರಿನಲ್ಲಿ ಹುಳು ಅಥವಾ ಕೊಳೆತ ಕಾಣಿಸಿದೆಯೇ ಎಂದು ತಿಳಿಸುವಿರಾ?",
        ],
    }

    SYMPTOM_QUESTIONS_EN = {
        "default": [
            "To help identify the exact issue with your crop 🔍, could you describe what you see on the leaves, stem, or roots?",
        ],
        "disease": [
            "To suggest the right treatment for the disease 🌿, are there yellow spots, dark patches, or fungal growth on the leaves?",
        ],
        "pest": [
            "To help control the pest infestation 🐛, are there holes in the leaves, or any specific insects visible?",
        ],
        "wilting": [
            "For the drying/wilting problem 💧, is the soil overly wet or are the roots rotting? Please let me know so I can suggest the exact remedy.",
        ],
    }

    SEASON_QUESTIONS_KN = [
        "🌦️ ಪ್ರಸ್ತುತ ಋತುಮಾನ (ಮಳೆಗಾಲ, ಚಳಿಗಾಲ, ಅಥವಾ ಬೇಸಿಗೆ) ಮತ್ತು ನಿಮ್ಮ ಕೃಷಿ ಕಾಲವನ್ನು ತಿಳಿಸಿದರೆ ಋತುಮಾನಕ್ಕೆ ತಕ್ಕ ಉತ್ತಮ ಸಲಹೆ ನೀಡಲು ಅನುಕೂಲವಾಗುತ್ತದೆ.",
    ]

    SEASON_QUESTIONS_EN = [
        "🌦️ Could you let me know the current season or growing period? That will help me tailor the seasonal advice for your crop.",
    ]

    REGION_QUESTIONS_KN = [
        "📍 ನಿಮ್ಮ ಹೊಲ ಅಥವಾ ಜಮೀನು ಯಾವ ಜಿಲ್ಲೆ/ಪ್ರದೇಶದಲ್ಲಿದೆ ಎಂದು ತಿಳಿಸಿದರೆ ಸ್ಥಳೀಯ ಹವಾಮಾನಕ್ಕೆ ತಕ್ಕ ನಿಖರ ಸಲಹೆ ನೀಡಬಲ್ಲೆ.",
    ]

    REGION_QUESTIONS_EN = [
        "📍 Could you mention your district or region? This helps in providing region-specific agricultural recommendations.",
    ]

    def generate(
        self,
        state: DialogueState,
        user_query: str = "",
    ) -> str | None:
        """
        Generate the most appropriate follow-up question based on the
        current dialogue state and the user's latest query.
        """
        missing = state.get_missing_fields()

        if not missing:
            return None

        is_english = state.detected_language == "en"

        # ── Priority 1: Ask for crop name ────────────────────────────────────
        if "crop_name" in missing:
            return self._personalize(self._pick_crop_question(is_english), state, is_english)

        # ── Priority 1.5: Deep Diagnostic Question ───────────────────────────
        if state.symptoms and len(state.symptoms) < 2 and not state.affected_part and not state.pest_visible:
            # Dynamically ask about affected part or pests based on symptom
            if is_english:
                q = f"You mentioned {state.symptoms[0]}. To give you the best advice, could you tell me which part of the plant is affected (e.g., lower leaves, upper leaves) or if you see any insects?"
            else:
                q = f"ನೀವು {state.symptoms[0]} ಲಕ್ಷಣವನ್ನು ಹೇಳಿದ್ದೀರಿ. ನಿಖರ ಪರಿಹಾರಕ್ಕಾಗಿ, ಇದು ಗಿಡದ ಯಾವ ಭಾಗದಲ್ಲಿ (ಉದಾ: ಕೆಳಗಿನ ಎಲೆಗಳು, ಮೇಲಿನ ಎಲೆಗಳು, ಕಾಂಡ) ಕಾಣಿಸುತ್ತಿದೆ ಅಥವಾ ಏನಾದರೂ ಕೀಟಗಳು ಕಾಣಿಸುತ್ತಿವೆಯೇ ಎಂದು ತಿಳಿಸುವಿರಾ?"
            return self._personalize(q, state, is_english)

        # ── Priority 2: Ask for symptoms ─────────────────────────────────────
        if "symptoms" in missing:
            return self._personalize(self._pick_symptom_question(state, user_query, is_english), state, is_english)

        # ── Priority 3: Ask about season ─────────────────────────────────────
        if "season" in missing and state.turn_count >= 4:
            q = self.SEASON_QUESTIONS_EN[0] if is_english else self.SEASON_QUESTIONS_KN[0]
            return self._personalize(q, state, is_english)

        # ── Priority 4: Ask about region ─────────────────────────────────────
        if "region" in missing and state.turn_count >= 5:
            q = self.REGION_QUESTIONS_EN[0] if is_english else self.REGION_QUESTIONS_KN[0]
            return self._personalize(q, state, is_english)

        return None

    def _personalize(self, text: str, state: DialogueState, is_english: bool) -> str:
        """Personalize follow-up question with farmer's name when available."""
        if state and state.farmer_name:
            name = state.farmer_name
            if is_english:
                if "Dear farmer!" in text:
                    text = text.replace("Dear farmer!", f"Dear {name}!")
                elif "Dear Farmer!" in text:
                    text = text.replace("Dear Farmer!", f"Dear {name}!")
                elif name.lower() not in text.lower():
                    text = f"Dear {name}! 🌾 " + text.lstrip("🌾 ")
            else:
                if "ರೈತ ಬಾಂಧವರೇ" in text:
                    text = text.replace("ರೈತ ಬಾಂಧವರೇ", f"ನಮಸ್ಕಾರ {name} ಅವರೇ")
                elif f"{name} ಅವರೇ" not in text:
                    text = f"ನಮಸ್ಕಾರ {name} ಅವರೇ! 🌾 " + text.lstrip("🌾 ")
        return text

    def needs_followup(self, state: DialogueState) -> bool:
        """
        Decide if the assistant should ask a follow-up question
        instead of immediately generating a full answer.
        Follow-up questions are strictly reserved for direct crop diagnosis
        where missing information prevents safe, accurate advice.
        """
        non_followup_intents = {
            "emotional_support",
            "motivation",
            "personal_advice",
            "casual_greeting",
            "agri_general_science",
            "out_of_scope",
            "general_advisory",
            "weather",
            "government_scheme",
            "crisis",
        }
        if state.intent in non_followup_intents:
            return False

        # Only trigger crop follow-up if the user is asking about a problem, symptom, or treatment that genuinely requires a crop name
        crop_specific_intents = {
            "disease_management",
            "pesticide",
            "fertilizer",
            "symptoms",
            "control",
            "prevention",
            "identification",
        }

        # If crop_name is missing: only ask if it's explicitly a crop-specific problem or symptoms were mentioned
        if not state.crop_name and state.turn_count <= 4:
            if state.intent in crop_specific_intents or state.symptoms or state.problem_type:
                return True
            return False
            
        # If symptoms are present but we lack detail (deep diagnosis)
        # Only trigger symptom clarification if intent is symptom/disease identification,
        # NOT when the user has already requested management, control, treatment, or specific advice.
        if state.intent in ["identification", "symptoms"] and state.symptoms and len(state.symptoms) < 2 and state.turn_count <= 3:
            # If we don't have affected_part or pest_visible, it's highly ambiguous
            if not state.affected_part and not state.pest_visible:
                return True

        return False

    # ── Private helpers ───────────────────────────────────────────────────────

    def _pick_crop_question(self, is_english: bool = False) -> str:
        """Return a warm crop name question."""
        return self.CROP_QUESTIONS_EN[0] if is_english else self.CROP_QUESTIONS_KN[0]

    def _pick_symptom_question(self, state: DialogueState, query: str, is_english: bool = False) -> str:
        """
        Pick the most relevant symptom question based on available context.
        """
        symptom_dict = self.SYMPTOM_QUESTIONS_EN if is_english else self.SYMPTOM_QUESTIONS_KN

        if any(w in query.lower() for w in ["ಒಣಗು", "ಬಾಡು", "wilting", "drying"]):
            return symptom_dict["wilting"][0]

        if state.problem_type == "pest" or any(w in query.lower() for w in ["ಕೀಟ", "ಹುಳ", "pest", "insect"]):
            return symptom_dict["pest"][0]

        if state.problem_type == "disease" or any(w in query.lower() for w in ["ರೋಗ", "ಶಿಲೀಂಧ್ರ", "disease", "fungus"]):
            return symptom_dict["disease"][0]

        return symptom_dict["default"][0]
