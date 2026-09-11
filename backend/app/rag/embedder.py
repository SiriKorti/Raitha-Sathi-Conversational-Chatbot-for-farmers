"""
embedder.py — Sentence Transformer Embedding Generator

WHAT IT DOES:
Converts text strings (Kannada or English) into mathematical vectors 
(embeddings). It uses the 'paraphrase-multilingual-MiniLM-L12-v2' model, 
which understands the semantic meaning of sentences.

WHY IT EXISTS:
Computers cannot "read" text, but they can compare lists of numbers. 
This file provides the mathematical bridge that allows the system to 
find answers that mean the same thing as the question, even if the 
words used are different.

CONNECTIONS:
- Used by 'retriever.py' to vectorize incoming user questions.
- Used by 'dataset_loader.py' (via ingestion scripts) to vectorize 
  the entire knowledge base.
"""

import numpy as np
from typing import Union
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.utils.logger import logger
from app.utils.exceptions import EmbeddingError, ModelLoadError


class Embedder:
    """
    Wraps a Sentence Transformer model for generating text embeddings.

    Features:
    - Lazy loading (model loaded only when first needed)
    - Batch encoding for efficiency
    - Supports fine-tuned model path if available
    - Normalised embeddings for cosine similarity compatibility
    """

    def __init__(self, model_name: str = None):
        """
        Args:
            model_name: HuggingFace model name or local path.
                        Defaults to settings.EMBEDDING_MODEL.
                        If a fine-tuned model exists, it is used automatically.
        """
        self._model: SentenceTransformer | None = None

        fine_tuned = settings.get_fine_tuned_model_dir()
        if fine_tuned.exists() and any(fine_tuned.iterdir()):
            self.model_name = str(fine_tuned)
            logger.info("Using fine-tuned embedding model from: {path}", path=self.model_name)
        else:
            self.model_name = model_name or settings.EMBEDDING_MODEL
            logger.info("Using base embedding model: {name}", name=self.model_name)

    # ── Model Loading ─────────────────────────────────────────────────────────

    @property
    def model(self) -> SentenceTransformer:
        """
        Lazily load the model on first access.
        This avoids slow startup when the model isn't needed immediately.
        """
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self):
        """Download (if needed) and load the Sentence Transformer model."""
        try:
            logger.info("Loading embedding model: {name}", name=self.model_name)
            self._model = SentenceTransformer(self.model_name)
            logger.info(
                "Embedding model loaded | dimension={dim}",
                dim=self._model.get_sentence_embedding_dimension()
            )
        except Exception as e:
            raise ModelLoadError(
                f"Failed to load embedding model '{self.model_name}': {e}"
            )

    # ── Core Encoding ─────────────────────────────────────────────────────────

    def encode(
        self,
        texts: Union[str, list[str]],
        batch_size: int = 32,
        normalize: bool = True,
        show_progress: bool = False,
    ) -> np.ndarray:
        """
        Encode one or more text strings into embedding vectors.

        Args:
            texts:         Single string or list of strings
            batch_size:    Number of texts to encode per batch
            normalize:     If True, L2-normalise vectors (required for cosine sim)
            show_progress: Show a tqdm progress bar for large batches

        Returns:
            numpy array of shape (n_texts, embedding_dim)

        Raises:
            EmbeddingError: If encoding fails
        """
        # Accept a single string
        if isinstance(texts, str):
            texts = [texts]

        if not texts:
            return np.array([])

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
            )
            return embeddings.astype(np.float32)  # FAISS requires float32

        except Exception as e:
            raise EmbeddingError(f"Encoding failed: {e}")

    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode a single text string.

        Convenience wrapper around encode() that returns a 1D vector.

        Args:
            text: Text to encode

        Returns:
            1D numpy array of shape (embedding_dim,)
        """
        vectors = self.encode([text])
        return vectors[0]

    def get_dimension(self) -> int:
        """Return the embedding vector dimension."""
        return self.model.get_sentence_embedding_dimension()
