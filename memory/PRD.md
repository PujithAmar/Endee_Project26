# SkillBridge - AI Placement Assistant (RAG)

## Original Problem Statement
Build an AI placement assistant that takes Resume + Job Description and uses a custom
RAG pipeline with a vector DB (Endee) + Gemini to produce: skill-gap analysis, match
score, resume suggestions, and tailored interview questions.

## User Personas
- **Students / Job seekers** preparing for placements who want personalised feedback
  on resume fit for a specific role
- **Bootcamp / course graduates** mapping a learning path to close gaps

## Architecture
```
Resume (PDF) + Job Description
       |
  pdfplumber parse
       |
  word-chunk (300 tokens, 60 overlap)
       |
  sentence-transformers/all-MiniLM-L6-v2  (local, 384-dim, normalized)
       |
  Endee Serverless vector index (HNSW + cosine, INT8)
       |
  Retrieve top-K (JD↔resume both directions)
       |
  Gemini 3 Flash Preview (fallback: 2.5-flash) — structured JSON
       |
  MongoDB persistence (analyses, chats)
```

### Tech Stack
- **Backend**: FastAPI, Motor (async Mongo), emergentintegrations (Gemini)
- **Frontend**: React + Tailwind + shadcn + sonner, Geist / Instrument Serif fonts
- **Embeddings**: sentence-transformers `all-MiniLM-L6-v2` (384-dim, local, free)
- **Vector DB**: Endee Serverless Cloud
- **LLM**: Gemini 3 Flash Preview (user-provided key) with 2.5-flash fallback
- **PDF**: pdfplumber
- **DB**: MongoDB

## Core Requirements (static)
1. Resume PDF upload OR raw text input
2. Job Description paste input
3. One-click Analyze producing: match_score, missing_skills, suggestions, interview_questions (tech + hr)
4. Grounded chat ("Ask anything about my profile") using session's indexed chunks
5. History of analyses with ability to reopen
6. Dark + minimal + professional UI, #0E1117 bg / #00ADB5 teal

## What's Been Implemented (Apr 22, 2026)
- `GET  /api/health` — mongo + endee + gemini probes
- `POST /api/analyze` — PDF upload OR form text field
- `POST /api/analyze-text` — JSON variant
- `POST /api/chat`, `GET /api/chat/{session_id}`
- `GET  /api/history`, `GET /api/history/{id}`, `DELETE /api/history/{id}`
- RAG pipeline (`rag_pipeline.py`): chunk → embed → upsert → retrieve → Gemini
- LLM fallback chain: `gemini-3-flash-preview` → `gemini-2.5-flash` with 503 retry
- Frontend pages: Analyzer, History, Chat; components: ResumeUpload (PDF dropzone + paste mode), JobDescriptionInput, ScoreRing (animated SVG), AnalysisResults (score, missing, strengths, suggestions, learning path, interview Qs with tabs)
- Toast system, responsive layout, animated entrance, grain + aurora background
- Tested: 10/10 backend tests passing (testing_agent_v3 iteration_1)

## Prioritized Backlog
### P0 — done ✅
- [x] Core RAG pipeline with Endee
- [x] PDF + text resume input
- [x] Match score, missing skills, suggestions, interview questions
- [x] Semantic chat grounded on session
- [x] History persistence
- [x] Dark theme UI matching spec

### P1 — next
- [ ] Pre-load MiniLM model on FastAPI startup (first request currently slow ~30s)
- [ ] Offload CPU-bound embed/upsert to run_in_executor (event-loop safety under load)
- [ ] Explicit 400 on empty resume_text/jd_text in `/api/analyze-text`
- [ ] ATS-style granular scoring (keyword density, formatting, section coverage)
- [ ] Full learning roadmap generator (week-by-week plan)

### P2 — later
- [ ] User accounts + OAuth
- [ ] Shareable public result pages (viral loop)
- [ ] Saved JD watchlist + batch analysis
- [ ] Export to PDF/Markdown
- [ ] Recruiter mode (reverse matching: JD → best resumes)
- [ ] Pagination for history

## Environment
- `/app/backend/.env` — MONGO_URL, DB_NAME, GEMINI_API_KEY, ENDEE_TOKEN, ENDEE_INDEX_NAME
- Endee index `skillbridge` (384-dim, cosine, INT8) is created on first run

## Known Limitations
- Sentence-transformers model downloads ~90MB on first request (one-time)
- Gemini 3 Flash Preview occasionally returns 503 under high demand — handled via fallback to 2.5-flash
