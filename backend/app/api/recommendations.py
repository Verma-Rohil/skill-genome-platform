"""
Recommendations Router
======================
FastAPI router for generating multi-signal skill recommendations based on current user profile.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem,
    RecommendationSignal,
)
from app.services.recommender import Recommender

router = APIRouter()


@router.post("", response_model=RecommendationResponse)
def get_recommendations(payload: RecommendationRequest, db: Session = Depends(get_db)):
    """Generates a ranked list of recommended skills combining archetype relevance, synergy, and similarity."""
    try:
        recommender = Recommender(db)
        recommendations = recommender.recommend_skills(
            user_skills=payload.current_skills,
            target_archetype_id=payload.target_archetype_id,
            top_k=payload.top_k
        )
        
        items = [
            RecommendationItem(
                skill_id=rec["skill_id"],
                canonical_name=rec["canonical_name"],
                score=rec["score"],
                reasons=rec["reasons"],
                signals=RecommendationSignal(
                    relevance=rec["signals"]["relevance"],
                    synergy=rec["signals"]["synergy"],
                    similarity=rec["signals"]["similarity"]
                )
            )
            for rec in recommendations
        ]
        
        return RecommendationResponse(recommendations=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")
