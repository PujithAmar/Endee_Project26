from __future__ import annotations
import os
import json
import re
import logging
import uuid
from typing import Optional

from google import genai

client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

logger = logging.getLogger(__name__)

# Model fallback
MODEL_FALLBACKS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite"
]


SYSTEM_PROMPT = """You are SkillBridge, an expert AI placement assistant.
You analyse a candidate's resume against a job description using retrieved context
and produce a structured, honest, encouraging report.
Always return VALID JSON matching the schema requested. Never add prose outside JSON.
"""


def _strip_fences(text: str) -> str:
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)

    a = text.find("{")
    b = text.rfind("}")
    if a != -1 and b != -1 and b > a:
        return text[a:b + 1]

    return text


def _call_gemini(prompt: str, system_message: str) -> str:
    last_err = None

    for model in MODEL_FALLBACKS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=f"{system_message}\n\n{prompt}"
            )

            if response.text:
                return response.text

        except Exception as e:
            logger.warning(f"{model} failed: {e}")
            last_err = e

    raise last_err or RuntimeError("All Gemini models failed")


async def run_analysis(
    resume_text: str,
    jd_text: str,
    retrieved_context: str,
    session_id: Optional[str] = None,
) -> dict:

    prompt = f"""Analyse this candidate against the job description.

=== RESUME ===
{resume_text[:6000]}

=== JOB DESCRIPTION ===
{jd_text[:4000]}

=== CONTEXT ===
{retrieved_context[:4000]}

Return STRICT JSON:
{{
  "match_score": 0,
  "score_reason": "",
  "extracted_skills": [],
  "matched_skills": [],
  "missing_skills": [],
  "resume_strengths": [],
  "weak_areas": [],
  "suggestions": [],
  "learning_path": [],
  "interview_questions": {{
    "technical": [],
    "hr": []
  }},
  "fit_summary": ""
}}
"""

    resp = _call_gemini(prompt, SYSTEM_PROMPT)
    raw = _strip_fences(resp.strip())

    try:
        return json.loads(raw)
    except Exception as e:
        logger.error("JSON parse failed: %s\nRAW: %s", e, raw[:1000])
        return {
            "match_score": 0,
            "score_reason": "Parsing failed",
            "extracted_skills": [],
            "matched_skills": [],
            "missing_skills": [],
            "resume_strengths": [],
            "weak_areas": [],
            "suggestions": ["Retry analysis"],
            "learning_path": [],
            "interview_questions": {"technical": [], "hr": []},
            "fit_summary": "Error occurred",
        }


async def run_chat(
    question: str,
    retrieved_context: str,
    session_id: str,
) -> str:

    sys_msg = """You are SkillBridge assistant.
Answer ONLY from provided context. Be concise."""

    prompt = f"""
Context:
{retrieved_context[:6000]}

Question:
{question}
"""

    resp = _call_gemini(prompt, sys_msg)
    return resp.strip()