"""
faiss_index.py — FAISS Vector Index Manager

WHAT IT DOES:
Manages the storage and searching of the vector database. It uses the 
FAISS library (Facebook AI Similarity Search) to find matches in 
milliseconds.

WHY IT EXISTS:
Standard databases are slow for "meaning-based" searches. This file 
implements a high-performance specialized index that stores vectors 
and their corresponding agricultural data on disk in 'models/'.

CONNECTIONS:
- Used by 'retriever.py' to find the top matching vectors.
- Used by 'scripts/ingest_data.py' to save the database after processing 
  new JSON files.
"""

import json
import numpy as np
import faiss
from pathlib import Path
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import FAISSIndexError


class FAISSIndex:
    """
    Manages a FAISS flat inner-product index for semantic retrieval.

    Inner product search on L2-normalised vectors == cosine similarity.
    This is the standard approach for Sentence Transformer retrieval.

    Index layout:
        - FAISS index stores vectors at integer positions 0, 1, 2, ...
        - Metadata list mirrors these positions:
          metadata[i] contains the full dataset entry for vector i
    """

    def __init__(self):
        self._index: faiss.IndexFlatIP | None = None
        self._metadata: list[dict] = []  # Parallel list to FAISS vectors

        self.index_path = Path(settings.FAISS_INDEX_PATH)
        self.metadata_path = Path(settings.FAISS_METADATA_PATH)
        self.dimension = settings.EMBEDDING_DIMENSION

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self, embeddings: np.ndarray, metadata: list[dict]):
        """
        Build the FAISS index from scratch.

        Args:
            embeddings: Float32 array of shape (n_entries, embedding_dim)
            metadata:   List of entry dicts, same length as embeddings

        Raises:
            FAISSIndexError: If shapes do not match or build fails
        """
        if len(embeddings) != len(metadata):
            raise FAISSIndexError(
                f"Embeddings count ({len(embeddings)}) != "
                f"metadata count ({len(metadata)})"
            )

        if embeddings.ndim != 2:
            raise FAISSIndexError(
                f"Expected 2D embeddings array, got shape {embeddings.shape}"
            )

        dimension = embeddings.shape[1]
        logger.info(
            "Building FAISS index | entries={n} | dimension={d}",
            n=len(embeddings), d=dimension
        )

        # IndexFlatIP = exact inner product search (cosine sim for normalised vecs)
        self._index = faiss.IndexFlatIP(dimension)
        self._index.add(embeddings)
        self._metadata = metadata

        logger.info(
            "FAISS index built successfully | total vectors={n}",
            n=self._index.ntotal
        )

    # ── Save / Load ───────────────────────────────────────────────────────────

    def save(self):
        """
        Persist the FAISS index and metadata to disk.

        Creates the directory if it does not exist.

        Raises:
            FAISSIndexError: If save fails
        """
        if self._index is None:
            raise FAISSIndexError("Cannot save — index has not been built yet")

        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)

            # Save FAISS binary index
            faiss.write_index(self._index, str(self.index_path))
            logger.info("FAISS index saved to: {path}", path=self.index_path)

            # Save metadata as JSON (preserves all entry fields)
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self._metadata, f, ensure_ascii=False, indent=2)
            logger.info("Metadata saved to: {path}", path=self.metadata_path)

        except Exception as e:
            raise FAISSIndexError(f"Failed to save index: {e}")

    def load(self):
        """
        Load a previously saved FAISS index and metadata from disk.

        Raises:
            FAISSIndexError: If files do not exist or loading fails
        """
        if not self.index_path.exists():
            raise FAISSIndexError(
                f"FAISS index not found at {self.index_path}. "
                "Run scripts/ingest_data.py to build the index first."
            )

        if not self.metadata_path.exists():
            raise FAISSIndexError(
                f"Metadata not found at {self.metadata_path}. "
                "Index may be corrupted — rebuild with scripts/ingest_data.py"
            )

        try:
            self._index = faiss.read_index(str(self.index_path))
            logger.info(
                "FAISS index loaded | vectors={n}", n=self._index.ntotal
            )

            with open(self.metadata_path, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)
            logger.info(
                "Metadata loaded | entries={n}", n=len(self._metadata)
            )

        except Exception as e:
            raise FAISSIndexError(f"Failed to load index: {e}")

    def is_loaded(self) -> bool:
        """Return True if the index is ready for searching."""
        return self._index is not None and len(self._metadata) > 0

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = None,
    ) -> list[dict]:
        """
        Find the top-k most similar entries to a query vector.

        Args:
            query_vector: 1D float32 numpy array (embedding of user query)
            top_k:        Number of results to return; defaults to settings.FAISS_TOP_K

        Returns:
            List of metadata dicts for the top-k matches,
            each with an added '_score' field (cosine similarity, 0–1)

        Raises:
            FAISSIndexError: If index is not loaded or search fails
        """
        if not self.is_loaded():
            raise FAISSIndexError(
                "Index not loaded. Call load() or build() first."
            )

        top_k = top_k or settings.FAISS_TOP_K

        # FAISS expects shape (1, dim) for a single query
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        try:
            scores, indices = self._index.search(query_vector, top_k)
        except Exception as e:
            raise FAISSIndexError(f"FAISS search failed: {e}")

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                # FAISS returns -1 when fewer than top_k results exist
                continue
            if idx >= len(self._metadata):
                logger.warning("FAISS returned invalid index {idx}", idx=idx)
                continue

            entry = dict(self._metadata[idx])
            entry["_score"] = float(score)  # Cosine similarity score
            results.append(entry)

        return results

    @property
    def total_vectors(self) -> int:
        """Return number of vectors stored in the index."""
        if self._index is None:
            return 0
        return self._index.ntotal
