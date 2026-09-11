"""
retriever.py — Semantic Retrieval Engine

WHAT IT DOES:
The central retrieval pipeline of the RAG system. It takes a user's 
question, converts it into a vector, and searches the FAISS index 
to find the most relevant pieces of agricultural knowledge.

WHY IT EXISTS:
This is the "R" in RAG (Retrieval-Augmented Generation). It ensures that 
the AI's answers are grounded in actual facts from your dataset rather 
than relying solely on the LLM's internal (and potentially outdated) memory.

CONNECTIONS:
- Uses 'embedder.py' to turn text into searchable numbers.
- Uses 'faiss_index.py' to perform the high-speed similarity lookup.
- Uses 'metadata_filter.py' to narrow down results (e.g., by crop or region).
"""

from app.rag.embedder import Embedder
from app.rag.faiss_index import FAISSIndex
from app.rag.metadata_filter import MetadataFilter
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import RetrievalError


class Retriever:
    """
    Semantic retrieval engine for agricultural knowledge.

    Pipeline:
        User Query (Kannada/English text)
            → Sentence Transformer embedding
            → FAISS similarity search
            → Metadata filtering (optional)
            → Ranked result list
    """

    def __init__(self):
        self.embedder = Embedder()
        self.faiss_index = FAISSIndex()
        self.metadata_filter = MetadataFilter()
        self._loaded = False

    # ── Initialisation ────────────────────────────────────────────────────────

    def load(self):
        """
        Load the FAISS index from disk.

        Must be called once before retrieve() is used.
        Called automatically by the FastAPI startup event.

        Raises:
            RetrievalError: If index loading fails
        """
        try:
            self.faiss_index.load()
            self._loaded = True
            logger.info(
                "Retriever ready | index size={n}",
                n=self.faiss_index.total_vectors
            )
        except Exception as e:
            raise RetrievalError(f"Failed to load retrieval index: {e}")

    # ── Core Retrieval ────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        crop_name: str = None,
        season: str = None,
        region: str = None,
        topic: str = None,
        intent: str = None,
        extracted_entities: dict = None,
    ) -> list[dict]:
        """
        Retrieve the most relevant dataset entries using hybrid keyword + semantic search.
        """
        if not self._loaded:
            raise RetrievalError(
                "Retriever not loaded. Call retriever.load() first."
            )

        top_k = top_k or settings.FAISS_TOP_K

        try:
            # Resolve canonical crop name (check both crop_name and query text)
            from app.utils.text_utils import extract_crop_from_text
            canonical_user_crop = extract_crop_from_text(crop_name) if crop_name else None
            if not canonical_user_crop:
                canonical_user_crop = extract_crop_from_text(query)
            if not canonical_user_crop and crop_name:
                canonical_user_crop = crop_name.strip().lower()

            # Step 1: Pre-filter candidate metadata pool to ensure zero cross-crop bleed
            metadata_pool = self.faiss_index._metadata
            candidate_indices = []
            
            for idx, entry in enumerate(metadata_pool):
                # Crop lock validation — ensure ZERO cross-crop bleed
                if canonical_user_crop:
                    entry_crop_raw = entry.get("crop_name", "")
                    entry_crop_canonical = extract_crop_from_text(entry_crop_raw) or entry_crop_raw.strip().lower()
                    user_crop_clean = canonical_user_crop.strip().lower()
                    # Use EXACT canonical equality — substring check causes "ಜೋಳ" (Jowar) to
                    # bleed into "ಮೆಕ್ಕೆಜೋಳ" (Maize) entries since "ಜೋಳ" is a substring.
                    if user_crop_clean != entry_crop_canonical:
                        continue
                
                # Season filter
                if season:
                    entry_season = str(entry.get("season", "")).lower()
                    if season.lower() not in entry_season:
                        continue
                        
                # Region filter
                if region:
                    entry_region = str(entry.get("region", "")).lower()
                    if region.lower() not in entry_region:
                        continue
                        
                candidate_indices.append(idx)

            if not candidate_indices:
                logger.debug("No candidates matching metadata filters.")
                return []

            # Step 1.1: Agricultural bilingual keyword expansion for cross-lingual & Kanglish queries
            AGRI_BILINGUAL_MAP = {
                "water": ["ನೀರು", "ನೀರಾವರಿ", "ಹಾಯಿಸಲು"],
                "watering": ["ನೀರು", "ನೀರಾವರಿ", "ಹಾಯಿಸಲು"],
                "irrigate": ["ನೀರಾವರಿ", "ನೀರು", "ಹಾಯಿಸಲು"],
                "irrigation": ["ನೀರಾವರಿ", "ನೀರು", "ವೇಳಾಪಟ್ಟಿ"],
                "neeru": ["ನೀರು", "ನೀರಾವರಿ"],
                "neeravari": ["ನೀರಾವರಿ", "ನೀರು"],
                "fertilizer": ["ಗೊಬ್ಬರ", "ರಾಸಾಯನಿಕ", "ರಸಗೊಬ್ಬರ", "npk", "ಪೋಷಕಾಂಶ"],
                "fertilizers": ["ಗೊಬ್ಬರ", "ರಾಸಾಯನಿಕ", "ರಸಗೊಬ್ಬರ", "npk"],
                "manure": ["ಗೊಬ್ಬರ", "ಸಾವಯವ", "ಕಾಂಪೋಸ್ಟ್"],
                "nutrient": ["ಪೋಷಕಾಂಶ", "ಗೊಬ್ಬರ"],
                "nutrients": ["ಪೋಷಕಾಂಶ", "ಗೊಬ್ಬರ"],
                "dosage": ["ಪ್ರಮಾಣ", "ಶಿಫಾರಸು"],
                "gobbara": ["ಗೊಬ್ಬರ", "ರಸಗೊಬ್ಬರ"],
                "rasagobbara": ["ರಸಗೊಬ್ಬರ", "ಗೊಬ್ಬರ", "npk"],
                "disease": ["ರೋಗ", "ಬೆಂಕಿ", "ಬೂದಿ", "ಕೊಳೆತ"],
                "diseases": ["ರೋಗ", "ಬೆಂಕಿ", "ಬೂದಿ"],
                "fungus": ["ಶಿಲೀಂಧ್ರ", "ಶಿಲೀಂಧ್ರನಾಶಕ"],
                "blight": ["ಬೆಂಕಿ", "ರೋಗ"],
                "wilt": ["ಬಾಡುವಿಕೆ", "ಒಣಗುವಿಕೆ"],
                "roga": ["ರೋಗ"],
                "pest": ["ಕೀಟ", "ಹುಳ", "ಕೀಟನಾಶಕ", "ಕೊರಕ"],
                "pests": ["ಕೀಟ", "ಹುಳ", "ಕೀಟನಾಶಕ"],
                "insect": ["ಕೀಟ", "ಹುಳ"],
                "insects": ["ಕೀಟ", "ಹುಳ"],
                "worm": ["ಹುಳ", "ಕೊರಕ"],
                "keeta": ["ಕೀಟ", "ಹುಳ"],
                "hula": ["ಹುಳ", "ಕೀಟ"],
                "seed": ["ಬೀಜ", "ಬಿತ್ತನೆ", "ತಳಿ"],
                "seeds": ["ಬೀಜ", "ಬಿತ್ತನೆ", "ತಳಿ"],
                "sowing": ["ಬಿತ್ತನೆ", "ಬಿತ್ತಲು", "ಸಮಯ"],
                "variety": ["ತಳಿ", "ತಳಿಗಳು"],
                "varieties": ["ತಳಿ", "ತಳಿಗಳು"],
                "bithane": ["ಬಿತ್ತನೆ"],
                "beeja": ["ಬೀಜ"],
                "thali": ["ತಳಿ"],
                "subsidy": ["ಸಹಾಯಧನ", "ಸಬ್ಸಿಡಿ", "ಯೋಜನೆ"],
                "subsidies": ["ಸಹಾಯಧನ", "ಸಬ್ಸಿಡಿ", "ಯೋಜನೆಗಳು"],
                "scheme": ["ಯೋಜನೆ", "ಸರ್ಕಾರಿ", "ಸಹಾಯ"],
                "schemes": ["ಯೋಜನೆಗಳು", "ಸರ್ಕಾರಿ", "ಸಹಾಯಧನ"],
                "government": ["ಸರ್ಕಾರಿ", "ಸರ್ಕಾರ"],
                "msp": ["ಬೆಂಬಲ", "ಬೆಲೆ", "ಖರೀದಿ", "ಕೇಂದ್ರ"],
                "support price": ["ಬೆಂಬಲ", "ಬೆಲೆ"],
                "yojane": ["ಯೋಜನೆ"],
                "sahayadhana": ["ಸಹಾಯಧನ"],
            }
            expanded_terms = []
            q_lower = query.lower()
            for k, syns in AGRI_BILINGUAL_MAP.items():
                if k in q_lower:
                    expanded_terms.extend(syns)

            # Step 2: Encode the query (with bilingual assistance if non-Kannada query)
            embedding_query = f"{query} {' '.join(set(expanded_terms))}".strip() if expanded_terms else query
            query_vector = self.embedder.encode_single(embedding_query)

            # Step 3: Vector similarity search (FAISS Index)
            # Search all vectors to prevent premature truncation of crop candidates
            raw_results = self.faiss_index.search(query_vector, top_k=len(metadata_pool))

            # Step 4: Hybrid Keyword + Semantic Scoring on filtered candidates
            # Normalize query words
            from app.rag.database_searcher import DatabaseSearcher
            normalizer = DatabaseSearcher._normalize
            normalized_query = normalizer(query)
            query_words = set(normalized_query.split())
            if expanded_terms:
                query_words.update(set(normalizer(t) for t in expanded_terms))

            # Configurable Hybrid Weights
            SEMANTIC_WEIGHT = 0.60
            KEYWORD_WEIGHT = 0.25
            METADATA_WEIGHT = 0.15

            hybrid_results = []
            candidate_set = set(candidate_indices)

            for entry in raw_results:
                idx = entry.get("_index")
                if idx not in candidate_set:
                    continue

                # 1. Semantic Score (from FAISS)
                semantic_score = entry.get("_score", 0.0)

                # 2. Keyword/Entity Score
                retrieval_text = normalizer(entry.get("retrieval_text", ""))
                entry_words = set(retrieval_text.split())
                
                # Basic overlap
                intersect = query_words & entry_words
                base_keyword_score = len(intersect) / len(query_words) if query_words else 0.0
                
                # Boost for tagged agricultural entities/keywords
                entry_keywords = set([normalizer(k) for k in entry.get("keywords", [])])
                entity_overlap = query_words & entry_keywords
                entity_boost = (len(entity_overlap) / len(entry_keywords)) if entry_keywords else 0.0
                
                # Give extra weight if extracted entities match
                extracted_boost = 0.0
                if extracted_entities:
                    for key, val in extracted_entities.items():
                        if val and normalizer(val) in retrieval_text:
                            extracted_boost += 0.2
                            
                keyword_score = min(1.0, base_keyword_score + (0.5 * entity_boost) + extracted_boost)

                # 3. Metadata Score
                metadata_score = 0.0
                entry_topic = str(entry.get("topic", "")).lower()
                entry_subtopic = str(entry.get("subtopic", "")).lower()
                
                if intent:
                    intent_clean = intent.lower()
                    intent_synonyms = {
                        "irrigation": ["ನೀರಾವರಿ", "irrigation", "ನೀರು"],
                        "fertilizer": ["ಗೊಬ್ಬರ", "ಪೋಷಕಾಂಶ", "fertilizer", "nutrition"],
                        "pest": ["ಕೀಟ", "pest", "ಹುಳ"],
                        "disease": ["ರೋಗ", "disease", "ಶಿಲೀಂಧ್ರ"],
                        "variety": ["ತಳಿ", "variety"],
                        "government_scheme": ["ಯೋಜನೆ", "ಸಹಾಯಧನ", "scheme", "subsidy", "ಬೆಂಬಲ ಬೆಲೆ", "msp"],
                    }.get(intent_clean, [intent_clean])
                    if any(syn in entry_topic or syn in entry_subtopic for syn in intent_synonyms):
                        metadata_score += 0.5
                    elif any(syn in entry_words for syn in intent_synonyms):
                        metadata_score += 0.3

                if topic and (topic.lower() in entry_topic or topic.lower() in entry_subtopic):
                    metadata_score += 0.5
                if canonical_user_crop:
                    # If it passed the hard filter, it's the correct crop, grant metadata score
                    metadata_score += 0.5
                    
                metadata_score = min(1.0, metadata_score)

                # 4. Final Hybrid Score
                hybrid_score = (
                    (SEMANTIC_WEIGHT * semantic_score) + 
                    (KEYWORD_WEIGHT * keyword_score) + 
                    (METADATA_WEIGHT * metadata_score)
                )
                
                entry_copy = dict(entry)
                entry_copy["_score"] = hybrid_score
                entry_copy["_semantic_score"] = semantic_score
                entry_copy["_keyword_score"] = keyword_score
                entry_copy["_metadata_score"] = metadata_score
                hybrid_results.append(entry_copy)

            # Rank by hybrid score
            hybrid_results.sort(key=lambda x: x["_score"], reverse=True)
            final_results = hybrid_results[:top_k]
            
            # Step 5: Confidence Estimation
            for i, res in enumerate(final_results):
                score = res["_score"]
                # Margin between this result and the next best result
                margin = (score - final_results[i+1]["_score"]) if i + 1 < len(final_results) else score
                
                # Explicit Confidence Levels
                if score >= 0.70 and margin >= 0.05:
                    confidence = "HIGH"
                elif score >= 0.55:
                    confidence = "MEDIUM"
                else:
                    confidence = "LOW"
                    
                res["_confidence_level"] = confidence
                res["_confidence_margin"] = margin

            logger.debug(
                "Retrieved {n} hybrid results for query: {q} | Top Confidence: {c}",
                n=len(final_results),
                q=query[:60],
                c=final_results[0]["_confidence_level"] if final_results else "NONE"
            )
            return final_results

        except Exception as e:
            raise RetrievalError(f"Retrieval pipeline error: {e}")

    def retrieve_with_scores(self, query: str, top_k: int = None) -> list[tuple[dict, float]]:
        """
        Retrieve results along with their similarity scores.

        Returns:
            List of (entry_dict, score) tuples
        """
        results = self.retrieve(query, top_k=top_k)
        return [(entry, entry.get("_score", 0.0)) for entry in results]
