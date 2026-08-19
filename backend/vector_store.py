"""Endee vector store wrapper with local fallback for SkillBridge RAG pipeline."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
import logging
import math

logger = logging.getLogger(__name__)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class LocalVectorStore:
    def __init__(self):
        self.items: List[Dict[str, Any]] = []

    def upsert(self, items: List[Dict[str, Any]]):
        for it in items:
            self.items.append({
                "id": str(it["id"]),
                "vector": it["vector"],
                "meta": it.get("meta", {}),
                "filter": it.get("filter", {}),
            })
        return len(items)

    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filter: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        scored = []
        for it in self.items:
            if filter:
                match = True
                for f in filter:
                    for k, v in f.items():
                        if it.get("filter", {}).get(k) != v and it.get("meta", {}).get(k) != v:
                            match = False
                            break
                if not match:
                    continue
            sim = cosine_similarity(vector, it["vector"])
            scored.append({"id": it["id"], "score": sim, "meta": it["meta"]})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def delete_by_session(self, session_id: str):
        self.items = [it for it in self.items if it.get("filter", {}).get("session_id") != session_id]


class EndeeStore:
    def __init__(self):
        self.local_fallback = LocalVectorStore()
        self.use_local = False
        token = os.environ.get("ENDEE_TOKEN", "")
        self.index_name = os.environ.get("ENDEE_INDEX_NAME", "skillbridge")
        self.dimension = 384
        try:
            from endee import Endee, Precision
            self.client = Endee(token)
            self._ensure_index()
            self.index = self.client.get_index(name=self.index_name)
        except Exception as e:
            logger.info("Endee cloud connection initialized with fallback (%s)", e)
            self.use_local = True

    def _ensure_index(self):
        from endee import Precision
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

    def upsert(self, items: List[Dict[str, Any]]):
        if self.use_local:
            return self.local_fallback.upsert(items)
        try:
            batch = []
            for it in items:
                batch.append({
                    "id": str(it["id"]),
                    "vector": it["vector"],
                    "meta": it.get("meta", {}),
                    "filter": it.get("filter", {}),
                })
            for i in range(0, len(batch), 1000):
                self.index.upsert(batch[i:i + 1000])
            return len(batch)
        except Exception as e:
            logger.warning("Endee upsert failed (%s), using local fallback", e)
            return self.local_fallback.upsert(items)

    def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filter: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        if self.use_local:
            return self.local_fallback.query(vector, top_k, filter)
        try:
            kwargs = {"vector": vector, "top_k": top_k, "include_vectors": False}
            if filter:
                kwargs["filter"] = filter
            results = self.index.query(**kwargs)
            return results or []
        except Exception as e:
            logger.warning("Endee query failed (%s), using local fallback", e)
            return self.local_fallback.query(vector, top_k, filter)

    def delete_by_session(self, session_id: str):
        self.local_fallback.delete_by_session(session_id)


_store: Optional[EndeeStore] = None


def get_store() -> EndeeStore:
    global _store
    if _store is None:
        _store = EndeeStore()
    return _store
