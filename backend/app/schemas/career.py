"""
Career Archetype Schemas
========================
Pydantic models for career archetypes listing, detail lookup, and skill gap analysis.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CareerArchetypeResponse(BaseModel):
    id: int
    name: str
    description: str
    num_jobs: int
    model_version: str

    class Config:
        from_attributes = True


class ArchetypeSkillResponse(BaseModel):
    skill_id: int
    canonical_name: str
    importance_score: float

    class Config:
        from_attributes = True


class CareerArchetypeDetailResponse(CareerArchetypeResponse):
    top_skills: List[ArchetypeSkillResponse] = []


class SkillGapRequest(BaseModel):
    current_skills: List[str] = Field(..., description="List of user's current skills")
    target_archetype_id: int = Field(..., description="ID of the target career archetype")


class MatchingSkillDetail(BaseModel):
    skill_id: int
    canonical_name: str
    importance_score: float


class GapSkillDetail(BaseModel):
    skill_id: int
    canonical_name: str
    importance_score: float
    closest_substitute: Optional[str] = None
    substitute_similarity: float = 0.0
    substitute_credit: float = 0.0


class SkillGapResponse(BaseModel):
    archetype_id: int
    archetype_name: str
    match_score: float = Field(..., description="Overall match score in [0.0, 1.0]")
    matching_skills: List[MatchingSkillDetail]
    missing_skills: List[GapSkillDetail]
    num_jobs_in_market: int
