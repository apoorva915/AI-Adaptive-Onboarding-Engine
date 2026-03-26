from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.llm_service import extract_skills_with_llm
from backend.models import AnalyzeResponse, RequiredSkill, Skill
from backend.parser import load_input
from backend.skill_gap import compute_skill_gap

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI-Adaptive Onboarding Engine (MVP)")

cors_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _coerce_skills(raw: List[Dict[str, Any]], mode: str) -> List[Any]:
    """
    Convert LLM output dicts into typed Pydantic models (best-effort).
    Drops items that can't be validated.
    """
    coerced: List[Any] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue

        try:
            if mode == "resume":
                coerced.append(Skill(**item))
            else:
                coerced.append(RequiredSkill(**item))
        except Exception:
            continue
    return coerced


def _normalize_for_filter(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9+.# ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# These are broad categories often returned by the LLM that don't map cleanly to
# concrete skills/tools. Filter them to keep the MVP output actionable.
EXCLUDE_SKILL_TERMS = {
    "computer science",
    "computer science fundamentals",
    "information technology",
    "object-oriented programming",
    "object-oriented design",
    "frontend development",
    "back-end development",
    "software engineering",
    "web technologies",
}


def _should_exclude_skill(skill_name: str) -> bool:
    return _normalize_for_filter(skill_name) in EXCLUDE_SKILL_TERMS


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    resume_file: Optional[UploadFile] = File(None),
    jd_file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(None),
    jd_text: Optional[str] = Form(None),
):
    # 1) Load + clean inputs
    resume_input = load_input(resume_file, resume_text)
    jd_input = load_input(jd_file, jd_text)

    # 2) Extract candidate skills (resume) + required skills (JD)
    candidate_raw = extract_skills_with_llm(resume_input, mode="resume") if resume_input else []
    required_raw = extract_skills_with_llm(jd_input, mode="jd") if jd_input else []

    # 3) Coerce into typed models
    candidate_skills = _coerce_skills(candidate_raw, mode="resume")
    required_skills = _coerce_skills(required_raw, mode="jd")

    # 3b) Filter generic categories (LLM sometimes returns broad concepts)
    candidate_skills = [s for s in candidate_skills if not _should_exclude_skill(s.skill_name)]
    required_skills = [s for s in required_skills if not _should_exclude_skill(s.skill_name)]

    # 4) Compute gap
    gap = compute_skill_gap(candidate_skills=candidate_skills, required_skills=required_skills)

    return {
        "candidate_skills": [s.model_dump() for s in candidate_skills],
        "required_skills": [s.model_dump() for s in required_skills],
        "skill_gap": gap,
    }

