"""Build the vector index from processed knowledge base documents.
"""

import sys
import logging
from pathlib import Path

# Make sure backend modules are importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.kb_chunker import load_and_chunk_all
from app.services.kb_embedder import Embedder
from app.services.kb_vectorstore import VectorStore

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def main():
    # Step 1: Chunk
    logger.info("Loading and chunking documents...")
    chunks = load_and_chunk_all()
    if not chunks:
        logger.error("No chunks produced. Run kb_sources first.")
        sys.exit(1)
    logger.info("Chunks ready: %d", len(chunks))

    # Step 2: Embed
    logger.info("Initializing embedding model...")
    embedder = Embedder()

    texts = [c.text for c in chunks]
    logger.info("Embedding %d chunks...", len(texts))
    vectors = embedder.embed_texts(texts)
    logger.info("Embedding complete.")

    # Step 3: Store
    logger.info("Indexing into ChromaDB...")
    store = VectorStore()
    store.clear()
    store.add_chunks(chunks, vectors)

    # Step 4: Sanity checks
    test_queries = [
        ("What is diabetes?", "health topic"),
        ("Total Cholesterol: 215 mg/dL", "lab result"),
        ("Metformin 500 MG", "medication"),
        ("Hypertension diagnosis", "condition"),
    ]

    print(f"\n{'='*60}")
    print(f"Index built: {store.count()} chunks stored")
    print(f"\nSanity checks:")
    print(f"{'='*60}")

    for query, label in test_queries:
        qvec = embedder.embed_query(query)
        results = store.query(qvec, top_k=3)
        print(f"\n  [{label}] \"{query}\"")
        for i, r in enumerate(results, 1):
            title = r["metadata"].get("title", "?")
            score = r["score"]
            is_drug = "drug" in r["metadata"].get("filename", "")
            tag = " [drug]" if is_drug else ""
            print(f"    {i}. {title}{tag} (score: {score:.3f})")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()