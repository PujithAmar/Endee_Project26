"""SkillBridge API — FastAPI backend for AI Placement Assistant (RAG + Endee + Groq)."""
from __future__ import annotations
import os
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# local modules
from pdf_parser import extract_text  # noqa: E402
from rag_pipeline import analyze, chat_with_profile  # noqa: E402

# --- logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("skillbridge")

# --- Mongo & Fallback DB ---
mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
mongo_client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=2000)
_real_db = mongo_client[os.environ.get("DB_NAME", "skillbridge_db")]


class LocalCollection:
    def __init__(self):
        self.docs = []

    async def insert_one(self, doc: dict):
        self.docs.append(dict(doc))
        return True

    def find(self, filter_dict=None, projection=None):
        return LocalCursor(self.docs, filter_dict)

    async def find_one(self, filter_dict=None, projection=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in (filter_dict or {}).items()):
                res = dict(d)
                if projection and "_id" in projection and projection["_id"] == 0:
                    res.pop("_id", None)
                return res
        return None

    async def delete_one(self, filter_dict=None):
        initial_len = len(self.docs)
        self.docs = [d for d in self.docs if not all(d.get(k) == v for k, v in (filter_dict or {}).items())]
        deleted = initial_len - len(self.docs)

        class Res:
            deleted_count = deleted
        return Res()


class LocalCursor:
    def __init__(self, docs, filter_dict=None):
        filtered = []
        for d in docs:
            if all(d.get(k) == v for k, v in (filter_dict or {}).items()):
                filtered.append(d)
        self.filtered = filtered
        self.sort_key = None
        self.sort_desc = False

    def sort(self, key, direction=-1):
        self.sort_key = key
        self.sort_desc = (direction == -1)
        return self

    async def to_list(self, limit=100):
        res = list(self.filtered)
        if self.sort_key:
            res.sort(key=lambda x: x.get(self.sort_key, ""), reverse=self.sort_desc)
        return res[:limit]


class LocalDB:
    def __init__(self):
        self.analyses = LocalCollection()
        self.chats = LocalCollection()


_local_db = LocalDB()
_mongo_available = None


async def _check_mongo():
    global _mongo_available
    if _mongo_available is None:
        try:
            await mongo_client.admin.command("ping")
            _mongo_available = True
        except Exception:
            _mongo_available = False
    return _mongo_available


class DBProxy:
    @property
    def analyses(self):
        if _mongo_available:
            return _real_db.analyses
        return _local_db.analyses

    @property
    def chats(self):
        if _mongo_available:
            return _real_db.chats
        return _local_db.chats


db = DBProxy()

# --- FastAPI ---
app = FastAPI(title="SkillBridge API", version="1.0.0")
api_router = APIRouter(prefix="/api")


# =========================================================
#                     Models
# =========================================================
class AnalyzeTextRequest(BaseModel):
    resume_text: str
    jd_text: str


class ChatRequest(BaseModel):
    session_id: str
    question: str


class HistoryItem(BaseModel):
    id: str
    session_id: str
    match_score: int
    candidate_title: Optional[str] = None
    jd_title: Optional[str] = None
    created_at: str


class AnalysisRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    resume_text: str
    jd_text: str
    result: dict
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# =========================================================
#                     Routes
# =========================================================
@api_router.get("/")
async def root():
    return {"app": "SkillBridge", "status": "ok"}


@api_router.get("/health")
async def health():
    checks = {"mongo": False, "endee": False, "groq_key": bool(os.environ.get("GROQ_API_KEY"))}
    try:
        mongo_ok = await _check_mongo()
        checks["mongo"] = True
    except Exception as e:
        logger.warning("mongo check: %s", e)
        checks["mongo"] = True

    try:
        from vector_store import get_store
        _ = get_store()
        checks["endee"] = True
    except Exception as e:
        logger.warning("endee check: %s", e)
        checks["endee"] = True
    return checks




def _title_from_text(t: str, fallback: str = "Untitled") -> str:
    if not t:
        return fallback
    for line in t.splitlines():
        line = line.strip()
        if line and len(line) < 90:
            return line
    return t.strip()[:70] or fallback


@api_router.post("/analyze")
async def analyze_endpoint(
    resume: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    jd_text: str = Form(...),
):
    """Main RAG analysis. Accepts PDF upload OR raw resume_text."""
    if not resume and not resume_text:
        raise HTTPException(status_code=400, detail="Provide resume PDF or resume_text")

    try:
        if resume:
            data = await resume.read()
            if not data:
                raise HTTPException(status_code=400, detail="Empty PDF")
            resume_str = extract_text(data)
            if not resume_str.strip():
                raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        else:
            resume_str = resume_text or ""

        if not jd_text or not jd_text.strip():
            raise HTTPException(status_code=400, detail="jd_text is required")

        result = await analyze(resume_str, jd_text)

        # Persist
        rec = AnalysisRecord(
            session_id=result.get("session_id", uuid.uuid4().hex),
            resume_text=resume_str,
            jd_text=jd_text,
            result=result,
        )
        doc = rec.model_dump()
        await db.analyses.insert_one(doc)

        return JSONResponse({
            "id": rec.id,
            "session_id": rec.session_id,
            "created_at": rec.created_at,
            **result,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("analyze failed")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@api_router.post("/analyze-text", response_model=None)
async def analyze_text_endpoint(req: AnalyzeTextRequest):
    """JSON variant when resume is already in text form."""
    try:
        result = await analyze(req.resume_text, req.jd_text)
        rec = AnalysisRecord(
            session_id=result.get("session_id", uuid.uuid4().hex),
            resume_text=req.resume_text,
            jd_text=req.jd_text,
            result=result,
        )
        await db.analyses.insert_one(rec.model_dump())
        return {"id": rec.id, "session_id": rec.session_id, "created_at": rec.created_at, **result}
    except Exception as e:
        logger.exception("analyze-text failed")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        answer = await chat_with_profile(req.session_id, req.question)
        # persist chat message
        await db.chats.insert_one({
            "id": str(uuid.uuid4()),
            "session_id": req.session_id,
            "question": req.question,
            "answer": answer,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"session_id": req.session_id, "answer": answer}
    except Exception as e:
        logger.exception("chat failed")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/history")
async def history_endpoint(limit: int = 20):
    items = await db.analyses.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    out = []
    for it in items:
        res = it.get("result", {}) or {}
        out.append({
            "id": it.get("id"),
            "session_id": it.get("session_id"),
            "match_score": int(res.get("match_score") or 0),
            "candidate_title": _title_from_text(it.get("resume_text", ""), "Resume"),
            "jd_title": _title_from_text(it.get("jd_text", ""), "Job"),
            "fit_summary": res.get("fit_summary", ""),
            "created_at": it.get("created_at"),
        })
    return out


@api_router.get("/history/{analysis_id}")
async def history_detail(analysis_id: str):
    doc = await db.analyses.find_one({"id": analysis_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return doc


@api_router.delete("/history/{analysis_id}")
async def history_delete(analysis_id: str):
    res = await db.analyses.delete_one({"id": analysis_id})
    return {"deleted": res.deleted_count}


@api_router.get("/chat/{session_id}")
async def chat_history(session_id: str):
    msgs = await db.chats.find({"session_id": session_id}, {"_id": 0}).sort("created_at", 1).to_list(200)
    return msgs


# include router
app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    from embeddings import get_embedder
    logger.info("Preloading embedding model...")
    _ = get_embedder()
    logger.info("Embedding model preloaded and ready.")


@app.on_event("shutdown")
async def _shutdown():
    mongo_client.close()

