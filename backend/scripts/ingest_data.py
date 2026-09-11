"""
ingest_data.py — Dataset Ingestion & FAISS Index Builder Script

Run this script ONCE before starting the server to:
1. Load all agricultural JSON datasets from data/raw/
2. Validate and preprocess each entry
3. Generate Sentence Transformer embeddings
4. Build and save the FAISS index to models/faiss_index/

After running this, the FAISS index is ready for semantic retrieval.

Usage:
    python scripts/ingest_data.py
    python scripts/ingest_data.py --dataset data/raw/my_dataset.json
    python scripts/ingest_data.py --sample   (use sample dataset for testing)
"""

import sys
import argparse
import time
from pathlib import Path

# Add project root to path so imports work correctly
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.utils.logger import logger
from app.rag.dataset_loader import DatasetLoader
from app.rag.preprocessor import Preprocessor
from app.rag.embedder import Embedder
from app.rag.faiss_index import FAISSIndex


def ingest(dataset_path: str = None, use_sample: bool = False):
    """
    Full ingestion pipeline: load → preprocess → embed → index → save.

    Args:
        dataset_path: Override default dataset path
        use_sample:   Use the sample dataset (for testing)
    """
    logger.info("=" * 60)
    logger.info("AGRICULTURAL DATASET INGESTION")
    logger.info("=" * 60)
    start_time = time.time()

    # ── Step 1: Load Dataset ──────────────────────────────────────────────────
    logger.info("Step 1/5: Loading dataset...")
    entries = []
    loader = DatasetLoader(dataset_path=dataset_path)

    if use_sample:
        entries = loader.load_sample()
    else:
        # Load from primary raw dataset path
        try:
            entries.extend(loader.load_all())
        except Exception as e:
            logger.debug("No primary dataset found: {e}", e=e)

        # Load from the custom database path (where the user added their file)
        try:
            loader_db = DatasetLoader(dataset_path=settings.DATABASE_PATH)
            db_entries = loader_db.load_all()
            
            # Merge while avoiding duplicates based on ID
            existing_ids = {e.get("id") for e in entries if e.get("id")}
            merged_count = 0
            for entry in db_entries:
                if entry.get("id") not in existing_ids:
                    entries.append(entry)
                    merged_count += 1
            if merged_count > 0:
                logger.info("Merged {n} entries from custom database", n=merged_count)
        except Exception as e:
            logger.debug("No database files found to merge: {e}", e=e)

    if not entries:
        logger.error(
            "No entries found! Add JSON files to {raw} or {db} and try again.",
            raw=settings.DATASET_PATH,
            db=settings.DATABASE_PATH
        )
        logger.info(
            "Tip: You can also run with --sample for a quick test."
        )
        sys.exit(1)

    stats = loader.get_stats(entries)
    logger.info(
        "Loaded {n} entries | Languages: {l} | Crops: {c}",
        n=stats["total"],
        l=list(stats["by_language"].keys()),
        c=len(stats["by_crop"]),
    )

    # ── Step 2: Preprocess ────────────────────────────────────────────────────
    logger.info("Step 2/5: Preprocessing entries...")
    preprocessor = Preprocessor()
    processed_entries = preprocessor.process(entries)
    retrieval_texts = preprocessor.build_texts_for_embedding(processed_entries)
    logger.info("Preprocessing complete: {n} entries ready", n=len(processed_entries))

    # ── Step 3: Generate Embeddings ───────────────────────────────────────────
    logger.info(
        "Step 3/5: Generating embeddings with model: {m}",
        m=settings.EMBEDDING_MODEL
    )
    logger.info("This may take a few minutes on first run (model download)...")

    embedder = Embedder()
    embeddings = embedder.encode(
        retrieval_texts,
        batch_size=32,
        show_progress=True,
    )
    logger.info(
        "Embeddings generated | shape={shape} | dimension={dim}",
        shape=embeddings.shape,
        dim=embeddings.shape[1] if len(embeddings.shape) > 1 else 0,
    )

    # ── Step 4: Build FAISS Index ─────────────────────────────────────────────
    logger.info("Step 4/5: Building FAISS index...")
    faiss_index = FAISSIndex()
    faiss_index.build(embeddings, processed_entries)
    logger.info(
        "FAISS index built | {n} vectors", n=faiss_index.total_vectors
    )

    # ── Step 5: Save to Disk ──────────────────────────────────────────────────
    logger.info("Step 5/5: Saving index to disk...")
    faiss_index.save()

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("✓ Ingestion complete in {t:.1f}s", t=elapsed)
    logger.info("✓ FAISS index: {p}", p=settings.FAISS_INDEX_PATH)
    logger.info("✓ Metadata:    {p}", p=settings.FAISS_METADATA_PATH)
    logger.info("=" * 60)
    logger.info("Now start the server: uvicorn app.main:app --reload")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest agricultural dataset and build FAISS index"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="Path to dataset file or directory (default: data/raw/)"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Use the sample dataset for quick testing"
    )
    args = parser.parse_args()
    ingest(dataset_path=args.dataset, use_sample=args.sample)
