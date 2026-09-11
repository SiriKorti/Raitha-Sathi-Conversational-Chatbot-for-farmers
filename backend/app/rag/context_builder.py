"""
context_builder.py — RAG Context Builder

WHAT IT DOES:
Takes the list of retrieved dataset entries and builds a structured,
readable context string that is injected into the LLM prompt. It
formats all rich fields from the database schema (symptoms, causes,
step-by-step solutions, organic options, warnings) into a concise block.

WHY IT EXISTS:
A good context string is the heart of RAG quality. By isolating context
formatting here, we can tune what information the LLM sees without
touching the retrieval or prompt logic.

CONNECTIONS:
- Called by 'response_generator.py' after FAISS retrieval.
- Reads entries from the database schema (symptoms, causes, solution dict).
"""

from app.utils.text_utils import truncate_text
from app.utils.logger import logger


# Maximum characters per retrieved entry in the context
MAX_ENTRY_CHARS = 800

# Maximum total context characters sent to LLM
MAX_TOTAL_CONTEXT_CHARS = 4000


class ContextBuilder:
    """
    Converts retrieved FAISS results into a structured context string
    suitable for injection into an LLM prompt.
    """

    def build(self, entries: list[dict], max_entries: int = 5) -> str:
        """
        Build a context string from the top retrieved entries.

        Args:
            entries:     List of retrieved entry dicts (from Retriever)
            max_entries: Maximum number of entries to include

        Returns:
            Formatted context string for the LLM prompt
        """
        if not entries:
            return ""

        context_parts = []

        for i, entry in enumerate(entries[:max_entries]):
            part = self._format_entry(entry, position=i + 1)
            if part:
                context_parts.append(part)

        # Join all parts
        full_context = "\n\n---\n\n".join(context_parts)

        # Truncate if total context is too long
        if len(full_context) > MAX_TOTAL_CONTEXT_CHARS:
            full_context = full_context[:MAX_TOTAL_CONTEXT_CHARS] + "\n[...more results truncated]"

        logger.debug(
            "Context built: {n} entries, {chars} chars",
            n=len(context_parts), chars=len(full_context)
        )
        return full_context

    def _format_entry(self, entry: dict, position: int) -> str:
        """
        Format a single dataset entry into a readable context block.

        Supports BOTH dataset schemas:
        - Simple:  {"question": "...", "answer": "..."}
        - Complex: {"solution": {"short_answer": ..., "step_by_step": [...]}}

        Args:
            entry:    Dataset entry dict
            position: Result rank (1 = best match)

        Returns:
            Formatted string for this entry
        """
        lines = []

        # ── Header with rank, crop, topic, and confidence score ──────────────
        score = entry.get("_score", 0)
        crop = entry.get("crop_name", "")
        topic = entry.get("topic", "")
        season = entry.get("season", "")
        header = f"[ಸಂಬಂಧಿತ ಮಾಹಿತಿ #{position}"
        if crop:
            header += f" | ಬೆಳೆ: {crop}"
        if topic:
            header += f" | ವಿಷಯ: {topic}"
        if season:
            header += f" | ಕಾಲ: {season}"
        header += f" | ಸಂಬಂಧ: {score:.2f}]"
        lines.append(header)

        # ── Question (shows what kind of query this matches) ──────────────────
        if entry.get("question"):
            lines.append(f"ಪ್ರಶ್ನೆ: {entry['question']}")

        # ── Problem description ───────────────────────────────────────────────
        if entry.get("problem_description"):
            desc = truncate_text(entry["problem_description"], max_chars=150)
            lines.append(f"ಸಮಸ್ಯೆ: {desc}")

        # ── Symptoms (critical for diagnosis) ────────────────────────────────
        symptoms = entry.get("symptoms", [])
        if symptoms:
            lines.append("ಲಕ್ಷಣಗಳು: " + ", ".join(str(s) for s in symptoms[:5]))

        # ── Causes ───────────────────────────────────────────────────────────
        causes = entry.get("causes", [])
        if causes:
            lines.append("ಕಾರಣಗಳು: " + ", ".join(str(c) for c in causes[:3]))

        # ── PRIORITY: Simple answer string (most common DB format) ────────────
        # Most database files use {"answer": "plain text"} without a solution dict.
        # This must be checked BEFORE the solution dict to avoid empty context.
        simple_answer = entry.get("answer", "")
        if simple_answer and isinstance(simple_answer, str) and simple_answer.strip():
            answer_text = truncate_text(simple_answer.strip(), max_chars=400)
            lines.append(f"ಉತ್ತರ: {answer_text}")

        # ── Complex solution dict (enriched schema) ───────────────────────────
        solution = entry.get("solution", {})
        if isinstance(solution, dict) and solution:
            short_ans = solution.get("short_answer", "")
            if short_ans:
                short_ans = truncate_text(short_ans, max_chars=250)
                lines.append(f"ಪರಿಹಾರ: {short_ans}")

            # Step-by-step (actionable guidance) — only if steps add new info
            steps = solution.get("step_by_step", [])
            if steps:
                additive = [s for s in steps if str(s).strip() and str(s).strip() not in short_ans]
                if additive:
                    lines.append("ಹಂತಗಳು: " + " → ".join(str(s) for s in additive[:4]))

            # Organic solutions
            organic = solution.get("organic_solutions", [])
            if organic:
                lines.append("ಸಾವಯವ: " + "; ".join(str(s) for s in organic[:2]))

            # Recommended products
            products = solution.get("recommended_products", [])
            if products:
                lines.append("ಶಿಫಾರಸು ಉತ್ಪನ್ನಗಳು: " + ", ".join(str(p) for p in products[:3]))

            # Preventive measures
            preventive = solution.get("preventive_measures", [])
            if preventive:
                lines.append("ತಡೆಗಟ್ಟುವ ಕ್ರಮ: " + "; ".join(str(p) for p in preventive[:2]))

            # Warnings (important for safety)
            warnings = solution.get("warnings", [])
            if warnings:
                lines.append("⚠️ ಎಚ್ಚರಿಕೆ: " + "; ".join(str(w) for w in warnings[:2]))

        entry_text = "\n".join(lines)
        return truncate_text(entry_text, max_chars=MAX_ENTRY_CHARS)

    def build_minimal(self, entries: list[dict]) -> str:
        """
        Build a shorter context with only the most essential info.

        Used when the LLM context window is limited.
        Supports both simple and complex schema.

        Args:
            entries: Retrieved entry dicts

        Returns:
            Minimal context string
        """
        parts = []
        for entry in entries[:3]:
            question = entry.get("question", "")

            # Try simple answer first
            simple_ans = entry.get("answer", "")
            if simple_ans and isinstance(simple_ans, str):
                parts.append(f"Q: {question}\nA: {simple_ans[:300]}")
                continue

            # Fall back to complex solution dict
            solution = entry.get("solution", {})
            short_ans = solution.get("short_answer", "") if isinstance(solution, dict) else ""
            if short_ans:
                parts.append(f"Q: {question}\nA: {short_ans}")

        return "\n\n".join(parts)
