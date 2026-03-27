from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from .models import RequiredSkill, Skill


def normalize_skill_name(name: str) -> str:
    return (name or "").lower().strip()


def _normalize_for_matching(s: str) -> str:
    s = normalize_skill_name(s)
    # Keep alphanumerics, plus dots and hashes; collapse everything else to spaces.
    s = re.sub(r"[^a-z0-9.+# ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _candidate_tokens(candidates: List[Skill]) -> Set[str]:
    tokens: Set[str] = set()
    for c in candidates:
        tokens.add(_normalize_for_matching(c.skill_name))
    return tokens


def _matches_required(req: str, candidate_names: Set[str]) -> bool:
    req_n = _normalize_for_matching(req)
    if not req_n:
        return False

    # 1) Exact normalized match
    if req_n in candidate_names:
        return True

    # 2) Substring match (SQL vs PostgreSQL, etc.)
    for cand in candidate_names:
        if req_n in cand or cand in req_n:
            return True

    # 3) Common alias mapping for MVP robustness
    aliases: Dict[str, List[str]] = {
        # Databases
        "sql": ["postgresql", "mysql", "mariadb", "mssql", "oracle", "sql"],
        "relational databases": ["postgresql", "mysql", "mariadb", "mssql", "oracle"],
        # JavaScript ecosystems
        "javascript frameworks": ["react", "next.js", "nextjs", "angular", "vue", "nuxt", "svelte"],
        "front-end development": ["react", "next.js", "nextjs", "tailwind", "css", "html", "javascript", "typescript"],
        "back-end development": ["node.js", "express", "spring", "spring boot", "graphql", "rest api", "aws lambda"],
        "web technologies": ["html", "css", "javascript", "typescript", "react", "next.js", "tailwind"],
        # Tooling/practices often expressed as phrases
        "automated testing": ["jest", "pytest", "unit test", "cypress", "selenium"],
        "code reviews": ["github", "git", "pull request", "pr"],
        "object-oriented programming": ["oop", "java", "c++", "c#", "typescript"],
        "object-oriented design": ["ood", "design patterns"],
        "data structures": ["algorithms", "data structure", "trees", "graphs"],
    }

    for key, patterns in aliases.items():
        if req_n == _normalize_for_matching(key):
            return any(p in cand for cand in candidate_names for p in patterns)

    return False


def compute_skill_gap(candidate_skills: List[Skill], required_skills: List[RequiredSkill]) -> Dict[str, Any]:
    """
    Returns:
      {
        "missing_skills": [...],
        "matched_skills": [...]
      }
    """
    candidate_names = _candidate_tokens(candidate_skills)

    missing_skills: List[str] = []
    matched_skills: List[str] = []

    for req in required_skills:
        if _matches_required(req.skill_name, candidate_names):
            matched_skills.append(req.skill_name)
        else:
            missing_skills.append(req.skill_name)

    return {
        "missing_skills": missing_skills,
        "matched_skills": matched_skills,
    }

