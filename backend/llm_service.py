from __future__ import annotations
import os
import json
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Active Groq Models (Updated for current API support)
MODEL_FALLBACKS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
    "groq/compound",
    "openai/gpt-oss-20b",
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


def _get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except ImportError:
        return None


def _call_groq(prompt: str, system_message: str, json_mode: bool = False) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is missing")

    client = _get_groq_client()
    last_err = None

    for model in MODEL_FALLBACKS:
        try:
            if client is not None:
                kwargs = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}

                completion = client.chat.completions.create(**kwargs)
                content = completion.choices[0].message.content
                if content:
                    return content
            else:
                import requests
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                }
                if json_mode:
                    payload["response_format"] = {"type": "json_object"}

                res = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=45,
                )
                res.raise_for_status()
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                if content:
                    return content
        except Exception as e:
            logger.warning(f"Groq model {model} failed: {e}")
            last_err = e

    raise last_err or RuntimeError("All Groq models failed")


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

    resp = _call_groq(prompt, SYSTEM_PROMPT, json_mode=True)
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

    resp = _call_groq(prompt, sys_msg, json_mode=False)
    return resp.strip()