"""
Skill Schemas
=============
Pydantic models for skill extraction, similarity, and database serialization.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    id: int
    canonical_name: str
    category_id: Optional[int] = None
    aliases: Optional[List[str]] = []

    class Config:
        from_attributes = True


class SkillResponse(SkillBase):
    pass


class SimilarSkillResponse(BaseModel):
    skill_id: int
    canonical_name: str
    similarity_score: float = Field(..., description="Cosine similarity score")


class SynergySkillResponse(BaseModel):
    skill_id: int
    canonical_name: str
    cooccurrence_count: int
    support: float
    confidence: float = Field(..., description="Conditional probability P(B|A)")
    lift: float
    pmi: float


class SkillExtractRequest(BaseModel):
    text: str = Field(..., description="Raw job description or resume text")


class SkillExtractResponse(BaseModel):
    raw_text_length: int
    extracted_skills: List[str] = Field(..., description="List of unique normalized canonical skill names extracted")
