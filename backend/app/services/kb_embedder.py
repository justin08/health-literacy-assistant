"""Generate embeddings using a local HuggingFace model.
"""
 
import logging
from sentence_transformers import SentenceTransformer
 
logger = logging.getLogger(__name__)
 
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
 
 
class Embedder:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        logger.info("Loading embedding model: %s", model_name)
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info("Model loaded — %d dimensions", self.dimension)
 
    def embed_texts(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        """Embed a batch of texts. Used at index time."""
        vectors = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
        return vectors.tolist()
 
    def embed_query(self, query: str) -> list[float]:
        """Embed a single query. Used at retrieval time."""
        return self.model.encode(query).tolist()