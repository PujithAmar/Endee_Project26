"""Local embedding generator using sentence-transformers (all-MiniLM-L6-v2, 384-dim)."""
from __future__ import annotations
from typing import List, Optional
import logging
import threading

logger = logging.getLogger(__name__)


class EmbeddingService:
    _instance: Optional["EmbeddingService"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._model = None
        self.dimension = 384

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers/all-MiniLM-L6-v2 ...")
            self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            logger.info("Embedding model ready.")

    def encode(self, texts: List[str]) -> List[List[float]]:
        self._load()
        if not texts:
            return []
        vecs = self._model.encode(texts, convert_to_tensor=False, show_progress_bar=False, normalize_embeddings=True)
        return [v.tolist() for v in vecs]

    def encode_one(self, text: str) -> List[float]:
        return self.encode([text])[0]


_singleton = EmbeddingService()


def get_embedder() -> EmbeddingService:
    return _singleton
