"""
Skill Gap Analyzer Service
==========================
Analyzes the discrepancy between a user's current skills and a target career archetype's requirements.

WHY THIS SERVICE:
- Provides a personalized career roadmap for users.
- Ranks gaps mathematically by their importance in the target archetype.
- Incorporates semantic similarity (e.g. if the user knows PyTorch and the archetype requires TensorFlow,
  it recognizes the low barrier to entry rather than treating it as a total gap).
"""

from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.career_archetype import CareerArchetype
from app.models.archetype_skill import ArchetypeSkill
from app.models.skill import Skill
from app.services.similarity_engine import SimilarityEngine


class GapAnalyzer:
    def __init__(self, db: Session):
        self.db = db
        self.similarity_engine = SimilarityEngine(db)

    def analyze_gaps(self, user_skills: List[str], target_archetype_id: int) -> Dict[str, Any]:
        """
        Compares a user's skills against a target career archetype.
        Calculates match score, matching skills, and missing skills with overlap mapping.
        """
        # 1. Fetch target archetype
        archetype = self.db.query(CareerArchetype).filter_by(id=target_archetype_id).first()
        if not archetype:
            raise ValueError(f"Career archetype with ID {target_archetype_id} not found.")

        # 2. Fetch all skills required for the archetype
        arch_skills = (
            self.db.query(ArchetypeSkill)
            .filter_by(archetype_id=target_archetype_id)
            .order_by(ArchetypeSkill.importance_score.desc())
            .all()
        )
        
        # 3. Resolve user skills to canonical names
        user_canonical_skills = set()
        for us in user_skills:
            # Match using similarity engine string search
            matches = self.similarity_engine.find_similar_skills(us, top_n=1)
            # If we find an exact or very high similarity match, resolve to canonical
            if matches and matches[0][2] >= 0.90:
                user_canonical_skills.add(matches[0][1])
            else:
                user_canonical_skills.add(us.strip())

        matching_skills = []
        missing_skills = []
        
        total_importance = sum(as_.importance_score for as_ in arch_skills)
        earned_importance = 0.0

        for as_ in arch_skills:
            skill = self.db.query(Skill).filter_by(id=as_.skill_id).first()
            if not skill:
                continue

            canon_name = skill.canonical_name
            importance = as_.importance_score

            if canon_name in user_canonical_skills:
                matching_skills.append({
                    "skill_id": skill.id,
                    "canonical_name": canon_name,
                    "importance_score": importance
                })
                earned_importance += importance
            else:
                # Find closest user skill using similarity engine
                closest_user_skill = None
                highest_sim = 0.0
                
                # Check similarity of the missing skill against all user skills
                for us in user_canonical_skills:
                    # Retrieve similarity score between missing skill and user skill
                    sims = self.similarity_engine.find_similar_skills(canon_name, top_n=10)
                    for s_id, s_name, score in sims:
                        if s_name == us:
                            if score > highest_sim:
                                highest_sim = score
                                closest_user_skill = us
                            break
                            
                # If there's a strong semantic substitute (similarity >= 0.65)
                # count it partially towards the match score
                substitute_credit = 0.0
                if highest_sim >= 0.65:
                    substitute_credit = importance * (highest_sim ** 2)  # Quadratic penalty for gap distance
                    earned_importance += substitute_credit

                missing_skills.append({
                    "skill_id": skill.id,
                    "canonical_name": canon_name,
                    "importance_score": importance,
                    "closest_substitute": closest_user_skill,
                    "substitute_similarity": float(highest_sim),
                    "substitute_credit": float(substitute_credit)
                })

        # Calculate final match score in [0.0, 1.0]
        match_score = earned_importance / total_importance if total_importance > 0 else 0.0

        return {
            "archetype_id": target_archetype_id,
            "archetype_name": archetype.name,
            "match_score": float(match_score),
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "num_jobs_in_market": archetype.num_jobs
        }
