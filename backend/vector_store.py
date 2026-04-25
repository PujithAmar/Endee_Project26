"""Endee (Serverless) vector store wrapper for SkillBridge RAG pipeline."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
import logging

from endee import Endee, Precision

logger = logging.getLogger(__name__)


class EndeeStore:
    def __init__(self):
        token = os.environ["ENDEE_TOKEN"]
        self.index_name = os.environ.get("ENDEE_INDEX_NAME", "skillbridge")
        self.dimension = 384
        self.client = Endee(token)
        self._ensure_index()
        self.index = self.client.get_index(name=self.index_name)

    def _ensure_index(self):
        try:
            existing = self.client.list_indexes() or {}
            names = []
            if isinstance(existing, dict):
                names = [i.get("name") if isinstance(i, dict) else i for i in (existing.get("indexes") or [])]
            if self.index_name not in names:
                self.client.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    space_type="cosine",
                    precision=Precision.INT8,
                )
                logger.info("Created Endee index: %s", self.index_name)
        except Exception as e:
            logger.warning("ensure_index: %s", e)

    def upsert(self, items: List[Dict[str, Any]]):
        """items: [{id, vector, meta, filter}]  (max 1000 per call)"""
        if not items:
            return 0
        batch = []
        for it in items:
            batch.append({
                "id": str(it["id"]),
                "vector": it["vector"],
                "meta": it.get("meta", {}),
                "filter": it.get("filter", {}),
            })
        # Endee max 1000 per upsert
        for i in range(0, len(batch), 1000):
            self.index.upsert(batch[i:i + 1000])
        return len(batch)

    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filter: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        kwargs = {"vector": vector, "top_k": top_k, "include_vectors": False}
        if filter:
            kwargs["filter"] = filter
        try:
            results = self.index.query(**kwargs)
            return results or []
        except Exception as e:
            logger.error("Endee query failed: %s", e)
            return []

    def delete_by_session(self, session_id: str):
        # Endee SDK deletion per-id; we track ids in Mongo, so no-op here.
        pass


_store: Optional[EndeeStore] = None


def get_store() -> EndeeStore:
    global _store
    if _store is None:
        _store = EndeeStore()
    return _store
