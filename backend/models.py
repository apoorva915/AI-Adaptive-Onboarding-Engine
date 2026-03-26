from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict


class Skill(BaseModel):
    model_config = ConfigDict(extra="ignore")
    skill_name: str


class RequiredSkill(BaseModel):
    model_config = ConfigDict(extra="ignore")
    skill_name: str


class SkillList(BaseModel):
    skills: List[Skill]


class RequiredSkillList(BaseModel):
    skills: List[RequiredSkill]


class AnalyzeResponse(BaseModel):
    candidate_skills: List[Skill] = []
    required_skills: List[RequiredSkill] = []
    skill_gap: dict = {}

