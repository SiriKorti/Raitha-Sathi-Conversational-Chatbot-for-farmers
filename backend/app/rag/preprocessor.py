"""
preprocessor.py — Dataset Preprocessing Module

WHAT IT DOES:
Transforms raw loaded dataset entries into clean, enriched records ready
for embedding and FAISS indexing. Crucially, it builds a unique, rich
'retrieval_text' per entry by combining question, symptoms, causes, topic,
and keywords — so every entry gets a distinct semantic vector.

WHY IT EXISTS:
The raw database's generic 'retrieval_text' field is identical for all
entries of the same crop. This file rebuilds it from each entry's unique
signals so FAISS can distinguish between 'leaf yellowing disease' and
'irrigation advice' even though both are for the same crop.

CONNECTIONS:
- Called by 'scripts/ingest_data.py' to prepare data before embedding.
- Outputs the 'retrieval_text' strings consumed by 'embedder.py'.
"""

from app.utils.text_utils import clean_text
from app.utils.logger import logger


class Preprocessor:
    """
    Prepares dataset entries for embedding generation.

    Each entry passes through:
    1. Text cleaning (Unicode normalisation, whitespace)
    2. Rich retrieval_text construction from all unique per-entry fields
    3. Metadata enrichment (entry index for FAISS mapping)
    """

    def process(self, entries: list[dict]) -> list[dict]:
        """
        Process a list of raw dataset entries.

        Args:
            entries: Raw dataset entries from DatasetLoader

        Returns:
            Enriched entries with clean, unique 'retrieval_text' fields
        """
        processed = []
        for i, entry in enumerate(entries):
            try:
                clean_entry = self._process_single(entry, index=i)
                processed.append(clean_entry)
            except Exception as e:
                logger.warning(
                    "Failed to process entry #{i} ({id}): {e}",
                    i=i, id=entry.get("id", "?"), e=e
                )

        logger.info(
            "Preprocessed {n}/{total} entries successfully",
            n=len(processed), total=len(entries)
        )
        return processed

    def _process_single(self, entry: dict, index: int) -> dict:
        """
        Process a single dataset entry.

        Args:
            entry: Raw entry dict
            index: Position in dataset (used as FAISS index)

        Returns:
            Processed entry dict
        """
        # Work on a copy to avoid mutating original
        entry = dict(entry)

        # Clean main text fields
        for field in ["question", "problem_description"]:
            if entry.get(field):
                entry[field] = clean_text(entry[field])

        # Clean solution text fields
        solution = entry.get("solution", {})
        if isinstance(solution, dict):
            for sol_field in ["short_answer", "detailed_answer"]:
                if solution.get(sol_field):
                    solution[sol_field] = clean_text(solution[sol_field])
            entry["solution"] = solution

        # ── Build rich, per-entry-unique retrieval_text ───────────────────────
        # ALWAYS rebuild from unique per-entry fields.
        # The raw DB has identical retrieval_text for all 200 rice entries —
        # rebuilding ensures every entry gets a distinct semantic vector.
        entry["retrieval_text"] = self._build_rich_retrieval_text(entry)

        # Store the FAISS index position for later metadata lookup
        entry["_index"] = index

        return entry

    def _build_rich_retrieval_text(self, entry: dict) -> str:
        """
        Build a semantically unique retrieval text for a single entry.

        Combines all unique signals:
          - crop_name + topic (domain anchor)
          - question + all question_variants (exact phrasings)
          - symptoms (farmer-observable signs)
          - causes (diagnostic reasoning)
          - keywords (vocabulary bridging)
          - short_answer (grounds vector in the solution)

        This ensures two entries about different problems on the same crop
        will have meaningfully different vectors.
        """
        parts = []

        # 1. Domain anchor: crop name + topic
        crop = entry.get("crop_name", "")
        topic = entry.get("topic", "")
        subtopic = entry.get("subtopic", "")
        if crop:
            parts.append(crop)
        if topic:
            parts.append(topic)
        if subtopic:
            parts.append(subtopic)

        # 2. Primary question
        question = entry.get("question", "")
        if question:
            parts.append(question)

        # 3. All question_variants (different phrasings of the same query)
        for variant in entry.get("question_variants", []):
            if variant and variant.strip() and variant.strip() != question:
                parts.append(variant.strip())

        # 4. Keywords (domain tags)
        keywords = entry.get("keywords", [])
        if keywords:
            parts.append(" ".join(keywords))

        # 5. Symptoms (key for diagnosis queries)
        symptoms = entry.get("symptoms", [])
        if symptoms:
            parts.append("ಲಕ್ಷಣಗಳು: " + ", ".join(str(s) for s in symptoms))

        # 6. Causes (supports diagnostic reasoning)
        causes = entry.get("causes", [])
        if causes:
            parts.append("ಕಾರಣಗಳು: " + ", ".join(str(c) for c in causes[:3]))

        # 7. Short answer (grounds the vector in the actual solution)
        solution = entry.get("solution", {})
        if isinstance(solution, dict):
            short_ans = solution.get("short_answer", "")
            if short_ans:
                parts.append(short_ans)
                
        # Support for simple answer format
        simple_ans = entry.get("answer", "")
        if isinstance(simple_ans, str) and simple_ans:
            parts.append(simple_ans)

        # 8. Problem description (background context)
        prob = entry.get("problem_description", "")
        if prob:
            parts.append(prob[:200])

        combined = " | ".join(filter(None, parts))
        return clean_text(combined) if combined else entry.get("question", "")

    def build_texts_for_embedding(self, processed_entries: list[dict]) -> list[str]:
        """
        Extract the retrieval_text strings from all processed entries.

        This list is passed directly to the Embedder for vectorisation.

        Args:
            processed_entries: Output of self.process()

        Returns:
            List of retrieval_text strings (same order as entries)
        """
        texts = []
        for entry in processed_entries:
            text = entry.get("retrieval_text", "")
            if not text:
                # Fallback to question if retrieval_text is somehow empty
                text = entry.get("question", "")
            texts.append(text)
        return texts
