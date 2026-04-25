"""SkillBridge backend pytest suite.

Covers the core RAG flow:
- /api/health
- /api/analyze-text  (JSON path)
- /api/analyze       (multipart with PDF + validation)
- /api/history (list, detail, delete)
- /api/chat (with session_id) + /api/chat/{session_id}
- Cross-session isolation (Endee vector filter by session)
"""
from __future__ import annotations
import io
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")  # picked from container env (frontend .env mirrored)
API = f"{BASE_URL}/api"

# Generous timeout: first analyze call downloads MiniLM (~90MB) + Gemini + Endee roundtrip
LONG_TIMEOUT = 180
SHORT_TIMEOUT = 30


SAMPLE_RESUME_A = """John Doe
Senior Backend Engineer

Skills: Python, FastAPI, MongoDB, Docker, AWS, REST APIs, PostgreSQL
Experience:
- 5 years building scalable backend services in Python and FastAPI
- Led migration from monolith to microservices on AWS ECS
- Designed MongoDB schemas and ran production clusters
Education: B.Tech Computer Science, IIT Delhi
"""

SAMPLE_JD_A = """Senior Backend Engineer — FinTech

We are hiring a senior backend engineer experienced in Python, FastAPI, Kubernetes, Kafka,
and distributed systems. Strong knowledge of PostgreSQL, Redis, and event-driven
architectures is required. Experience with GCP is a plus.
"""

SAMPLE_RESUME_B = """Jane Smith
Frontend React Developer

Skills: React, TypeScript, TailwindCSS, Next.js, Jest
Experience: 3 years building SPA dashboards.
"""

SAMPLE_JD_B = """Frontend Engineer
React, Next.js, TailwindCSS required. GraphQL nice to have.
"""


# ----------------------------- fixtures -----------------------------
@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    s.headers.update({"Accept": "application/json"})
    return s


@pytest.fixture(scope="session")
def analysis_a(client):
    """Run a real analysis once and reuse across tests (slow first call)."""
    r = client.post(
        f"{API}/analyze-text",
        json={"resume_text": SAMPLE_RESUME_A, "jd_text": SAMPLE_JD_A},
        timeout=LONG_TIMEOUT,
    )
    assert r.status_code == 200, f"analyze-text failed: {r.status_code} {r.text[:500]}"
    return r.json()


@pytest.fixture(scope="session")
def analysis_b(client, analysis_a):
    r = client.post(
        f"{API}/analyze-text",
        json={"resume_text": SAMPLE_RESUME_B, "jd_text": SAMPLE_JD_B},
        timeout=LONG_TIMEOUT,
    )
    assert r.status_code == 200, f"analyze-text B failed: {r.status_code} {r.text[:500]}"
    return r.json()


# --------------------- /api/health ---------------------
class TestHealth:
    def test_health_all_true(self, client):
        r = client.get(f"{API}/health", timeout=SHORT_TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert data.get("mongo") is True, data
        assert data.get("endee") is True, data
        assert data.get("gemini_key") is True, data


# --------------------- /api/analyze-text ---------------------
class TestAnalyzeText:
    def test_schema(self, analysis_a):
        d = analysis_a
        # core ids
        assert isinstance(d.get("id"), str) and d["id"]
        assert isinstance(d.get("session_id"), str) and d["session_id"]
        assert isinstance(d.get("created_at"), str)
        # match_score 0-100 int
        ms = d.get("match_score")
        assert isinstance(ms, int), f"match_score not int: {type(ms)} -> {ms}"
        assert 0 <= ms <= 100
        # arrays
        assert isinstance(d.get("missing_skills"), list)
        assert isinstance(d.get("suggestions"), list)
        # interview_questions
        iq = d.get("interview_questions")
        assert isinstance(iq, dict)
        assert isinstance(iq.get("technical"), list)
        assert isinstance(iq.get("hr"), list)
        # extra fields
        assert isinstance(d.get("fit_summary"), str)
        assert isinstance(d.get("extracted_skills"), (list, dict))
        assert isinstance(d.get("resume_strengths"), list)
        assert isinstance(d.get("learning_path"), list)

    def test_persisted_in_mongo(self, client, analysis_a):
        # Should appear in /history
        r = client.get(f"{API}/history", timeout=SHORT_TIMEOUT)
        assert r.status_code == 200
        ids = [it["id"] for it in r.json()]
        assert analysis_a["id"] in ids


# --------------------- /api/analyze (multipart) ---------------------
def _make_pdf_bytes(text: str) -> bytes:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 750
    for line in text.splitlines():
        c.drawString(72, y, line[:90])
        y -= 14
        if y < 72:
            c.showPage()
            y = 750
    c.showPage()
    c.save()
    return buf.getvalue()


class TestAnalyzePDF:
    def test_pdf_upload_returns_full_schema(self, client):
        pdf = _make_pdf_bytes(SAMPLE_RESUME_A)
        files = {"resume": ("resume.pdf", pdf, "application/pdf")}
        data = {"jd_text": SAMPLE_JD_A}
        r = client.post(f"{API}/analyze", files=files, data=data, timeout=LONG_TIMEOUT)
        assert r.status_code == 200, f"{r.status_code} {r.text[:400]}"
        d = r.json()
        assert isinstance(d.get("match_score"), int)
        assert 0 <= d["match_score"] <= 100
        assert isinstance(d.get("missing_skills"), list)
        assert isinstance(d.get("suggestions"), list)
        iq = d.get("interview_questions") or {}
        assert isinstance(iq.get("technical"), list)
        assert isinstance(iq.get("hr"), list)
        assert d.get("session_id")
        assert d.get("id")

    def test_missing_resume_and_text_returns_400(self, client):
        r = client.post(
            f"{API}/analyze",
            data={"jd_text": SAMPLE_JD_A},
            timeout=SHORT_TIMEOUT,
        )
        assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text[:200]}"


