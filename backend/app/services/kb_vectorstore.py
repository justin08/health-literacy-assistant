"""ChromaDB vector store for the health knowledge base.
"""

import logging
from pathlib import Path

import chromadb

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_PERSIST_DIR = str(DATA_DIR / "chroma_store")
COLLECTION_NAME = "health_knowledge"


class VectorStore:
    def __init__(self, persist_dir: str = DEFAULT_PERSIST_DIR):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB '%s' — %d existing documents",
            COLLECTION_NAME, self.collection.count(),
        )

    def add_chunks(self, chunks, vectors: list[list[float]]):
        """Insert chunks with pre-computed embeddings."""
        ids = [f"chunk_{i:05d}" for i in range(len(chunks))]
        documents = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        # ChromaDB batch limit — insert in batches of 500
        batch = 500
        for start in range(0, len(chunks), batch):
            end = min(start + batch, len(chunks))
            self.collection.add(
                ids=ids[start:end],
                documents=documents[start:end],
                embeddings=vectors[start:end],
                metadatas=metadatas[start:end],
            )

        logger.info("Indexed %d chunks — total: %d", len(chunks), self.collection.count())

    def query(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        """Find the top-k most similar chunks."""
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        for i in range(len(results["ids"][0])):
            hits.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i],
            })
        return hits

    def clear(self):
        """Delete and recreate the collection."""
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Collection cleared.")

    def count(self) -> int:
        return self.collection.count()