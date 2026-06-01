"""
Generates personalized skill recommendations for a user based on their current skills
and target career archetype.
"""

from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.skill import Skill
from app.models.skill_cooccurrence import SkillCooccurrence
from app.models.archetype_skill import ArchetypeSkill
from app.services.similarity_engine import SimilarityEngine
from app.services.gap_analyzer import GapAnalyzer


class Recommender:
    def __init__(self, db: Session):
        self.db = db
        self.similarity_engine = SimilarityEngine(db)
        self.gap_analyzer = GapAnalyzer(db)

    def recommend_skills(
        self, 
        user_skills: List[str], 
        target_archetype_id: Optional[int] = None, 
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Calculates multi-signal recommendations for a user.
        Signals: Archetype Relevance (weight 0.5), Synergy (weight 0.3), Proximity (weight 0.2).
        """
        # Resolve user skills to canonical names
        user_canonical = set()
        user_ids = set()
        
        skills_list = self.db.query(Skill).all()
        id_to_name = {s.id: s.canonical_name for s in skills_list}
        name_to_id = {s.canonical_name.lower(): s.id for s in skills_list}

        for us in user_skills:
            matches = self.similarity_engine.find_similar_skills(us, top_n=1)
            if matches and matches[0][2] >= 0.90:
                user_canonical.add(matches[0][1])
                user_ids.add(matches[0][0])
            else:
                us_clean = us.strip().lower()
                if us_clean in name_to_id:
                    user_ids.add(name_to_id[us_clean])
                    user_canonical.add(id_to_name[name_to_id[us_clean]])
                else:
                    user_canonical.add(us.strip())

        # Candidate pool
        candidates = {}  # skill_id -> {relevance: 0.0, synergy: 0.0, similarity: 0.0, reasons: []}

        # 1. Target Archetype Relevance (if target_archetype_id provided)
        if target_archetype_id is not None:
            try:
                gaps = self.gap_analyzer.analyze_gaps(user_skills, target_archetype_id)
                # Map missing skills to candidate pool
                for gap in gaps["missing_skills"]:
                    s_id = gap["skill_id"]
                    if s_id not in user_ids:
                        candidates[s_id] = {
                            "relevance": gap["importance_score"],
                            "synergy": 0.0,
                            "similarity": 0.0,
                            "reasons": ["Required for target career archetype"]
                        }
            except Exception as e:
                print(f"[Recommender] Error loading target archetype gaps: {e}")

        # Load all co-occurrences for synergy calculation
        # To avoid loading everything, we only load pairs containing the user's current skills
        if user_ids:
            cooccurrences = (
                self.db.query(SkillCooccurrence)
                .filter(
                    (SkillCooccurrence.skill_a_id.in_(user_ids)) | 
                    (SkillCooccurrence.skill_b_id.in_(user_ids))
                )
                .all()
            )

            for co in cooccurrences:
                # Determine which skill is the neighbor
                if co.skill_a_id in user_ids:
                    user_s = co.skill_a_id
                    neighbor_s = co.skill_b_id
                    # P(neighbor | user) is confidence_a_b
                    confidence = co.confidence_a_b
                else:
                    user_s = co.skill_b_id
                    neighbor_s = co.skill_a_id
                    # P(neighbor | user) is confidence_b_a
                    confidence = co.confidence_b_a

                if neighbor_s in user_ids:
                    continue

                if neighbor_s not in candidates:
                    candidates[neighbor_s] = {"relevance": 0.0, "synergy": 0.0, "similarity": 0.0, "reasons": []}
                
                # Update synergy score (accumulate confidence transition probabilities)
                candidates[neighbor_s]["synergy"] = max(candidates[neighbor_s]["synergy"], confidence)
                
                # Add reason
                user_skill_name = id_to_name.get(user_s, "current skill")
                if len(candidates[neighbor_s]["reasons"]) < 3:
                    candidates[neighbor_s]["reasons"].append(f"Frequently paired with {user_skill_name}")

        # 3. Semantic Proximity
        # Find nearest neighbors in embedding space for each of the user's current skills
        for u_id in user_ids:
            sims = self.similarity_engine.find_similar_skills(u_id, top_n=5)
            for s_id, s_name, score in sims:
                if s_id in user_ids:
                    continue
                if s_id not in candidates:
                    candidates[s_id] = {"relevance": 0.0, "synergy": 0.0, "similarity": 0.0, "reasons": []}
                
                # Update similarity score
                candidates[s_id]["similarity"] = max(candidates[s_id]["similarity"], score)
                
                # Add reason
                user_skill_name = id_to_name.get(u_id, "current skill")
                if len(candidates[s_id]["reasons"]) < 3:
                    candidates[s_id]["reasons"].append(f"Similar to {user_skill_name}")

        # 4. Score Combination
        # Weights: relevance (0.5), synergy (0.3), similarity (0.2)
        w_rel = 0.5 if target_archetype_id is not None else 0.0
        w_syn = 0.6 if target_archetype_id is None else 0.3
        w_sim = 0.4 if target_archetype_id is None else 0.2

        recommendations = []
        for s_id, scores in candidates.items():
            final_score = (
                w_rel * scores["relevance"] +
                w_syn * scores["synergy"] +
                w_sim * scores["similarity"]
            )
            
            recommendations.append({
                "skill_id": s_id,
                "canonical_name": id_to_name.get(s_id, f"Skill {s_id}"),
                "score": float(final_score),
                "reasons": list(set(scores["reasons"]))[:3],
                "signals": {
                    "relevance": float(scores["relevance"]),
                    "synergy": float(scores["synergy"]),
                    "similarity": float(scores["similarity"])
                }
            })

        # Sort recommendations descending by score
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:top_k]
