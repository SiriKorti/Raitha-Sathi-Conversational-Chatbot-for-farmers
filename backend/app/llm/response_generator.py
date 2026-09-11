"""
response_generator.py — Unified LLM Response Generation Layer

WHAT IT DOES:
The primary "orchestrator" for the assistant's brain. It coordinates the
entire conversational RAG pipeline: from updating the dialogue state
and retrieving context to building the final prompt and calling the LLM.

Pipeline:
    User Query
    → Update dialogue state
    → Direct DB search (fastest path)
    → Check if follow-up is needed
    → FAISS semantic retrieval + confidence scoring
    → Build contextual prompt
    → LLM generation (Ollama → Gemini fallback)
    → Save to memory → Return response

WHY IT EXISTS:
Provides a single, clean interface for generating responses. Whether
the request comes from a REST API or a WebSocket, they both call this
module. This ensures consistent behavior and centralized error handling.

CONNECTIONS:
- Connects to 'app.rag.retriever' for semantic knowledge retrieval.
- Connects to 'app.rag.database_searcher' for direct DB lookup.
- Connects to 'app.llm.prompt_builder' for assembling LLM instructions.
- Connects to 'app.llm.ollama_client' (primary) and 'gemini_client' (fallback).
- Connects to 'app.conversation.session_manager' to read/write memory.
"""

import re
from typing import Optional, Dict, Any, List
from app.rag.retriever import Retriever
from app.conversation.dialogue_state import DialogueState
from app.rag.context_builder import ContextBuilder
from app.conversation.session_manager import SessionManager
from app.conversation.follow_up import FollowUpGenerator
from app.llm.prompt_builder import PromptBuilder
from app.rag.database_searcher import DatabaseSearcher
from app.llm.safety_validator import SafetyValidator
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import LLMConnectionError, LLMTimeoutError
from app.utils.text_utils import detect_language, clean_text, extract_crop_from_text
from app.services.weather_service import WeatherService
from app.services.mandi_service import MandiService
from app.services.scheme_service import SchemeService

# Minimum FAISS cosine-similarity score to consider a retrieval "confident"
# Below this threshold, FAISS context is considered unreliable.
# LLM will still be called but with a "general knowledge" note in the prompt.
RETRIEVAL_CONFIDENCE_THRESHOLD = 0.45

PREFIXES_TO_STRIP = [
    "⚠️ *ಹಕ್ಕುತ್ಯಾಗ: ಇದು AI ನಿಂದ ರಚಿಸಲಾದ ಉತ್ತರವಾಗಿದೆ. / Disclaimer: This is an AI-generated answer.*\n\n",
    "🦙 *Ollama ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... / Fetching answer from Ollama...*\n\n",
    "🌐 *Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... / Fetching answer from Gemini...*\n\n",
    "🌐 Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... / Fetching answer from Gemini...\n\n",
    "🦙 *Ollama ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... (Fallback) / Fetching answer from Ollama... (Fallback)*\n\n",
    "🌐 *Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... (Fallback) / Fetching answer from Gemini... (Fallback)*\n\n",
    "🌐 Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... (Fallback) / Fetching answer from Gemini... (Fallback)\n\n",
    "🦙 *Ollama ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ / Fetching answer from Ollama...*\n\n",
    "🌐 *Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ / Fetching answer from Gemini...*\n\n",
    "🌐 Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ / Fetching answer from Gemini...\n\n",
    "🌐 *Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... / Fetching answer from Gemini...*",
    "🌐 Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... / Fetching answer from Gemini...",
    "🦙 *Ollama ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... / Fetching answer from Ollama...*",
]


