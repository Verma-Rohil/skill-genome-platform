"""
Recommendation Schemas
======================
Pydantic models for personalized skill recommendations.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    current_skills: List[str] = Field(..., description="List of user's current skills")
    target_archetype_id: Optional[int] = Field(None, description="Optional ID of target career archetype to prioritize gaps")
    top_k: int = Field(10, description="Number of recommendations to return")


class RecommendationSignal(BaseModel):
    relevance: float = Field(..., description="Archetype gap relevance score")
    synergy: float = Field(..., description="Co-occurrence synergy score")
    similarity: float = Field(..., description="Semantic cosine similarity score")


class RecommendationItem(BaseModel):
    skill_id: int
    canonical_name: str
    score: float = Field(..., description="Aggregated recommendation score")
    reasons: List[str] = Field(..., description="Semantic justifications for recommendations")
    signals: RecommendationSignal


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
