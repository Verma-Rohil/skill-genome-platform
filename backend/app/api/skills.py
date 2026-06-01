"""
Skills Router
=============
FastAPI router for querying, searching, extracting, and calculating synergies of skills.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.skill import Skill
from app.models.skill_cooccurrence import SkillCooccurrence
from app.schemas.skill import (
    SkillResponse,
    SimilarSkillResponse,
    SynergySkillResponse,
    SkillExtractRequest,
    SkillExtractResponse,
)
from app.services.similarity_engine import SimilarityEngine
from app.services.skill_extractor import SkillExtractor

router = APIRouter()


@router.get("", response_model=List[SkillResponse])
def list_skills(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lists canonical skills with pagination and optional search term filtering."""
    query = db.query(Skill)
    if search:
        query = query.filter(Skill.canonical_name.ilike(f"%{search}%"))
    skills = query.offset(skip).limit(limit).all()
    return skills


@router.get("/{id}", response_model=SkillResponse)
def get_skill_details(id: int, db: Session = Depends(get_db)):
    """Retrieves detailed information for a specific skill by ID."""
    skill = db.query(Skill).filter(Skill.id == id).first()
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill with ID {id} not found")
    return skill


@router.get("/{id}/similar", response_model=List[SimilarSkillResponse])
def get_similar_skills(id: int, top_n: int = 10, db: Session = Depends(get_db)):
    """Finds semantic peer skills using the S-BERT SimilarityEngine."""
    skill = db.query(Skill).filter(Skill.id == id).first()
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill with ID {id} not found")
    
    similarity_engine = SimilarityEngine(db)
    similar = similarity_engine.find_similar_skills(id, top_n=top_n)
    
    return [
        SimilarSkillResponse(
            skill_id=s_id,
            canonical_name=name,
            similarity_score=score
        )
        for s_id, name, score in similar
    ]


@router.get("/{id}/synergy", response_model=List[SynergySkillResponse])
def get_synergy_skills(id: int, db: Session = Depends(get_db)):
    """Retrieves high-synergy skills frequently co-occurring in the job market."""
    skill = db.query(Skill).filter(Skill.id == id).first()
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill with ID {id} not found")
    
    skills_map = {s.id: s.canonical_name for s in db.query(Skill).all()}
    
    cooccurrences = db.query(SkillCooccurrence).filter(
        (SkillCooccurrence.skill_a_id == id) | (SkillCooccurrence.skill_b_id == id)
    ).order_by(SkillCooccurrence.lift.desc()).all()
    
    results = []
    for co in cooccurrences:
        if co.skill_a_id == id:
            target_id = co.skill_b_id
            confidence = co.confidence_a_b
        else:
            target_id = co.skill_a_id
            confidence = co.confidence_b_a
            
        canonical_name = skills_map.get(target_id, f"Skill {target_id}")
        results.append(
            SynergySkillResponse(
                skill_id=target_id,
                canonical_name=canonical_name,
                cooccurrence_count=co.cooccurrence_count,
                support=co.support,
                confidence=confidence,
                lift=co.lift,
                pmi=co.pmi
            )
        )
    return results


@router.post("/extract", response_model=SkillExtractResponse)
def extract_skills_from_text(payload: SkillExtractRequest, db: Session = Depends(get_db)):
    """Extracts and normalizes all taxonomy skills found within a job description text."""
    extractor = SkillExtractor(db)
    extracted = extractor.extract(payload.text)
    return SkillExtractResponse(
        raw_text_length=len(payload.text),
        extracted_skills=extracted
    )