class ResponseGenerator:
    """
    Orchestrates the full conversational RAG pipeline.

    Routing priority:
    1. Direct database match (fastest, most accurate)
    2. FAISS semantic retrieval + LLM grounding
    3. LLM-only generation (Ollama primary, Gemini fallback)
    """

    def __init__(self, retriever: Retriever, session_manager: SessionManager):
        """
        Args:
            retriever:       Loaded Retriever instance (shared singleton)
            session_manager: SessionManager instance (shared singleton)
        """
        self.retriever = retriever
        self.session_manager = session_manager
        self.context_builder = ContextBuilder()
        self.follow_up_gen = FollowUpGenerator()
        self.prompt_builder = PromptBuilder()
        self.db_searcher = DatabaseSearcher()
        self._gemini = None  # Lazy-loaded
        self.safety_validator = SafetyValidator(call_llm_fn=self._call_llm)
        
        self.weather_service = WeatherService()
        self.mandi_service = MandiService()
        self.scheme_service = SchemeService()

        logger.info(
            "ResponseGenerator ready | DB entries={n}",
            n=self.db_searcher.get_entry_count()
        )


    def _build_effective_query(self, query: str, state: DialogueState, history: list[dict] = None) -> str:
        """
        Enhances the user's query with rich context from the current dialogue state.
        Instead of just pronouns, it includes extracted symptoms, fertilizers, and conditions
        to ensure FAISS and the Semantic Verifier have the full picture.
        """
        # Check if the user is answering a pending follow-up question or clarifying crop
        prev_q = getattr(state, "pending_question", None)
        if not prev_q and history and len(query.split()) <= 4:
            farmer_turns = [h["content"] for h in history if h.get("role") in ("farmer", "user")]
            if farmer_turns and len(farmer_turns) >= 2:
                prev_q = farmer_turns[-2]

        if prev_q and len(query.split()) <= 5:
            state.pending_question = None
            resolved_query = f"{prev_q} ({query})"
            if state.crop_name and state.crop_name not in resolved_query:
                resolved_query = f"{resolved_query} {state.crop_name}"
            logger.info("Fused conversation turn with previous user query: '{orig}' -> '{new}'", orig=query, new=resolved_query)
            return resolved_query

        context_additions = []
        if state.crop_name and state.crop_name not in query:
            context_additions.append(state.crop_name)

        # Add other critical context if it's a short continuation query
        is_continuation = len(query.split()) <= 5 or any(p in query.lower() for p in ['ಇದು', 'ಇದಕ್ಕೆ', 'ಇದನ್ನು', 'ಅದಕ್ಕೆ', 'ಅದು', 'ಅದನ್ನು', 'it', 'this', 'that'])
        
        if is_continuation:
            if state.duration and state.duration not in query:
                context_additions.append(state.duration)
            if state.symptoms:
                context_additions.extend([s for s in state.symptoms if s not in query])
            if state.pest_name and state.pest_name not in query:
                context_additions.append(state.pest_name)
            if state.disease_name and state.disease_name not in query:
                context_additions.append(state.disease_name)
            if state.fertilizer_name and state.fertilizer_name not in query:
                context_additions.append(state.fertilizer_name)
            if state.soil_condition and state.soil_condition not in query:
                context_additions.append(state.soil_condition)
                
        if context_additions:
            resolved_query = f"{query} {' '.join(context_additions)}"
            logger.info("Built effective query: '{orig}' -> '{new}'", orig=query, new=resolved_query)
            return resolved_query

        return query

    async def _extract_entities_and_intent(self, query: str, history: list[dict]) -> dict:
        """
        Call Gemini / LLM to extract crop_name, intent, pest_name, disease_name, fertilizer_name, pesticide_name, and symptoms.
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
            "CRITICAL: Clearly understand the farmer's true underlying agricultural intent, even if they use casual, colloquial, or indirect phrasing.\n"
            "If the user is using pronouns like 'it', 'this', 'that', or 'ಅದು', 'ಇದಕ್ಕೆ', 'ಅದನ್ನು' to refer to a previously mentioned crop, pest, or disease in the conversation, resolve it using the history.\n\n"
            "=== Conversation History ===\n"
            f"{formatted_history}\n\n"
            "=== User Query ===\n"
            f"\"{query}\"\n\n"
            "- \"crop_name\": Specific crop name if mentioned in Kannada or English (e.g. \"ಮೂಲಂಗಿ\", \"ರಾಗಿ\", \"Tomato\", \"Radish\"), else null.\n"
            "- \"farmer_name\": If the user mentions their name (e.g. \"My name is Karan\", \"ನನ್ನ ಹೆಸರು ರಮೇಶ್\"), extract their name, else null.\n"
            "- \"intent\": One of: \"prevention\", \"control\", \"symptoms\", \"identification\", \"fertilizer\", \"irrigation\", \"harvesting\", \"spacing\", \"sowing\", \"disease_management\", \"pesticide\", \"weather\", \"market_price\", \"government_scheme\", \"greeting\", \"casual_greeting\", \"emotional_support\", \"motivation\", \"personal_advice\", \"agri_general_science\", \"out_of_scope\", \"crisis\", \"mixed\", \"general_advisory\", or null.\n"
            "- \"pest_name\": Specific insect/pest name if mentioned, else null.\n"
            "- \"disease_name\": Specific disease name if mentioned, else null.\n"
            "- \"fertilizer_name\": Specific fertilizer name if mentioned, else null.\n"
            "- \"pesticide_name\": Specific pesticide/chemical name if mentioned, else null.\n"
            "- \"symptoms\": List of symptoms mentioned (e.g. ಹಳದಿ ಎಲೆ, ಒಣಗುವಿಕೆ, ರಂಧ್ರಗಳು) else empty list.\n"
            "- \"crop_stage\": Growth stage if mentioned (e.g. seedling, flowering, harvesting), else null.\n"
            "- \"affected_part\": Plant part affected if mentioned (e.g. lower leaves, stem, root), else null.\n"
            "- \"duration\": How long the problem has been visible or age of crop (e.g. 40 days, 45 ದಿನಗಳು), else null.\n"
            "- \"pest_visible\": Are pests visible? (yes/no/description), else null.\n"
            "- \"soil_condition\": Current soil moisture if mentioned (e.g. dry, wet), else null.\n"
            "- \"soil_type\": Type of soil if mentioned (e.g. red soil, black soil), else null.\n"
            "- \"irrigation_method\": Method of irrigation if mentioned (e.g. drip, sprinkler), else null.\n"
            "- \"location\": District or city name if mentioned (e.g. Mandya, Tumkur), else null.\n\n"
            "Do not include markdown tags like ```json or any explanation, just return the JSON object."
        )
        try:
            raw_response, _ = await self._call_llm(prompt)
            cleaned = raw_response.strip()
            
            # Find the JSON block between curly braces
            import re
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(0)
            
            import json
            extracted = json.loads(cleaned)
            logger.info("Extracted entities & intent: {e}", e=extracted)
            return extracted
        except Exception as e:
            logger.error("Failed to extract entities/intent: {e}. Raw response was: {r}", e=e, r=cleaned if 'cleaned' in locals() else 'None')
            return {}

    async def _verify_semantic_match(self, user_query: str, retrieved_question: str) -> bool:
        """
        Verify if the retrieved database question matches the user's intent and crop context.
        """
        prompt = (
            "You are an expert agricultural semantic match verifier.\n\n"
            f"User Query: \"{user_query}\"\n"
            f"Database Candidate Question: \"{retrieved_question}\"\n\n"
            "Your task: Determine if the Database Candidate covers the same specific topic for the same crop and can be used to directly answer the User Query.\n\n"
            "RULES:\n"
            "1. SAME CROP: Both must refer to the same crop (or both be general agricultural queries).\n"
            "2. RELATED INTENT: The database question must address the same user intent (e.g. both ask about pest control, both ask about sowing, or both ask about fertilizer dosage).\n"
            "3. KANGLISH/TRANSLITERATION: Treat English, Kannada, and transliterated Kannada (Kanglish, e.g., 'suryakanthi' and 'ಸೂರ್ಯಕಾಂತಿ') as equivalent.\n"
            "4. ACCEPT if the database question answers the user query, even if the phrasing is slightly different or the database question is broader.\n"
            "5. Output EXACTLY 'YES' or 'NO' and nothing else."
        )
        try:
            res, _ = await self._call_llm(prompt)
            cleaned = res.strip().upper()
            logger.info("Semantic verification response: {c} for '{q1}' vs '{q2}'", c=cleaned, q1=user_query[:30], q2=retrieved_question[:30])
            return "YES" in cleaned
        except Exception as e:
            logger.error("Semantic verification failed: {e}", e=e)
            return False

    async def _format_db_answer_conversationally(self, user_query: str, db_answer: str, state: DialogueState, is_voice_mode: bool = False, language: str = "kn") -> str:
        """
        Use the LLM to format the verified database answer warmly and conversationally,
        addressing the farmer sweetly without introducing any external facts or hallucinations.
        """
        is_english = (language == "en" or state.detected_language == "en")
        name = state.farmer_name

        prompt = (
            "You are \"Raitha Sathi\" (🌾 ರೈತ ಸಾಥಿ) — a warm, patient, and highly knowledgeable agricultural officer and personal assistant for Karnataka farmers. Speak like a trusted local officer: respectful, patient, and practical.\n\n"
            "The farmer asked:\n"
            f"\"{user_query}\"\n\n"
            "Here is the verified FACTUAL solution from our database:\n"
            "---------------------------------------\n"
            f"{db_answer}\n"
            "---------------------------------------\n\n"
            "Your task is to rephrase and format this database answer into a warm, helpful, and polite response following these strict rules:\n"
            f"1. Address the farmer by name if known (e.g. \"ನಮಸ್ಕಾರ {name} ಅವರೇ!\" or \"Dear {name}!\"). If name is not known, address them with respect as \"ಕೃಷಿ ಬಾಂಧವರೇ\" or \"Dear Farmer\". Always use respectful honorifics.\n"
            "2. Keep the vocabulary simple and regionally familiar. Avoid literary or overly formal Kannada, and avoid technical English jargon—explain terms in plain language if you must use them (e.g. say 'nitrogen gobbara' alongside 'nitrogen fertilizer').\n"
            "3. State all numbers, prices, dates, and units clearly and unambiguously since these may be read aloud (e.g. write '500 rupees' instead of '₹500', '10 kilograms' instead of '10kg').\n"
            f"4. You MUST respond EXCLUSIVELY in {'English' if is_english else 'Kannada (ಕನ್ನಡ script)'}. Do not mix languages.\n"

            "5. STRICT DATABASE ADHERENCE: You MUST understand the provided database text completely and answer strictly in accordance with it. Treat the provided database text as the absolute truth. DO NOT add any external facts, dosages, advice, or chemical names. If the database answer is missing details, state that you are not fully sure and suggest they verify with their local Krishi Kendra.\n"
            f"6. {'Do NOT use markdown. Keep the answer brief. Spell out numbers as words.' if is_voice_mode else 'Use light formatting with short bullet points and bold key terms since it is read on a screen. Keep it scannable.'}\n"
            "Response:"
        )
        try:
            formatted_ans, _ = await self._call_llm(prompt)
            if formatted_ans and len(formatted_ans.strip()) > 20:
                return formatted_ans.strip()
        except Exception as e:
            logger.error("Failed to format DB answer conversationally: {e}", e=e)

        # Fallback if LLM formatting fails
        if name:
            greeting_prefix = f"Dear {name}! 🌾 " if is_english else f"ನಮಸ್ಕಾರ {name} ಅವರೇ! 🌾 "
            return f"{greeting_prefix}{db_answer}"
        return db_answer

    def _build_case1_response(
        self,
        db_entry: dict,
        farmer_name: Optional[str] = None,
        is_english: bool = False,
        is_voice_mode: bool = False,
    ) -> str:
        """
        Builds the complete, structured Case 1 Gold Standard response from
        the matched database record using purely verified DB fields.
        """
        # 1. Greeting
        if is_english:
            greeting = f"Dear {farmer_name}! 🌾\n\n" if farmer_name else "Hello Farmer! 🌾\n\n"
        else:
            greeting = f"ನಮಸ್ಕಾರ {farmer_name} ಅವರೇ! 🌾\n\n" if farmer_name else "ನಮಸ್ಕಾರ ಕೃಷಿ ಬಾಂಧವರೇ! 🌾\n\n"

        # 2. Topic & Crop
        crop_display = db_entry.get("crop_name", "").split("(")[0].strip()
        if not is_english:
            topic = db_entry.get("topic") or db_entry.get("subtopic") or ""
        else:
            topic = db_entry.get("subtopic") or db_entry.get("topic") or ""

        # 3. Intro sentence
        if is_english:
            if crop_display and topic:
                intro = f"Proper **{topic}** for **{crop_display}** is essential for healthy crop growth and optimal yield. Here is the verified information for your question:\n\n"
            elif crop_display:
                intro = f"Here is the verified information you need regarding **{crop_display}**:\n\n"
            else:
                intro = "Here is the verified information for your question:\n\n"
        else:
            if crop_display and topic:
                intro = f"**{crop_display}** ಬೆಳೆಯಲ್ಲಿ **{topic}** ಉತ್ತಮ ಬೆಳವಣಿಗೆ ಮತ್ತು ಇಳುವರಿಗೆ ಬಹಳ ಮುಖ್ಯ. ನೀವು ಕೇಳಿರುವ ಪ್ರಶ್ನೆಗೆ ಅಗತ್ಯವಾದ ಮಾಹಿತಿ ಇಲ್ಲಿದೆ:\n\n"
            elif crop_display:
                intro = f"**{crop_display}** ಕುರಿತು ನೀವು ಕೇಳಿರುವ ಪ್ರಶ್ನೆಗೆ ಅಗತ್ಯವಾದ ಮಾಹಿತಿ ಇಲ್ಲಿದೆ:\n\n"
            else:
                intro = "ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಅಗತ್ಯವಾದ ಮಾಹಿತಿ ಇಲ್ಲಿದೆ:\n\n"

        # 4. Main Solution text
        solution = db_entry.get("solution") or {}
        if isinstance(solution, dict):
            short = solution.get("short_answer", "").strip()
            detailed = solution.get("detailed_answer", "").strip()
            primary_answer = detailed if len(detailed) >= len(short) else short
            if not primary_answer:
                primary_answer = short or detailed or db_entry.get("answer", "")
        elif isinstance(db_entry.get("answer"), str):
            primary_answer = db_entry.get("answer", "").strip()
            solution = {}
        else:
            primary_answer = ""

        sections = []
        if primary_answer:
            sections.append(primary_answer)

        # 5. Environmental Conditions / Context
        context = db_entry.get("context") or {}
        if isinstance(context, dict):
            cond_lines = []
            field_labels = {
                "soil_type": ("Soil Type", "ಮಣ್ಣಿನ ವಿಧ"),
                "climate": ("Climate", "ಹವಾಮಾನ"),
                "temperature": ("Temperature", "ಸೂಕ್ತ ತಾಪಮಾನ"),
                "rainfall": ("Rainfall", "ವಾರ್ಷಿಕ ಮಳೆ ಪ್ರಮಾಣ"),
                "crop_stage": ("Crop Stage", "ಬೆಳೆಯ ಹಂತ"),
            }
            for k, (en_lbl, kn_lbl) in field_labels.items():
                val = context.get(k)
                if val and str(val).strip().lower() not in ("", "none", "null", "general"):
                    lbl = en_lbl if is_english else kn_lbl
                    cond_lines.append(f"  • **{lbl}:** {val}  ")

            if cond_lines:
                hdr = "• **Favorable Growing Conditions / Environment:**  " if is_english else "• **ಬೆಳವಣಿಗೆಗೆ ಅನುಕೂಲಕರ ಪರಿಸ್ಥಿತಿಗಳು:**  "
                sections.append(f"{hdr}\n" + "\n".join(cond_lines))

        # 6. Step-by-Step Instructions
        steps = solution.get("step_by_step") if isinstance(solution, dict) else None
        if steps and isinstance(steps, list):
            clean_steps = [s.strip() for s in steps if s and s.strip()]
            all_fragments = all(s in primary_answer for s in clean_steps)
            if not all_fragments and clean_steps != [primary_answer]:
                hdr = "• **Step-by-Step Instructions:**  " if is_english else "• **ಹಂತ ಹಂತವಾಗಿ ಕೈಗೊಳ್ಳಬೇಕಾದ ಕ್ರಮಗಳು:**  "
                step_lines = [f"  {i}. {s}  " for i, s in enumerate(clean_steps[:6], 1)]
                sections.append(f"{hdr}\n" + "\n".join(step_lines))

        # 7. Preventive Measures
        prevent = solution.get("preventive_measures") if isinstance(solution, dict) else None
        if prevent and isinstance(prevent, list):
            clean_prev = [p.strip() for p in prevent if p and p.strip()]
            if clean_prev:
                hdr = "• **Preventive Measures:**  " if is_english else "• **ತಡೆಗಟ್ಟುವ ಕ್ರಮಗಳು:**  "
                prev_lines = [f"  • {p}  " for p in clean_prev[:4]]
                sections.append(f"{hdr}\n" + "\n".join(prev_lines))

        # 8. Organic Solutions
        organic = solution.get("organic_solutions") if isinstance(solution, dict) else None
        if organic and isinstance(organic, list):
            clean_org = [o.strip() for o in organic if o and o.strip()]
            if clean_org:
                hdr = "• **Organic Solutions:**  " if is_english else "• **ಸಾವಯವ ಪರಿಹಾರ:**  "
                org_lines = [f"  • {o}  " for o in clean_org[:3]]
                sections.append(f"{hdr}\n" + "\n".join(org_lines))

        # 9. Warnings / Key Considerations
        warnings = solution.get("warnings") if isinstance(solution, dict) else None
        if warnings and isinstance(warnings, list):
            clean_warn = [w.strip() for w in warnings if w and w.strip()]
            if clean_warn:
                hdr = "• **Key Considerations & Warnings:**  " if is_english else "• **ಗಮನಿಸಬೇಕಾದ ಅಂಶಗಳು & ಎಚ್ಚರಿಕೆ:**  "
                warn_lines = [f"  • {w}  " for w in clean_warn[:3]]
                sections.append(f"{hdr}\n" + "\n".join(warn_lines))

        # 10. Recommended Products
        products = solution.get("recommended_products") if isinstance(solution, dict) else None
        if products and isinstance(products, list):
            clean_prod = [p.strip() for p in products if p and p.strip()]
            # Filter out non-product strings like district names or traits
            non_product_terms = ["ತುಮಕೂರು", "ಹಾಸನ", "ಮೈಸೂರು", "ಬೆಂಗಳೂರು", "Karnataka", "ಹೆಚ್ಚು", "ಕಡಿಮೆ", "ಗುಣಮಟ್ಟ"]
            actual_prods = [p for p in clean_prod if not any(term in p for term in non_product_terms)]
            if actual_prods:
                hdr = "• **Recommended Inputs / Products:**  " if is_english else "• **ಶಿಫಾರಸು ಮಾಡಿದ ಉತ್ಪನ್ನಗಳು:**  "
                prod_lines = [f"  • {p}  " for p in actual_prods[:3]]
                sections.append(f"{hdr}\n" + "\n".join(prod_lines))

        body = "\n\n".join(sections)

        # 11. Explainability Metadata Footer
        footer = ""
        if not is_voice_mode:
            meta = db_entry.get("metadata") or {}
            source_val = meta.get("source", "Agricultural Knowledge Dataset")
            meta_items = [
                f"📚 **Source:** {source_val}",
                "✓ **Verified Evidence**",
                "🎯 **Confidence:** HIGH",
            ]
            if meta.get("last_updated"):
                meta_items.append(f"🗓 **Last updated:** {meta.get('last_updated')}")
            # Double trailing spaces ensure line-breaks in CommonMark / GFM markdown
            footer = "\n\n---\n\n" + "  \n".join(meta_items) + "\n"

        return f"{greeting}{intro}{body}{footer}"

    async def _verify_semantic_candidates(
        self,
        user_query: str,
        candidates: list[dict],
        crop_name: Optional[str] = None
    ) -> Optional[dict]:
        """
        Verify candidate records from semantic retrieval against user intent.
        Rejects spurious candidates (e.g. bio-fertilizer seed treatment when user asks
        about ragi fertilizer dosage; variety questions when user asks about irrigation timing).
        """
        if not candidates:
            return None

        # Build candidate prompt without confusing ID prefix
        candidate_list_text = "\n".join([
            f"Candidate {i+1}: Question: \"{c.get('question')}\" | Topic: {c.get('topic')} / {c.get('subtopic')}"
            for i, c in enumerate(candidates[:8])
        ])

        prompt = (
            "You are an agricultural intent verification expert for Raitha Sathi.\n"
            f"User Query: \"{user_query}\"\n"
            f"Crop: {crop_name or 'General'}\n\n"
            "Here are candidate database records retrieved by vector search:\n"
            f"{candidate_list_text}\n\n"
            "TASK:\n"
            f"Determine which candidate (1 to {len(candidates[:8])}) truly and specifically answers the user's intended question.\n"
            "CRITICAL RULES:\n"
            "1. CROP SAFETY: The candidate must match the user's crop.\n"
            "2. INTENT FIDELITY: If user asks about watering/irrigation timing, choose the irrigation timing question, not variety selection or fertilizer.\n"
            "3. SPECIFICITY: If user asks what fertilizer to use for a crop (e.g., ragi), choose the primary chemical/NPK fertilizer dosage question, NOT seed treatment (bio-fertilizer), stem nutrients, or drought stress.\n"
            "4. If user asks about minimum support price (MSP), government procurement, or subsidy, choose the MSP/procurement/scheme question.\n"
            f"5. Output ONLY the candidate number (e.g. '1', '2', up to '{len(candidates[:8])}'). If NONE of the candidates match the user's intent, output 'NONE'.\n"
            "Answer (number only):"
        )
        try:
            res, _ = await self._call_llm(prompt)
            res_clean = res.strip()
            # 1. Match by candidate index (1 to N)
            for token in res_clean.split():
                if token.isdigit():
                    num = int(token)
                    if 1 <= num <= len(candidates[:8]):
                        selected_idx = num - 1
                        logger.info("✓ Case 2 Semantic match verified by index {idx}: {q}", idx=num, q=candidates[selected_idx].get("question"))
                        return candidates[selected_idx]
            # 2. Fallback: match by record ID in case LLM outputted record ID
            for token in res_clean.split():
                if token.isdigit():
                    num = int(token)
                    for cand in candidates[:8]:
                        if cand.get("id") == num:
                            logger.info("✓ Case 2 Semantic match verified by ID {id}: {q}", id=num, q=cand.get("question"))
                            return cand
            logger.info("Case 2 candidates rejected by verifier (output={o})", o=res_clean)
            return None
        except Exception as e:
            logger.error("Candidate verification failed: {e}", e=e)
            top_cand = candidates[0]
            if top_cand.get("_score", 0.0) >= 0.70:
                return top_cand
            return None

    async def _build_case2_response(
        self,
        db_entry: dict,
        user_query: str,
        farmer_name: Optional[str] = None,
        is_english: bool = False,
        is_voice_mode: bool = False,
    ) -> str:
        """
        Builds the complete Gold Standard Case 2 response from the verified semantic
        database match. Strictly grounded in DB facts with full explainability metadata.
        """
        meta = db_entry.get("metadata") or {}
        source_val = meta.get("source", "Agricultural Knowledge Dataset")
        last_updated = meta.get("last_updated", "2026-05-08")
        footer = ""
        if not is_voice_mode:
            meta_items = [
                f"📚 **Source:** {source_val}",
                "✓ **Verified Evidence**",
                "🎯 **Confidence:** HIGH",
            ]
            if last_updated:
                meta_items.append(f"🗓 **Last updated:** {last_updated}")
            footer = "\n\n---\n\n" + "  \n".join(meta_items) + "\n"

        solution = db_entry.get("solution") or {}
        crop_raw = db_entry.get("crop_name", "")
        EN_CROP_MAP = {
            "ರಾಗಿ": "Ragi (Finger Millet)",
            "ತೆಂಗು": "Coconut",
            "ಮೆಕ್ಕೆಜೋಳ": "Maize / Corn",
            "ಕಡಲೆ": "Chickpea / Bengal Gram",
            "ಭತ್ತ": "Paddy / Rice",
            "ಹತ್ತಿ": "Cotton",
            "ಕಬ್ಬು": "Sugarcane",
            "ತೊಗರಿ": "Pigeon Pea / Red Gram",
            "ಶೇಂಗಾ": "Groundnut",
            "ಈರುಳ್ಳಿ": "Onion",
            "ಟೊಮೆಟೊ": "Tomato",
            "ಮೆಣಸಿನಕಾಯಿ": "Chilli",
            "ಅಡಿಕೆ": "Arecanut",
            "ಕಾಫಿ": "Coffee",
            "ಬಾಳೆ": "Banana",
        }
        if is_english:
            crop_display = EN_CROP_MAP.get(crop_raw.strip(), crop_raw)
        else:
            crop_display = crop_raw.split("(")[0].strip()
        topic = db_entry.get("subtopic") or db_entry.get("topic") or ""

        if is_english:
            prompt = (
                "You are \"Raitha Sathi\" (🌾 ರೈತ ಸಾಥಿ) — an expert agricultural officer and personal assistant for Karnataka farmers.\n"
                "The farmer asked in English:\n"
                f"\"{user_query}\"\n\n"
                "Here is the verified FACTUAL database record from our agricultural knowledge dataset:\n"
                "--------------------------------------------------\n"
                f"Crop: {crop_display}\n"
                f"Topic: {topic}\n"
                f"Primary Solution: {solution.get('detailed_answer') or solution.get('short_answer') or db_entry.get('answer', '')}\n"
                f"Step-by-step instructions: {solution.get('step_by_step')}\n"
                f"Preventive measures: {solution.get('preventive_measures')}\n"
                f"Warnings: {solution.get('warnings')}\n"
                f"Recommended products: {solution.get('recommended_products')}\n"
                "--------------------------------------------------\n\n"
                "TASK: Present this verified database solution in clear, professional, farmer-friendly English following these strict rules:\n"
                f"1. GREETING: Start with 'Dear {farmer_name}! 🌾\\n\\n' if farmer name is known, else 'Dear Farmer! 🌾\\n\\n'.\n"
                f"2. INTRO: A short natural sentence: 'Proper **{topic}** for **{crop_display}** is essential for healthy crop growth and optimal yield. Here is the verified information for your question:\\n\\n'.\n"
                "3. MAIN ANSWER: Clear, comprehensive explanation using the verified database solution.\n"
                "4. STRUCTURED BULLETS: Include bullet points for step-by-step instructions, preventive measures, or warnings if provided in the data.\n"
                "5. STRICT FACTUALITY: Do NOT introduce any facts, dosages, or advice not present in the record.\n"
                "Response:"
            )
            try:
                res, _ = await self._call_llm(prompt)
                clean_body = res.strip()
                if clean_body:
                    return f"{clean_body}{footer}"
            except Exception as e:
                logger.error("English Case 2 LLM formatting failed: {e}", e=e)

        # Pure Kannada formatting (uses exact Gold Standard structure identical to Case 1)
        return self._build_case1_response(
            db_entry=db_entry,
            farmer_name=farmer_name,
            is_english=False,
            is_voice_mode=is_voice_mode,
        )

    # ── Main Generate Methods ─────────────────────────────────────────

    # Sentinel appended to the stream when Case 1 (direct DB match) is used.
    # Stripped from the final response text before returning to the caller.
    _DB_MATCH_SENTINEL = "\x00__DB_MATCH__\x00"

    async def generate(
        self,
        session_id: str,
        user_query: str,
        is_voice_mode: bool = False,
        language: str = "kn",
        user_id: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Non-streaming response generation.

        Detects whether the response came from a direct DB match (Case 1)
        via a sentinel appended by generate_stream(), then sets the correct
        source field ('database') so the frontend shows the right badge.
        """
        full_tokens = []
        async for token in self.generate_stream(
            session_id=session_id,
            user_query=user_query,
            is_voice_mode=is_voice_mode,
            language=language,
            user_id=user_id,
            **kwargs
        ):
            full_tokens.append(token)

        full_text = "".join(full_tokens)
        state = self.session_manager.get_state(session_id, user_id=user_id)

        # Detect Case 1 / Case 2 (exact or semantic DB match) via sentinel and strip it.
        is_db_match = self._DB_MATCH_SENTINEL in full_text
        if is_db_match:
            full_text = full_text.replace(self._DB_MATCH_SENTINEL, "")

        return {
            "response": full_text.strip(),
            "is_followup": False,
            "context_used": is_db_match,
            "retrieved_count": 1 if is_db_match else 0,
            "source": "database" if is_db_match else "llm",
            "confidence": 0.9 if is_db_match else 0.85,
            "provider": "database" if is_db_match else "gemini",
            "metadata": {"state": state.to_dict() if state else {}},
        }

    async def generate_stream(
        self,
        session_id: str,
        user_query: str,
        is_voice_mode: bool = False,
        language: str = "kn",
        user_id: Optional[str] = None,
        **kwargs
    ):
        """
        Streaming version of generate() -- yields tokens as they arrive.
        """
        self.session_manager.add_user_turn(session_id, user_query, user_id=user_id)
        state = self.session_manager.get_state(session_id, user_id=user_id)
        history = self.session_manager.get_recent_history(session_id, n=5, user_id=user_id)

        # Step 1.0: Detect language from the CURRENT query immediately (CRITICAL)
        from app.utils.text_utils import detect_language as _detect_lang
        detected = _detect_lang(user_query)
        if detected == "mixed":
            latin_chars = sum(1 for c in user_query if c.isascii() and c.isalpha())
            total_alpha = sum(1 for c in user_query if c.isalpha())
            detected = "en" if total_alpha > 0 and latin_chars / total_alpha >= 0.5 else "kn"
        
        effective_lang = "en" if (language == "en" or detected == "en") else "kn"
        state.detected_language = effective_lang
        is_english = (effective_lang == "en")
        logger.info("Detected language: {lang} (effective: {eff}) | query={q}", lang=detected, eff=effective_lang, q=user_query[:50])

        # Step 1.0.1: Fast Greeting Interceptor (Immediate warm response in < 0.05 seconds)
        punct_chars = " ,.!?–—;:\"'()[]{}।\t\n"
        tokens = [t.strip(punct_chars).lower() for t in user_query.split()]
        tokens = [t for t in tokens if t]
        greeting_words = {
            "hi", "hello", "hey", "namaskara", "namaste", "good morning", "good evening", "good afternoon",
            "ನಮಸ್ಕಾರ", "ಹಲೋ", "ಶುಭೋದಯ", "ನಮಸ್ತೆ", "ಹಾಯ್", "ಸುಪ್ರಭಾತ"
        }
        has_greeting_word = any(t in greeting_words for t in tokens)
        has_agri_topic = any(topic in user_query.lower() for topic in [
            "ಬೆಳೆ", "ರೋಗ", "ಗೊಬ್ಬರ", "ಬೆಲೆ", "ಹವಾಮಾನ", "ಕ್ರಿಮಿನಾಶಕ", "ಔಷಧ", "ಇಳುವರಿ",
            "crop", "disease", "fertilizer", "price", "weather", "pesticide", "yield", "seed"
        ])
        is_simple_greeting = has_greeting_word and not has_agri_topic and len(tokens) <= 5

        if is_simple_greeting:
            name = state.farmer_name
            if is_english:
                greeting_msg = (
                    f"Hello {name}! 🌾 Welcome to Raitha Sathi. How are you doing today? "
                    "We can discuss your crops, farming decisions, or simply talk about how things are going on your farm. What's on your mind? 😊" if name else
                    "Hello! 🌾 Welcome to Raitha Sathi, your personal farming companion. How are you doing today? "
                    "We can discuss your crops, farming decisions, or just catch up on how things are going on your farm. What's on your mind? 😊"
                )
            else:
                greeting_msg = (
                    f"ನಮಸ್ಕಾರ {name} ಅವರೇ! 🌾 ನಾನು ನಿಮ್ಮ ಕೃಷಿ ಸಂಗಾತಿ 'ರೈತ ಸಾಥಿ'. ಹೇಗಿದ್ದೀರಾ? "
                    "ಇವತ್ತು ನಿಮ್ಮ ದಿನ ಹೇಗಿತ್ತು? ನಿಮ್ಮ ಬೆಳೆಗಳ ಬಗ್ಗೆ ಏನಾದರೂ ವಿಚಾರಿಸಬೇಕಾ, ಅಥವಾ ಸ್ವಲ್ಪ ಮಾತನಾಡಬೇಕಾ? 😊" if name else
                    "ನಮಸ್ಕಾರ! 🌾 ಹೇಗಿದ್ದೀರಾ? ಇವತ್ತು ಏನು ಮಾತನಾಡೋಣ? "
                    "ನಿಮ್ಮ ಬೆಳೆ, ಕೃಷಿ ನಿರ್ಧಾರಗಳ ಬಗ್ಗೆ ಸಹಾಯ ಬೇಕಾ, ಅಥವಾ ದಿನ ಹೇಗಿತ್ತು ಅಂತ ಹಂಚಿಕೊಳ್ಳುತ್ತೀರಾ? 😊"
                )
            self.session_manager.add_assistant_turn(session_id, greeting_msg, user_id=user_id)
            yield greeting_msg
            return

        # Step 1.0.2: Mental Health & Crisis Safety Check
        crisis_words = [
            "ಸಾಯಲು", "ಸಾಯಬೇಕು", "ಜೀವ ಕಳೆದುಕೊಳ್ಳ", "ಆತ್ಮಹತ್ಯೆ", "ಬದುಕಲು ಇಷ್ಟವಿಲ್ಲ", "ಬದುಕೋದು ಬೇಡ",
            "suicide", "kill myself", "end my life", "want to die", "don't want to live"
        ]
        if any(cw in user_query.lower() for cw in crisis_words):
            if is_english:
                crisis_msg = (
                    "I can hear how much pain you are going through right now, and I want you to know that you are not alone. "
                    "Please don't carry this heavy burden by yourself. Reach out immediately to someone you trust, a family member, or a doctor. "
                    "In India, you can call the 24/7 mental health helpline **14416 (Tele-MANAS)** or emergency services at **112** for immediate support. "
                    "Your life is precious, and there is caring help available right now."
                )
            else:
                crisis_msg = (
                    "ಅಯ್ಯೋ… ನೀವು ಈಗ ಬಹಳ ಕಷ್ಟಕರವಾದ ಪರಿಸ್ಥಿತಿಯನ್ನು ಎದುರಿಸುತ್ತಿದ್ದೀರಿ ಎಂದು ನನಗೆ ಅರ್ಥವಾಗುತ್ತಿದೆ. "
                    "ದಯವಿಟ್ಟು ಈ ಸಮಯದಲ್ಲಿ ಒಬ್ಬರೇ ಇರಬೇಡಿ. ನಿಮ್ಮ ಕುಟುಂಬದವರು, ಆಪ್ತರು ಅಥವಾ ನಂಬಿಕಸ್ಥರ ಜೊತೆ ತಕ್ಷಣ ಮಾತನಾಡಿ. "
                    "ಯಾವುದೇ ತುರ್ತು ನೆರವು ಅಥವಾ ಆಪ್ತಸಮಾಲೋಚನೆಗಾಗಿ ಉಚಿತ ರಾಷ್ಟ್ರೀಯ ಸಹಾಯವಾಣಿ **14416 (Tele-MANAS)** ಅಥವಾ ತುರ್ತು ಸಂಖ್ಯೆ **112** ಗೆ ಕರೆ ಮಾಡಿ. "
                    "ನಿಮ್ಮ ಜೀವ ನಮಗೆ ಮತ್ತು ನಿಮ್ಮವರಿಗೂ ಅತ್ಯಂತ ಅಮೂಲ್ಯ. ಸಹಾಯ ಪಡೆಯಲು ದಯವಿಟ್ಟು ಹಿಂಜರಿಯಬೇಡಿ."
                )
            self.session_manager.add_assistant_turn(session_id, crisis_msg, user_id=user_id)
            yield crisis_msg
            return

        # Step 1.1: Fast Local Slot Extraction
        state.update_from_text(user_query)
        effective_query = self._build_effective_query(user_query, state, history=history)

        # ── Step 1.3: External Service Interception ─────────
        if state.intent == "weather":
            is_crop_management_query = any(k in user_query.lower() for k in [
                "ಯಾವ ಹವಾಮಾನ", "ಉತ್ತಮವಾಗಿ ಬೆಳೆಯುತ್ತದೆ", "climate", "suitab", "temperature required",
                "ನೀರಾವರಿ", "ನಿರ್ವಹಣೆ", "ನೀರು ಹೇಗೆ", "ಹೇಗೆ ಮಾಡಬೇಕು", "ಏನು ಮಾಡಬೇಕು", "ಕ್ರಮಗಳು", "ಬೆಳೆಗಳಿಗೆ"
            ])
            if not is_crop_management_query:
                loc = state.location or state.region or "Karnataka"
                weather_data = self.weather_service.get_weather(loc)
                formatted_weather = await self._format_db_answer_conversationally(
                    user_query, weather_data, state, is_voice_mode=is_voice_mode, language=effective_lang
                )
                self.session_manager.add_assistant_turn(session_id, formatted_weather, user_id=user_id)
                yield formatted_weather
                return
            
        if state.intent == "market_price":
            loc = state.location or state.region or "Karnataka"
            crop = state.crop_name or "Unknown Crop"
            mandi_data = self.mandi_service.get_price(crop, loc)
            formatted_price = await self._format_db_answer_conversationally(
                user_query, mandi_data, state, is_voice_mode=is_voice_mode, language=effective_lang
            )
            self.session_manager.add_assistant_turn(session_id, formatted_price, user_id=user_id)
            yield formatted_price
            return

        if state.intent == "government_scheme" and not state.crop_name:
            scheme_data = self.scheme_service.get_schemes_context()
            name = state.farmer_name
            if is_english:
                greeting = f"Dear {name}! 🌾\n\n" if name else "Dear Farmer! 🌾\n\n"
                intro = "Here are the verified government subsidy schemes and financial assistance programs available for Karnataka farmers:\n\n"
            else:
                greeting = f"ನಮಸ್ಕಾರ {name} ಅವರೇ! 🌾\n\n" if name else "ನಮಸ್ಕಾರ ಕೃಷಿ ಬಾಂಧವರೇ! 🌾\n\n"
                intro = "ರೈತರಿಗೆ ದೊರೆಯುವ ಪ್ರಮುಖ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಮತ್ತು ಸಹಾಯಧನದ ಅಧಿಕೃತ ವಿವರಗಳು ಇಲ್ಲಿವೆ:\n\n"

            prompt = (
                "You are \"Raitha Sathi\" (🌾 ರೈತ ಸಾಥಿ) — a trusted agricultural officer for Karnataka farmers.\n"
                "The farmer asked:\n"
                f"\"{user_query}\"\n\n"
                "Here are the verified schemes from our database:\n"
                f"{scheme_data}\n\n"
                "TASK: Format this verified information into a clear, structured, farmer-friendly response.\n"
                f"Language: {'English' if is_english else 'Kannada (ಕನ್ನಡ script)'}.\n"
                "Format each scheme clearly with bullet points:\n"
                "• **[Scheme Name]:**\n"
                "  - Key Benefits & Subsidy percentage\n"
                "  - Eligibility requirements\n"
                "  - How to apply (e.g., RSK, FRUITS portal)\n\n"
                "Add a practical conclusion advising the farmer to visit their local Raitha Samparka Kendra (RSK).\n"
                "STRICT FIDELITY: Zero hallucinations. Do not introduce any unsupported schemes or facts.\n"
                "Response:"
            )
            try:
                res, _ = await self._call_llm(prompt)
                footer = (
                    "\n\n---\n\n"
                    "📚 **Source:** Government Agricultural Schemes Dataset  \n"
                    "✓ **Verified Evidence**  \n"
                    "🎯 **Confidence:** HIGH  \n"
                    "🗓 **Last updated:** 2026-05-08\n"
                )
                full_scheme_resp = f"{greeting}{intro}{res.strip()}{footer}"
                self.session_manager.add_assistant_turn(session_id, full_scheme_resp, user_id=user_id)
                yield full_scheme_resp
                yield self._DB_MATCH_SENTINEL
                return
            except Exception as e:
                logger.error("Government scheme formatting failed: {e}", e=e)

        # Identify if this is a companion / life / emotional / general science / out-of-scope query
        companion_intents = {
            "emotional_support",
            "motivation",
            "personal_advice",
            "agri_general_science",
            "out_of_scope",
            "casual_greeting",
            "crisis",
        }
        out_of_scope_keywords = [
            "python", "java", "coding", "programmer", "software", "movie", "cinema",
            "actor", "actress", "film", "song", "cricket", "football", "match", "ipl",
            "politics", "minister", "president", "prime minister", "election",
            "recipe", "cake", "pizza", "burger", "gaming", "ವಿಮಾನ", "ಸಿನಿಮಾ", "ರಾಜಕೀಯ",
            "ಕ್ರಿಕೆಟ್", "ಚುನಾವಣೆ", "ಸೆಲೆಬ್ರಿಟಿ", "ವಿರಾಟ್", "ಕೊಹ್ಲಿ", "virat", "kohli",
            "ಧೋನಿ", "dhoni", "ರೋಹಿತ್", "rohit", "ರೈಲು", "ಟಿಕೆಟ್", "ಬುಕ್", "train",
            "ticket", "booking", "book", "capital of", "france", "ಫ್ರಾನ್ಸ್", "paris",
            "ರಾಜಧಾನಿ", "who is", "who was", "bank balance", "recharge", "mobile recharge"
        ]
        q_lower = user_query.lower()
        if any(kw in q_lower for kw in out_of_scope_keywords) and not state.crop_name:
            state.intent = "out_of_scope"

        # Case 4: Agriculture-only scope protection (Gemini not called for unrelated topics)
        if state.intent == "out_of_scope":
            refusal_text = (
                "ಕ್ಷಮಿಸಿ ಕೃಷಿ ಬಾಂಧವರೇ 🌾, ನಾನು ಕೃಷಿಗೆ ಸಂಬಂಧಿಸಿದ ಮಾಹಿತಿಗಾಗಿ ತರಬೇತಿ ಪಡೆದಿದ್ದೇನೆ. ದಯವಿಟ್ಟು ಕೃಷಿ, ಬೆಳೆ, ಕೀಟ, ರೋಗ, ಗೊಬ್ಬರ, ನೀರಾವರಿ ಅಥವಾ ಇತರ ಕೃಷಿ ಸಂಬಂಧಿತ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ."
                if not is_english
                else "Sorry farmer friend 🌾, I am trained specifically to provide agricultural information. Please ask questions related to farming, crops, pests, diseases, fertilizers, irrigation, or other agricultural topics."
            )
            self.session_manager.add_assistant_turn(session_id, refusal_text, user_id=user_id)
            yield refusal_text
            return

        is_companion_or_non_crop = (
            state.intent in companion_intents
            or (
                not state.crop_name
                and not state.symptoms
                and not state.problem_type
                and state.intent not in ["weather", "market_price", "government_scheme", "disease_management", "fertilizer", "pesticide", "irrigation", "sowing", "harvesting"]
            )
        )

        context_text = ""
        top_confidence = 0.0

        if not is_companion_or_non_crop:
            # ── Step 2: Direct Database Search (Case 1: Exact/Direct Matching) ──
            db_res = self.db_searcher.search(effective_query, crop_name=state.crop_name, intent=state.intent, return_matched_question=True)
            if db_res:
                db_answer, matched_question, db_entry = db_res
                state.update_from_text(effective_query)
                name = state.farmer_name

                # Build the complete Gold Standard structured response from DB fields
                formatted_answer = self._build_case1_response(
                    db_entry=db_entry,
                    farmer_name=name,
                    is_english=is_english,
                    is_voice_mode=is_voice_mode,
                )

                logger.info(
                    "Case 1 DB match | crop={c} | question={q}",
                    c=db_entry.get("crop_name", ""), q=matched_question[:60]
                )
                self.session_manager.add_assistant_turn(session_id, formatted_answer, user_id=user_id)
                # Yield the formatted answer, then append the DB-match sentinel so
                # generate() can detect Case 1 and set source='database'.
                yield formatted_answer
                yield self._DB_MATCH_SENTINEL
                return

            # ── Step 3: Check if a follow-up question is needed ───────────────────
            if self.follow_up_gen.needs_followup(state):
                follow_up_q = self.follow_up_gen.generate(state, effective_query)
                if follow_up_q:
                    state.pending_question = user_query
                    self.session_manager.add_assistant_turn(session_id, follow_up_q, user_id=user_id)
                    yield follow_up_q
                    return

            # ── Step 4: FAISS Semantic Retrieval ──────────────────────────────────
            enriched_query = f"{effective_query} {state.to_retrieval_query()}"
            retrieved_entries = []

            try:
                retrieved_entries = self.retriever.retrieve(
                    query=enriched_query,
                    top_k=settings.FAISS_TOP_K,
                    crop_name=state.crop_name,
                    season=state.season,
                    region=state.region,
                    intent=state.intent,
                    extracted_entities={
                        "pest_name": state.pest_name,
                        "disease_name": state.disease_name,
                        "fertilizer_name": state.fertilizer_name,
                        "pesticide_name": state.pesticide_name,
                    }
                )
                if retrieved_entries:
                    top_confidence = retrieved_entries[0].get("_score", 0.0)
                    context_text = self.context_builder.build(retrieved_entries)

                    # Step 4.1: Case 2 Verified Semantic Match -> Gold Standard RAG Response
                    if top_confidence >= 0.40:
                        verified_match = await self._verify_semantic_candidates(
                            user_query=user_query,
                            candidates=retrieved_entries[:8],
                            crop_name=state.crop_name
                        )
                        if verified_match:
                            logger.info(
                                "✓ Case 2 Verified Semantic Match | crop={c} | question={q}",
                                c=verified_match.get("crop_name", ""),
                                q=verified_match.get("question", "")[:60]
                            )
                            name = state.farmer_name
                            formatted_case2 = await self._build_case2_response(
                                db_entry=verified_match,
                                user_query=user_query,
                                farmer_name=name,
                                is_english=is_english,
                                is_voice_mode=is_voice_mode,
                            )
                            self.session_manager.add_assistant_turn(session_id, formatted_case2, user_id=user_id)
                            yield formatted_case2
                            yield self._DB_MATCH_SENTINEL
                            return

                logger.info(
                    "FAISS retrieval (stream) | entries={n} | top_confidence={c:.2f}",
                    n=len(retrieved_entries), c=top_confidence
                )
            except Exception as e:
                logger.warning("Retrieval failed: {e}", e=e)

        # ── Step 5: Build prompt and call LLM ────────────────────────────────
        # In Case 3 / fallback (no exact or verified semantic database match),
        # strictly isolate Gemini prompt: unverified FAISS entries must NOT be passed as factual context.
        context_text = ""
        is_low_confidence = True
        logger.info("Case 3 / Fallback prompt isolation: context cleared, relying on Gemini agricultural reasoning.")
            
        prompt = self.prompt_builder.build(
            user_query=user_query,
            context=context_text,
            history=history[:-1],
            state=state,
            confidence_score=top_confidence,
            is_voice_mode=is_voice_mode,
            is_low_confidence=is_low_confidence,
            diary_summary=self.session_manager.diary.get_summary(session_id),
            language=effective_lang
        )

        full_response = []

        # 1. Output Raitha Sathi greeting first
        greeting = "ನಮಸ್ಕಾರ ಕೃಷಿ ಬಾಂಧವರೇ! 🌾\n\n" if not is_english else "Dear Farmer! 🌾\n\n"
        full_response.append(greeting)
        yield greeting

        # 2. Output Gemini fetching indicator second (before Gemini starts generating/streaming)
        fetching_indicator = "🌐 Gemini ನಿಂದ ಉತ್ತರ ಪಡೆಯಲಾಗುತ್ತಿದೆ... / Fetching answer from Gemini...\n\n"
        full_response.append(fetching_indicator)
        yield fetching_indicator

        # 3. Stream Gemini tokens
        try:
            async for token in self._stream_llm(prompt):
                full_response.append(token)
                yield token
        except Exception as e:
            logger.error("Streaming LLM failed: {e}", e=e)
            error_msg = "ಕ್ಷಮಿಸಿ, ಉತ್ತರ ನೀಡಲು ತೊಂದರೆ ಆಗುತ್ತಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ."
            yield error_msg
            full_response.append(error_msg)

        # ── Step 6.8: Record to Farm Diary ───────────────────────────────────
        if state.crop_name:
            if state.intent in ["disease_management", "pesticide", "fertilizer", "irrigation"]:
                summary_topic = f"{state.intent} advice"
                if state.problem_type:
                    summary_topic += f" for {state.problem_type}"
                self.session_manager.diary.add_advisory_record(
                    session_id=session_id,
                    crop=state.crop_name,
                    topic=summary_topic,
                    summary=user_query[:50]
                )
            if state.intent == "sowing" or "planting" in user_query.lower():
                self.session_manager.diary.add_journey_event(session_id, state.crop_name, "Sowing/Planting")

        # Strip indicator from history so conversation memory stays clean
        clean_response = "".join(full_response)
        for prefix in PREFIXES_TO_STRIP:
            clean_response = clean_response.replace(prefix, "")
        clean_response = clean_response.replace(fetching_indicator, "")

        self.session_manager.add_assistant_turn(session_id, clean_response.strip(), user_id=user_id)

    # ── Private: LLM Orchestration ────────────────────────────────────────────

    async def _call_llm(self, prompt: str) -> tuple[str, str]:
        """
        Orchestrate LLM calls using Gemini.

        Returns:
            Tuple of (response_text, provider_name_used)
        """
        try:
            gemini = self._get_gemini_client()
            if gemini:
                result = await gemini.generate(prompt)
                if result:
                    return result, "gemini"
        except (LLMConnectionError, LLMTimeoutError) as e:
            logger.error("Gemini unavailable: {e}", e=e)
        except Exception as e:
            logger.error("Gemini error: {e}", e=e)

        return "", "none"

    async def _stream_llm(self, prompt: str):
        """
        Stream tokens from Gemini with failover to non-streaming fallback.
        Yields token strings.
        """
        token_count = 0
        try:
            gemini = self._get_gemini_client()
            if gemini:
                async for token in gemini.generate_stream(prompt):
                    if token:
                        token_count += 1
                        yield token
            else:
                raise LLMConnectionError("Gemini client not available")
        except Exception as e:
            logger.error("Gemini stream failed: {e}", e=e)

        if token_count == 0:
            logger.warning("Gemini stream yielded 0 tokens. Invoking non-streaming fallback.")
            result = await self._call_llm(prompt)
            if result and result[0]:
                yield result[0]
            else:
                yield "ಕ್ಷಮಿಸಿ, ಈ ಪ್ರಶ್ನೆಗೆ ಸಮಗ್ರ ಮಾಹಿತಿ ಒದಗಿಸಲು ತಾಂತ್ರಿಕ ತೊಂದರೆ ಆಗಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಕೇಳಿ."

    def _get_gemini_client(self):
        """Lazily initialise Gemini client on first use."""
        if self._gemini is None and settings.GEMINI_API_KEY:
            try:
                from app.llm.gemini_client import GeminiClient
                self._gemini = GeminiClient()
            except Exception as e:
                logger.error("Cannot init Gemini client: {e}", e=e)
                return None
        return self._gemini

    async def _classify_query(self, query: str) -> str:
        """
        Classifies a user query into 'greeting', 'agricultural', or 'non_agricultural'.
        """
        normalized = query.lower().strip().rstrip("?").rstrip("!").strip()
        greetings = {
            "hello", "hi", "namaskara", "namaste", "ನಮಸ್ಕಾರ", "ಹಲೋ", "ಹಾಯ್", 
            "good morning", "good afternoon", "good evening", "hey"
        }
        if normalized in greetings:
            return "greeting"

        # Pre-check non-agricultural keywords for instant classification
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
        agri_cultivation_keywords = [
            "crop", "farm", "farming", "soil", "pest", "disease", "fertilizer", "water", "yield",
            "seed", "nursery", "sapling", "grafting", "propagation", "cultivation", "harvest", "plantation",
            "grape", "grapes", "mango", "banana", "chilli", "chili", "tomato", "onion", "potato",
            "garlic", "ginger", "wheat", "cashew", "apple", "papaya", "pineapple", "lemon", "betel",
            "avocado", "pomegranate", "dragon", "dragonfruit", "sweet", "color", "colour",
            "ಬೆಳೆ", "ಕೃಷಿ", "ಮಣ್ಣು", "ಕೀಟ", "ರೋಗ", "ಗೊಬ್ಬರ", "ಬೀಜ", "ಸಸಿ", "ನರ್ಸರಿ", "ಕಸಿ",
            "ಉತ್ಪಾದನೆ", "ತೋಟ", "ಬೇಸಾಯ", "ಇಳುವರಿ", "ಕೊಯ್ಲು", "ಸಾಗುವಳಿ", "ಹಣ್ಣು", "ತರಕಾರಿ",
            "ದ್ರಾಕ್ಷಿ", "ಮಾವು", "ಬಾಳೆ", "ಮೆಣಸಿನಕಾಯಿ", "ಟೊಮ್ಯಾಟೊ", "ಈರುಳ್ಳಿ", "ಆಲೂಗಡ್ಡೆ", "ಬೆಳ್ಳುಳ್ಳಿ",
            "ಶುಂಠಿ", "ಗೋಧಿ", "ಗೇರು", "ಸೇಬು", "ಪಪ್ಪಾಯಿ", "ಅನಾನಸ್", "ನಿಂಬೆ", "ಅರಟ", "ದಾಳಿಂಬೆ", "ಬದನೆ", "ಕೊತ್ತಂಬರಿ",
            # Supported crop names
            "ಸಜ್ಜೆ", "ರಾಗಿ", "ಜೋಳ", "ಭತ್ತ", "ಅಕ್ಕಿ", "ತೆಂಗು", "ಅಡಿಕೆ", "ಕಬ್ಬು", "ಅರಿಶಿನ", "ಮೆಕ್ಕೆಜೋಳ",
            "ಕಾಫಿ", "ಹತ್ತಿ", "ಕಡಲೆ", "ತೊಗರಿ", "ಶೇಂಗಾ", "ಧಾನ್ಯ",
            "bajra", "ragi", "jowar", "paddy", "rice", "coconut", "arecanut", "sugarcane", "turmeric", "maize",
            "coffee", "cotton", "groundnut", "redgram", "chickpea",
            # Market / APMC / trade — agricultural domain
            "ಎಪಿಎಂಸಿ", "ಮಾರುಕಟ್ಟೆ", "ಮಾರಾಟ", "ಬೆಲೆ", "ಖರೀದಿ", "ಸಂಗ್ರಹ", "ಗೋದಾಮು", "ರಫ್ತು", "ಆದಾಯ",
            "apmc", "market", "selling", "storage", "price", "msp", "procurement", "export",
        ]
        
        has_non_agri = any(kw in normalized for kw in non_agri_keywords)
        has_agri_cultivation = any(akw in normalized for akw in agri_cultivation_keywords)

        if has_non_agri and not has_agri_cultivation:
            return "non_agricultural"

        prompt = (
            "You are an AI classifier. Classify the user query into exactly one of these categories:\n"
            "- 'greeting' (if it is a greeting or pleasantry like hello, hi, how are you, etc.)\n"
            "- 'agricultural' (if it is related to agriculture, farming, crops, soil, weather impact on crops, pests, diseases, irrigation, fertilizers, etc.)\n"
            "- 'non_agricultural' (if it is NOT related to agriculture/farming, such as general questions about coding, history, politics, sports, math, movies, entertainment, general knowledge, etc.)\n\n"
            f"Query: \"{query}\"\n\n"
            "Reply with only one word: greeting, agricultural, or non_agricultural."
        )
        try:
            # We call LLM without stream
            response_text, _ = await self._call_llm(prompt)
            cleaned = response_text.lower().strip().replace("'", "").replace('"', "")
            if "non_agricultural" in cleaned or "non-agricultural" in cleaned or "non_agri" in cleaned:
                return "non_agricultural"
            elif "agricultural" in cleaned:
                return "agricultural"
            elif "greeting" in cleaned:
                return "greeting"
            
            return "agricultural" if has_agri_cultivation else "non_agricultural"
        except Exception as e:
            logger.error("Query classification failed: {e}", e=e)
            return "agricultural" if has_agri_cultivation else "non_agricultural"