# --------------------- /api/history ---------------------
class TestHistory:
    def test_list_schema(self, client, analysis_a):
        r = client.get(f"{API}/history", timeout=SHORT_TIMEOUT)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list) and len(items) >= 1
        it = next((x for x in items if x["id"] == analysis_a["id"]), None)
        assert it is not None
        for k in ("id", "session_id", "match_score", "candidate_title", "jd_title", "created_at"):
            assert k in it, f"missing key {k} in {it}"
        assert isinstance(it["match_score"], int)

    def test_history_detail(self, client, analysis_a):
        r = client.get(f"{API}/history/{analysis_a['id']}", timeout=SHORT_TIMEOUT)
        assert r.status_code == 200
        doc = r.json()
        assert doc["id"] == analysis_a["id"]
        assert doc["session_id"] == analysis_a["session_id"]
        assert "result" in doc
        assert "_id" not in doc  # mongo objectId must be excluded

    def test_history_delete(self, client):
        # create a throwaway record
        r = client.post(
            f"{API}/analyze-text",
            json={"resume_text": "TEST_DELETE skills python", "jd_text": "Python developer"},
            timeout=LONG_TIMEOUT,
        )
        assert r.status_code == 200
        rid = r.json()["id"]
        d = client.delete(f"{API}/history/{rid}", timeout=SHORT_TIMEOUT)
        assert d.status_code == 200
        assert d.json().get("deleted") == 1
        # confirm gone
        g = client.get(f"{API}/history/{rid}", timeout=SHORT_TIMEOUT)
        assert g.status_code == 404


# --------------------- /api/chat ---------------------
class TestChat:
    def test_chat_returns_answer_and_persists(self, client, analysis_a):
        sid = analysis_a["session_id"]
        q = "What are the candidate's strongest backend skills?"
        r = client.post(
            f"{API}/chat",
            json={"session_id": sid, "question": q},
            timeout=LONG_TIMEOUT,
        )
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d.get("session_id") == sid
        assert isinstance(d.get("answer"), str) and len(d["answer"]) > 0

        # persisted
        h = client.get(f"{API}/chat/{sid}", timeout=SHORT_TIMEOUT)
        assert h.status_code == 200
        msgs = h.json()
        assert isinstance(msgs, list) and len(msgs) >= 1
        assert any(m.get("question") == q for m in msgs)

    def test_session_isolation(self, client, analysis_a, analysis_b):
        """Different sessions should yield different chat history & retrieval context."""
        sid_a = analysis_a["session_id"]
        sid_b = analysis_b["session_id"]
        assert sid_a != sid_b

        # ask a question scoped to B
        q = "Which frontend frameworks does the candidate know?"
        rb = client.post(f"{API}/chat", json={"session_id": sid_b, "question": q}, timeout=LONG_TIMEOUT)
        assert rb.status_code == 200

        # chat history endpoints are partitioned
        ha = client.get(f"{API}/chat/{sid_a}", timeout=SHORT_TIMEOUT).json()
        hb = client.get(f"{API}/chat/{sid_b}", timeout=SHORT_TIMEOUT).json()
        sids_a = {m["session_id"] for m in ha}
        sids_b = {m["session_id"] for m in hb}
        assert sids_a == {sid_a}
        assert sids_b == {sid_b}
