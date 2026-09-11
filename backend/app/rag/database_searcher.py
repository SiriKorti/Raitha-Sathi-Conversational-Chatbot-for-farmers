"""
database_searcher.py — Hybrid Semantic + Keyword Database Searcher

WHAT IT DOES:
Searches all JSON files in the 'database/' directory for answers.
Uses a multi-tier strategy: exact match → substring → keyword containment
→ retrieval_text search → Jaccard similarity, all against the enriched schema.

WHY IT EXISTS:
For any question present in the 1,500-entry knowledge base,
this module guarantees a database-grounded answer is returned BEFORE
falling through to LLM generation.

CONNECTIONS:
- Called by 'response_generator.py' as the FIRST lookup step.
- Reads all JSON files from the path in 'app.config.DATABASE_PATH'.
"""

import re
import unicodedata
from pathlib import Path
from app.config import settings
from app.utils.logger import logger


class DatabaseSearcher:
    """
    Searches for answers directly in the JSON database files.

    Matching strategy (in priority order):
    1. Exact match on question or any variant
    2. Query fully contains the candidate question (substring)
    3. Candidate fully contains the query (substring)
    4. ALL query tokens found inside candidate (keyword containment)
    5. retrieval_text token overlap
    6. Jaccard similarity >= threshold on question + variants
    7. High keyword overlap fallback (>= 65% of query tokens in candidate)
    """

    def __init__(self):
        self.data: list[dict] = []
        self._load_database()

    # ── Loading ───────────────────────────────────────────────────────────────

    def _load_database(self):
        """Load all JSON files from the database directory."""
        db_path = Path(settings.DATABASE_PATH)

        if not db_path.exists():
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / settings.DATABASE_PATH

        if not db_path.exists():
            logger.warning(f"Database path {db_path} does not exist.")
            return

        try:
            from app.rag.dataset_loader import DatasetLoader
            loader = DatasetLoader(dataset_path=str(db_path))
            self.data = loader.load_all()
            logger.info(
                "DatabaseSearcher ready: {n} entries from {p}",
                n=len(self.data), p=db_path
            )
        except Exception as e:
            logger.error(f"Failed to load database: {e}")

    # ── Public API ────────────────────────────────────────────────────────────

    def _get_canonical_crop(self, crop_name: str) -> str:
        """Helper to resolve a crop to its standardized canonical Kannada form."""
        if not crop_name:
            return ""
        from app.utils.text_utils import extract_crop_from_text
        canonical = extract_crop_from_text(crop_name)
        return canonical if canonical else crop_name.strip().lower()

    def _detect_candidate_intent(self, question: str) -> str | None:
        """Heuristic mapping to classify candidate questions into agricultural intent categories."""
        q = question.lower()
        if any(w in q for w in ["ಮಣ್ಣು", "ಮಣ್ಣಿನ", "ನೆಲ", "soil", "land", "ph", "ಜೇಡಿ", "ಮೆಕ್ಕಲು"]):
            return "soil"
        if any(w in q for w in ["ನಿಯಂತ್ರಣ", "ಹತೋಟಿ", "ಕಡಿಮೆ ಮಾಡು", "ನಿವಾರಣೆ", "ಔಷಧಿ", "control", "prevent", "pesticide", "insecticide"]):
            return "control"
        if any(w in q for w in ["ಲಕ್ಷಣ", "ಗುರುತಿಸು", "symptom", "identify"]):
            return "symptoms"
        if any(w in q for w in ["ಗೊಬ್ಬರ", "ಪೋಷಕಾಂಶ", "fertilizer", "nutrition", "npk"]):
            return "fertilizer"
        if any(w in q for w in ["ನೀರು", "ನೀರಾವರಿ", "irrigate", "water"]):
            return "irrigation"
        if any(w in q for w in ["ಬಿತ್ತನೆ", "ಸಸಿ ನೆಡು", "sow", "plant", "ಬೀಜ", "seed"]):
            return "sowing"
        if any(w in q for w in ["ಅಂತರ", "spacing", "distance"]):
            return "spacing"
        if any(w in q for w in ["ಕಟಾವು", "harvest"]):
            return "harvesting"
        return None

    def _get_adaptive_threshold(self, query: str, has_crop: bool) -> float:
        """Determine similarity threshold adaptively based on query specificity."""
        query_lower = query.lower()
        # Common highly ambiguous questions require higher threshold
        common_keywords = ["ಬಿತ್ತನೆ", "ಗೊಬ್ಬರ", "ಅಂತರ", "ಸಮಯ", "ಯಾವಾಗ", "sow", "fertilizer", "spacing", "time", "when"]
        if any(w in query_lower for w in common_keywords):
            return 0.60 if has_crop else 0.70
        return 0.45 if has_crop else 0.55

    def search(self, query: str, crop_name: str = None, intent: str = None, threshold: float = None, return_matched_question: bool = False) -> str | tuple[str, str] | None:
        """
        Search for a matching question in the database with strict filters.

        Returns a formatted answer string (or tuple of answer and matched question if return_matched_question is True) if found, else None.
        """
        if not query or not self.data:
            return None

        # Normalize query and extract both raw words and stemmed roots
        normalized_query = self._normalize(query)
        query_tokens = self._get_tokens(query)
        if not query_tokens:
            return None

        # Standardize crop names to prevent cross-crop bleed (check both crop_name and query text)
        user_crop_canonical = self._get_canonical_crop(crop_name) if crop_name else None
        if not user_crop_canonical:
            from app.utils.text_utils import extract_crop_from_text
            extracted_crop = extract_crop_from_text(query)
            if extracted_crop:
                user_crop_canonical = self._get_canonical_crop(extracted_crop)

        # Set of canonical crops actually present in the 15-crop database
        db_canonical_crops = {
            self._get_canonical_crop(e.get("crop_name", "")) 
            for e in self.data 
            if e.get("crop_name")
        }
        db_canonical_crops = {c for c in db_canonical_crops if c}

        if user_crop_canonical:
            if user_crop_canonical not in db_canonical_crops:
                logger.info(
                    "Requested crop '{c}' is an out-of-database crop. Skipping local DB search to trigger Case 3 LLM fallback.", 
                    c=user_crop_canonical
                )
                return None

        # Build crop word exclusion set
        crop_tokens = set()
        if user_crop_canonical:
            crop_tokens = self._get_tokens(user_crop_canonical)
            for ct in list(crop_tokens):
                crop_tokens.add(ct + "ದ")
                crop_tokens.add(ct + "ನಲ್ಲಿ")
                crop_tokens.add(ct + "ಯಲ್ಲಿ")
                crop_tokens.add(ct + "ಗೆ")
                crop_tokens.add(ct + "ಕ್ಕೆ")
            from app.utils.text_utils import extract_crop_from_text
            for qt in query_tokens:
                if extract_crop_from_text(qt) == user_crop_canonical or (crop_name and qt in crop_name.lower()):
                    crop_tokens.add(qt)

        # Determine threshold adaptively
        if threshold is None:
            threshold = self._get_adaptive_threshold(query, bool(user_crop_canonical))

        # ── Phase 1: Global Exact Match ──────────────────────────────────────────
        for entry in self.data:
            entry_crop_canonical = self._get_canonical_crop(entry.get("crop_name", ""))
            if user_crop_canonical:
                if entry_crop_canonical and user_crop_canonical != entry_crop_canonical:
                    continue

            answer = self.extract_answer(entry)
            if not answer:
                continue

            candidates = [entry.get("question", "")]
            candidates += entry.get("question_variants", [])
            pdesc = entry.get("problem_description", "")
            if pdesc: candidates.append(pdesc)

            for cand in candidates:
                if cand and self._normalize(cand) == normalized_query:
                    logger.info("Phase 1 Exact DB match: {q}", q=normalized_query[:60])
                    if return_matched_question:
                        return answer, cand, entry
                    return answer

        # ── Phase 2: Global Substring Match ──────────────────────────────────────
        for entry in self.data:
            entry_crop_canonical = self._get_canonical_crop(entry.get("crop_name", ""))
            if user_crop_canonical:
                if entry_crop_canonical and user_crop_canonical != entry_crop_canonical:
                    continue

            answer = self.extract_answer(entry)
            if not answer:
                continue

            candidates = [entry.get("question", "")]
            candidates += entry.get("question_variants", [])
            pdesc = entry.get("problem_description", "")
            if pdesc: candidates.append(pdesc)

            for cand in candidates:
                if not cand: continue
                nc = self._normalize(cand)
                if len(nc) > 8 and (nc in normalized_query or (len(normalized_query) >= 12 and normalized_query in nc)):
                    logger.info("Phase 2 Substring DB match: {q}", q=normalized_query[:60])
                    if return_matched_question:
                        return answer, cand, entry
                    return answer

        # ── Phase 3: Global Ranked Content Keyword & Jaccard Match ────────────────
        STOP_WORDS = {
            "ಯಾವ", "ಹೇಗೆ", "ಏನು", "ಎಷ್ಟು", "ಯಾವುದು", "ಮಾಡಬೇಕು", "ಮಾಡಲು", "ಮಾಡಬಹುದು",
            "ಮತ್ತು", "ಅಥವಾ", "ಇವು", "ಅವು", "ಇರುವ", "ಬಗ್ಗೆ", "ಬೆಳೆಯ", "ಬೆಳೆಗೆ", "ಬೆಳೆಯಲ್ಲಿ", "ಬೆಳೆ",
            "ರೈತರು", "ಕರ್ನಾಟಕ", "ಉತ್ತರ", "ಪ್ರಶ್ನೆ", "ಕಡಿಮೆ", "ರೀತಿ", "ಯಾವ ರೀತಿ",
            "ಒಂದು", "ಎರಡು", "ಎಕರೆಗೆ", "ಎಕರೆ", "ಬೇಕು", "ಬೇಕಾಗುತ್ತದೆ", "ಹಾಕಬೇಕು"
        }

        # Check if query has content tokens beyond stop words and crop names
        content_query_tokens = query_tokens - STOP_WORDS - crop_tokens
        if not content_query_tokens:
            logger.debug("Query contains only crop name or stop words, skipping Phase 3 ranked match: {q}", q=normalized_query[:60])
            return None

        scored_candidates = []
        for entry in self.data:
            entry_crop_canonical = self._get_canonical_crop(entry.get("crop_name", ""))
            if user_crop_canonical:
                if entry_crop_canonical and user_crop_canonical != entry_crop_canonical:
                    continue
            else:
                # If no crop was specified in query/state, don't loosely match crop-specific entries in Phase 3
                if entry_crop_canonical and entry_crop_canonical in db_canonical_crops:
                    continue

            answer = self.extract_answer(entry)
            if not answer:
                continue

            candidates = [entry.get("question", "")]
            candidates += entry.get("question_variants", [])
            pdesc = entry.get("problem_description", "")
            if pdesc: candidates.append(pdesc)

            for cand in candidates:
                if not cand: continue
                
                # Filter by intent category first if specified (ignore generic advisory)
                if intent and intent not in ("general_advisory", "general"):
                    cand_intent = self._detect_candidate_intent(cand)
                    if cand_intent and intent != cand_intent:
                        continue

                cand_tokens = self._get_tokens(cand)

                inter = (query_tokens & cand_tokens) - STOP_WORDS - crop_tokens
                union = (query_tokens | cand_tokens) - STOP_WORDS - crop_tokens
                score = len(inter) / len(union) if union else 0.0

                # Small boost (+0.05) for tie-breaking candidates matching the query's specific intent category
                cand_intent = self._detect_candidate_intent(cand)
                intent_boost = 0.05 if (intent and cand_intent and intent == cand_intent) else 0.0
                final_score = score + intent_boost

                min_count = 2 if len(query_tokens - STOP_WORDS - crop_tokens) >= 2 else 1
                min_score = threshold

                if len(inter) >= min_count and score >= min_score:
                    scored_candidates.append((final_score, len(inter), answer, cand, entry))

        if scored_candidates:
            scored_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
            top_score, top_count, top_ans, top_cand, top_entry = scored_candidates[0]

            min_count = 2 if len(query_tokens - STOP_WORDS - crop_tokens) >= 2 else 1
            min_score = threshold

            if top_count >= min_count and top_score >= min_score:
                logger.info(
                    "Phase 3 Ranked DB match | score={s:.2f} | count={c} | match={m} | query={q}",
                    s=top_score, c=top_count, m=top_cand[:50], q=normalized_query[:60]
                )
                if return_matched_question:
                    return top_ans, top_cand, top_entry
                return top_ans

        logger.debug("No direct DB match for: {q}", q=normalized_query[:60])
        return None

    def search_by_symptoms(self, symptoms: list[str], crop_name: str = None) -> list[dict]:
        """
        Find entries matching given symptoms, optionally filtered by crop.
        Returns up to 5 entries ordered by symptom overlap.
        """
        if not symptoms or not self.data:
            return []

        symptom_words = set(w.lower() for s in symptoms for w in s.split())
        scored = []

        for entry in self.data:
            if crop_name:
                # Use canonical equality to prevent substring bleed (e.g. "ಜೋಳ" in "ಮೆಕ್ಕೆಜೋಳ")
                entry_crop_canonical = self._get_canonical_crop(entry.get("crop_name", ""))
                user_crop_canonical_sym = self._get_canonical_crop(crop_name)
                if entry_crop_canonical and user_crop_canonical_sym != entry_crop_canonical:
                    continue

            entry_symptom_words = set(
                w.lower()
                for s in entry.get("symptoms", [])
                for w in s.split()
            )
            if not entry_symptom_words:
                continue

            overlap = len(symptom_words & entry_symptom_words)
            if overlap > 0:
                scored.append((entry, overlap))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in scored[:5]]

    def get_all_crops(self) -> list[str]:
        """Return sorted unique list of crop names in the database."""
        return sorted({e.get("crop_name", "") for e in self.data if e.get("crop_name")})

    def get_entry_count(self) -> int:
        """Return total number of loaded entries."""
        return len(self.data)

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _normalize(text: str) -> str:
        """Lowercase, Unicode-normalize, remove parentheses/brackets,
        collapse whitespace, and strip trailing question marks.

        Unicode NFC normalization ensures that Kannada characters encoded
        differently (e.g. from different editors or terminals) still match.
        """
        # Unicode NFC normalization — fixes invisible Kannada encoding mismatches
        text = unicodedata.normalize("NFC", text)
        # Strip quotes, punctuation, and brackets but keep inner text as tokens
        text = re.sub(r"[\(\)\[\]\{\}'\"`‘’“”:,;\-–—]", " ", text)
        # Lowercase and collapse whitespace
        text = re.sub(r"\s+", " ", text.strip().lower())
        # Strip trailing Kannada question mark (?) and ASCII question mark
        text = text.rstrip("?").rstrip("\u003f").strip()
        return text

    @staticmethod
    def _stem_kannada_word(word: str) -> str:
        """Strip Kannada noun case inflections (ವಿಭಕ್ತಿ ಪ್ರತ್ಯಯಗಳು) to match root forms."""
        word = unicodedata.normalize("NFC", word.strip().lower())
        if len(word) <= 2:
            return word
        suffixes = [
            "ಗಳಿಂದಲೂ", "ಗಳಿಂದ", "ಗಳಲ್ಲಿ", "ಗಳನ್ನು", "ಗಳಿಗೆ", "ಗಳಿಗಾಗಿ", "ಗಳ",
            "ದಿಂದಲೂ", "ಯಿಂದಲೂ", "ದಿಂದ", "ಯಿಂದ", "ದಲ್ಲಿ", "ನಲ್ಲಿ", "ಯಲ್ಲಿ", "ಅಲ್ಲಿ",
            "ವನ್ನು", "ಯನ್ನು", "ಅನ್ನು", "ನ್ನು",
            "ವಿನ", "ಯಿನ", "ಇನ",
            "ಕ್ಕಿಂತ", "ಗಿಂತ",
            "ಕ್ಕೆ", "ಇಗೆ", "ಗೆ", "ಗಾಗಿ", "ಯಾಗಿ",
            "ದ", "ಯ", "ನ"
        ]
        for sfx in suffixes:
            if len(word) - len(sfx) >= 2 and word.endswith(sfx):
                return word[:-len(sfx)]
        return word

    def _get_tokens(self, text: str) -> set[str]:
        """Extract both raw words and stemmed roots for flexible Kannada matching."""
        norm = self._normalize(text)
        tokens = set()
        for w in norm.split():
            if len(w) > 1:
                tokens.add(w)
                tokens.add(self._stem_kannada_word(w))
        return tokens

    def extract_answer(self, entry: dict) -> str | None:
        """
        Extract a formatted answer from an entry.

        Supports both old simple format {"answer": "..."} and the new
        enriched schema with solution.short_answer / detailed_answer.
        """
        # ── New enriched schema ───────────────────────────────────────────────
        solution = entry.get("solution")
        if isinstance(solution, dict):
            short    = solution.get("short_answer",    "").strip()
            detailed = solution.get("detailed_answer", "").strip()
            steps    = solution.get("step_by_step",    [])
            prevent  = solution.get("preventive_measures", [])
            organic  = solution.get("organic_solutions",   [])
            warnings = solution.get("warnings",            [])

            # Use detailed answer as primary if available, else short answer
            primary = detailed or short
            if not primary:
                return None

            parts = [primary]

            if steps and steps != [primary]:
                # Only include steps that are genuinely additive (not fragments of the primary answer)
                additive_steps = [
                    s for s in steps
                    if s.strip() and s.strip() != primary and s.strip() not in primary
                ]
                if additive_steps:
                    parts.append("\n\n📋 **ಹಂತ ಹಂತವಾಗಿ:**")
                    for i, step in enumerate(additive_steps[:5], 1):
                        parts.append(f"  {i}. {step}")

            if prevent:
                parts.append("\n🛡️ **ತಡೆಗಟ್ಟುವ ಕ್ರಮಗಳು:**")
                for m in prevent[:3]:
                    parts.append(f"  • {m}")

            if organic:
                parts.append("\n🌿 **ಸಾವಯವ ಪರಿಹಾರ:**")
                for s in organic[:2]:
                    parts.append(f"  • {s}")

            if warnings:
                parts.append("\n⚠️ **ಎಚ್ಚರಿಕೆ:**")
                for w in warnings[:2]:
                    parts.append(f"  • {w}")

            return "\n".join(parts)

        # ── Legacy simple schema {"answer": "..."} ────────────────────────────
        answer = entry.get("answer", "")
        if isinstance(answer, str) and answer.strip():
            return answer.strip()

        return None
