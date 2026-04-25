"""Orchestrates the full RAG pipeline: chunk → embed → store → retrieve → LLM."""
from __future__ import annotations
from typing import List, Tuple
import uuid

from embeddings import get_embedder
from vector_store import get_store
from pdf_parser import chunk_text
from llm_service import run_analysis, run_chat


def _ingest(session_id: str, resume_text: str, jd_text: str) -> Tuple[List[str], List[str]]:
    emb = get_embedder()
    store = get_store()

    resume_chunks = chunk_text(resume_text, chunk_size=300, overlap=60)
    jd_chunks = chunk_text(jd_text, chunk_size=300, overlap=60)

    items = []
    resume_ids, jd_ids = [], []

    if resume_chunks:
        vecs = emb.encode(resume_chunks)
        for i, (c, v) in enumerate(zip(resume_chunks, vecs)):
            cid = f"{session_id}_r_{i}"
            resume_ids.append(cid)
            items.append({
                "id": cid,
                "vector": v,
                "meta": {"session": session_id, "kind": "resume", "idx": i, "text": c[:1500]},
                "filter": {"session": session_id, "kind": "resume"},
            })

    if jd_chunks:
        vecs = emb.encode(jd_chunks)
        for i, (c, v) in enumerate(zip(jd_chunks, vecs)):
            cid = f"{session_id}_j_{i}"
            jd_ids.append(cid)
            items.append({
                "id": cid,
                "vector": v,
                "meta": {"session": session_id, "kind": "jd", "idx": i, "text": c[:1500]},
                "filter": {"session": session_id, "kind": "jd"},
            })

    store.upsert(items)
    return resume_ids, jd_ids


def _retrieve(session_id: str, query_text: str, top_k: int = 6, kind: str | None = None) -> List[dict]:
    emb = get_embedder()
    store = get_store()
    qv = emb.encode_one(query_text)
    flt = [{"session": {"$eq": session_id}}]
    if kind:
        flt.append({"kind": {"$eq": kind}})
    return store.query(qv, top_k=top_k, filter=flt)


def _context_from_hits(hits: List[dict]) -> str:
    parts = []
    for h in hits:
        meta = h.get("meta", {}) if isinstance(h, dict) else {}
        txt = meta.get("text") or ""
        kind = meta.get("kind", "")
        score = h.get("similarity") if isinstance(h, dict) else None
        if txt:
            parts.append(f"[{kind} | sim={score:.2f}]\n{txt}" if score is not None else f"[{kind}]\n{txt}")
    return "\n\n".join(parts)


async def analyze(resume_text: str, jd_text: str) -> dict:
    """Full end-to-end RAG analysis."""
    session_id = uuid.uuid4().hex[:16]

    # 1. Ingest both documents
    _ingest(session_id, resume_text, jd_text)

    # 2. Retrieve: top resume chunks most similar to the JD
    jd_hits = _retrieve(session_id, jd_text, top_k=6, kind="resume")
    # 3. Retrieve: top JD chunks most similar to the resume (for missing-skill discovery)
    resume_hits = _retrieve(session_id, resume_text, top_k=6, kind="jd")

    context = (
        "### Resume chunks most relevant to JD:\n"
        + _context_from_hits(jd_hits)
        + "\n\n### JD chunks most relevant to resume:\n"
        + _context_from_hits(resume_hits)
    )

    # 4. LLM analysis
    result = await run_analysis(resume_text, jd_text, context, session_id=session_id)
    result["session_id"] = session_id
    return result


async def chat_with_profile(session_id: str, question: str) -> str:
    """Semantic search across a prior session's chunks, then LLM answer."""
    hits = _retrieve(session_id, question, top_k=6)
    ctx = _context_from_hits(hits) or "(no relevant context found)"
    return await run_chat(question, ctx, session_id=f"chat-{session_id}")
