"""SkillBridge API — FastAPI backend for AI Placement Assistant (RAG + Endee + Gemini)."""
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

# --- Mongo ---
mongo_url = os.environ["MONGO_URL"]
mongo_client = AsyncIOMotorClient(mongo_url)
db = mongo_client[os.environ["DB_NAME"]]

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
    checks = {"mongo": False, "endee": False, "gemini_key": bool(os.environ.get("GEMINI_API_KEY"))}
    try:
        await mongo_client.admin.command("ping")
        checks["mongo"] = True
    except Exception as e:
        logger.warning("mongo ping: %s", e)
    try:
        from vector_store import get_store
        _ = get_store()
        checks["endee"] = True
    except Exception as e:
        logger.warning("endee check: %s", e)
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


@app.on_event("shutdown")
async def _shutdown():
    mongo_client.close()
