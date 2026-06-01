"""
Careers Router
==============
FastAPI router for querying career archetypes and performing skill gap analysis.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.career_archetype import CareerArchetype
from app.models.archetype_skill import ArchetypeSkill
from app.models.skill import Skill
from app.schemas.career import (
    CareerArchetypeResponse,
    CareerArchetypeDetailResponse,
    ArchetypeSkillResponse,
    SkillGapRequest,
    SkillGapResponse,
    MatchingSkillDetail,
    GapSkillDetail,
)
from app.services.gap_analyzer import GapAnalyzer

router = APIRouter()


@router.get("/archetypes", response_model=List[CareerArchetypeResponse])
def list_archetypes(db: Session = Depends(get_db)):
    """Lists all career archetypes discovered by clustering."""
    return db.query(CareerArchetype).all()


@router.get("/archetypes/{id}", response_model=CareerArchetypeDetailResponse)
def get_archetype_details(id: int, db: Session = Depends(get_db)):
    """Retrieves detailed information and key skill requirements for an archetype."""
    archetype = db.query(CareerArchetype).filter(CareerArchetype.id == id).first()
    if not archetype:
        raise HTTPException(status_code=404, detail=f"Career archetype with ID {id} not found")
        
    skills_map = {s.id: s.canonical_name for s in db.query(Skill).all()}
    arch_skills = (
        db.query(ArchetypeSkill)
        .filter(ArchetypeSkill.archetype_id == id)
        .order_by(ArchetypeSkill.importance_score.desc())
        .all()
    )
    
    top_skills = [
        ArchetypeSkillResponse(
            skill_id=askill.skill_id,
            canonical_name=skills_map.get(askill.skill_id, f"Skill {askill.skill_id}"),
            importance_score=askill.importance_score
        )
        for askill in arch_skills
    ]
    
    return CareerArchetypeDetailResponse(
        id=archetype.id,
        name=archetype.name,
        description=archetype.description,
        num_jobs=archetype.num_jobs,
        model_version=archetype.model_version,
        top_skills=top_skills
    )


@router.post("/gap", response_model=SkillGapResponse)
def analyze_skill_gaps(payload: SkillGapRequest, db: Session = Depends(get_db)):
    """Analyzes gaps between user's current skills and archetype requirements, including substitute credits."""
    try:
        analyzer = GapAnalyzer(db)
        gap_report = analyzer.analyze_gaps(
            user_skills=payload.current_skills,
            target_archetype_id=payload.target_archetype_id
        )
        
        # Format response to match Pydantic schema
        matching_skills = [
            MatchingSkillDetail(
                skill_id=m["skill_id"],
                canonical_name=m["canonical_name"],
                importance_score=m["importance_score"]
            )
            for m in gap_report["matching_skills"]
        ]
        
        missing_skills = [
            GapSkillDetail(
                skill_id=m["skill_id"],
                canonical_name=m["canonical_name"],
                importance_score=m["importance_score"],
                closest_substitute=m["closest_substitute"],
                substitute_similarity=m["substitute_similarity"],
                substitute_credit=m["substitute_credit"]
            )
            for m in gap_report["missing_skills"]
        ]
        
        return SkillGapResponse(
            archetype_id=gap_report["archetype_id"],
            archetype_name=gap_report["archetype_name"],
            match_score=gap_report["match_score"],
            matching_skills=matching_skills,
            missing_skills=missing_skills,
            num_jobs_in_market=gap_report["num_jobs_in_market"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")
