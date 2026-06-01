"""
Workforce Disruption Simulator Service
======================================
Simulates technology shock propagation through the Skill Synergy Network using
conditional probabilities, and calculates the vulnerability of career archetypes.

WHY THIS SIMULATOR:
- Pivots Goal 6 from static trend forecasting to dynamic workforce "What-If" planning.
- Uses conditional probability transition weights P(B | A) from co-occurrence mining.
- Models 2-hop shock propagation with mathematical decay (decay_factor = 0.5).
"""

from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from app.models.skill import Skill
from app.models.skill_cooccurrence import SkillCooccurrence
from app.models.career_archetype import CareerArchetype
from app.models.archetype_skill import ArchetypeSkill


class DisruptionSimulator:
    def __init__(self, db: Session):
        self.db = db

    def simulate_shocks(self, skill_shocks: Dict[str, float], decay_factor: float = 0.5) -> Dict[str, Any]:
        """
        Runs shock propagation on the Skill Synergy Network.
        Input: Dict mapping skill names (or IDs) -> initial shock [0.0, 1.0].
        Output: Dict containing final propagated shocks and archetype vulnerabilities.
        """
        # 1. Resolve all skills and map to database IDs
        skills = self.db.query(Skill).all()
        name_to_id = {s.canonical_name.lower(): s.id for s in skills}
        id_to_name = {s.id: s.canonical_name for s in skills}
        
        # Parse initial shocks
        initial_shocks_id = {}
        for skill_key, shock_val in skill_shocks.items():
            shock_val = max(0.0, min(1.0, float(shock_val)))
            key_str = str(skill_key).strip().lower()
            
            # Resolve by ID if digit, else by name
            if key_str.isdigit():
                s_id = int(key_str)
                if s_id in id_to_name:
                    initial_shocks_id[s_id] = shock_val
            elif key_str in name_to_id:
                initial_shocks_id[name_to_id[key_str]] = shock_val

        if not initial_shocks_id:
            print("[DisruptionSimulator] Warning: No valid skills found in the shock input. Returning baseline.")
            archetypes = self.db.query(CareerArchetype).all()
            vulnerabilities = [
                {
                    "archetype_id": arch.id,
                    "archetype_name": arch.name,
                    "disruption_score": 0.0,
                    "num_jobs": arch.num_jobs
                }
                for arch in archetypes
            ]
            return {"skill_shocks": [], "archetype_vulnerabilities": vulnerabilities}

        # 2. Load all co-occurrence relationships as transition weights
        cooccurrences = self.db.query(SkillCooccurrence).all()
        
        # Build transition weight dictionary: T[source_id][target_id] = P(target | source)
        T = {}
        for co in cooccurrences:
            s_a, s_b = co.skill_a_id, co.skill_b_id
            
            if s_a not in T:
                T[s_a] = {}
            if s_b not in T:
                T[s_b] = {}
                
            # Confidence_a_b is P(B | A) (i.e. transition A -> B)
            T[s_a][s_b] = co.confidence_a_b
            # Confidence_b_a is P(A | B) (i.e. transition B -> A)
            T[s_b][s_a] = co.confidence_b_a

        # 3. Propagate shocks (Hop 1)
        # s1[j] = max( s0[j], sum_{i} s0[i] * P(j | i) )
        s1 = {}
        for target_id in id_to_name.keys():
            s0_val = initial_shocks_id.get(target_id, 0.0)
            
            contributions = 0.0
            for source_id, source_shock in initial_shocks_id.items():
                if source_id != target_id:
                    p_transition = T.get(source_id, {}).get(target_id, 0.0)
                    contributions += source_shock * p_transition
                    
            s1[target_id] = max(s0_val, min(1.0, contributions))

        # 4. Propagate shocks (Hop 2 with decay)
        # s2[j] = max( s1[j], gamma * sum_{k} s1[k] * P(j | k) )
        s2 = {}
        for target_id in id_to_name.keys():
            s1_val = s1.get(target_id, 0.0)
            
            contributions = 0.0
            for source_id, source_shock in s1.items():
                if source_id != target_id:
                    p_transition = T.get(source_id, {}).get(target_id, 0.0)
                    contributions += source_shock * p_transition
                    
            s2[target_id] = max(s1_val, min(1.0, decay_factor * contributions))

        # Format output shocks
        formatted_shocks = []
        for s_id, shock_val in s2.items():
            if shock_val > 0.001 or s_id in initial_shocks_id:
                formatted_shocks.append({
                    "skill_id": s_id,
                    "canonical_name": id_to_name[s_id],
                    "initial_shock": float(initial_shocks_id.get(s_id, 0.0)),
                    "propagated_shock": float(shock_val)
                })
        
        # Sort by propagated shock descending
        formatted_shocks.sort(key=lambda x: x["propagated_shock"], reverse=True)

        # 5. Assess Career Archetype Vulnerabilities
        # Disruption_c = sum_{j} Importance_{c, j} * s2[j]
        archetypes = self.db.query(CareerArchetype).all()
        vulnerabilities = []
        
        for arch in archetypes:
            arch_skills = self.db.query(ArchetypeSkill).filter_by(archetype_id=arch.id).all()
            
            disruption_score = 0.0
            total_importance = 0.0
            
            for askill in arch_skills:
                importance = askill.importance_score
                shock_val = s2.get(askill.skill_id, 0.0)
                disruption_score += importance * shock_val
                total_importance += importance
                
            # Normalize disruption score relative to target total importance
            normalized_disruption = disruption_score / total_importance if total_importance > 0 else 0.0
            
            vulnerabilities.append({
                "archetype_id": arch.id,
                "archetype_name": arch.name,
                "disruption_score": float(normalized_disruption),
                "num_jobs": arch.num_jobs
            })
            
        vulnerabilities.sort(key=lambda x: x["disruption_score"], reverse=True)

        return {
            "skill_shocks": formatted_shocks,
            "archetype_vulnerabilities": vulnerabilities
        }
