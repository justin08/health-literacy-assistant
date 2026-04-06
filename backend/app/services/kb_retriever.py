"""Retrieve relevant knowledge base chunks for a clinical query.
"""

import logging

from app.services.kb_embedder import Embedder
from app.services.kb_vectorstore import VectorStore

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 5


class Retriever:
    def __init__(self, embedder: Embedder = None, store: VectorStore = None):
        self.embedder = embedder or Embedder()
        self.store = store or VectorStore()

    def retrieve(self, query: str, top_k: int = DEFAULT_TOP_K) -> list[dict]:
        """Find the top-k most relevant chunks for a query.

        Returns list of dicts with 'text', 'metadata', and 'score'.
        """
        query_vector = self.embedder.embed_query(query)
        results = self.store.query(query_vector, top_k=top_k)

        logger.info(
            "Query: \"%s...\" → %d results (top: %.3f)",
            query[:50], len(results),
            results[0]["score"] if results else 0,
        )
        return results

    def retrieve_as_context(self, query: str, top_k: int = DEFAULT_TOP_K) -> str:
        """Retrieve and format chunks as a single context string for the prompt."""
        results = self.retrieve(query, top_k)

        if not results:
            return "No relevant reference information found."

        sections = []
        for i, r in enumerate(results, 1):
            title = r["metadata"].get("title", "Unknown")
            source = r["metadata"].get("source_url", "")
            header = f"[Source {i}: {title}]"
            if source:
                header += f" ({source})"
            sections.append(f"{header}\n{r['text']}")

        return "\n\n---\n\n".join(sections)

    @property
    def ready(self) -> bool:
        """Check if the retriever has an indexed knowledge base."""
        return self.store.count() > 0


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    retriever = Retriever()
    print(f"Knowledge base ready: {retriever.ready} ({retriever.store.count()} chunks)\n")

    test_queries = [
        "Total Cholesterol: 215 mg/dL. Reference range: 0-200 mg/dL. Interpretation: H.",
        "Diagnosis: Diabetes mellitus type 2. Status: active.",
        "Medication: Metformin hydrochloride 500 MG Oral Tablet. Dosage: 2x per day via oral.",
        "Hemoglobin A1c: 7.2%. Reference range: 4.0-5.7%. Interpretation: H.",
        "Medication: Ibuprofen 200 MG Oral Tablet.",
    ]

    for q in test_queries:
        print(f"{'='*60}")
        print(f"Query: {q}")
        results = retriever.retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            title = r["metadata"].get("title", "?")
            is_drug = "drug" in r["metadata"].get("filename", "")
            tag = " [drug]" if is_drug else ""
            print(f"  {i}. {title}{tag} (score: {r['score']:.3f})")
        print()