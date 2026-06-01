"""
Computes association metrics (Support, Confidence, Lift, PMI) for skill pairings.
"""

import math
from typing import List, Dict, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.job_skill import JobSkill
from app.models.job_posting import JobPosting
from app.models.skill import Skill
from app.models.skill_cooccurrence import SkillCooccurrence


class SynergyAnalyzer:
    def __init__(self, db: Session):
        self.db = db

    def compute_and_save_synergies(self, min_cooccurrence: int = 1) -> int:
        """
        Calculates co-occurrence metrics for all skills in job postings.
        Saves results to the skill_cooccurrences table.
        Returns the number of pairs saved.
        """
        print("[SynergyAnalyzer] Fetching jobs and job skills mappings...")
        
        # 1. Total jobs count
        N = self.db.query(JobPosting).count()
        if N == 0:
            print("[SynergyAnalyzer] Error: No jobs in database to calculate synergies.")
            return 0

        # 2. Count individual skill frequencies across all jobs
        skill_counts_query = (
            self.db.query(JobSkill.skill_id, func.count(JobSkill.job_id))
            .group_by(JobSkill.skill_id)
            .all()
        )
        
        skill_counts = {skill_id: count for skill_id, count in skill_counts_query}
        print(f"[SynergyAnalyzer] Loaded frequencies for {len(skill_counts)} skills.")

        # 3. Fetch all job-skill pairings grouped by job_id
        job_skills = self.db.query(JobSkill.job_id, JobSkill.skill_id).all()
        job_to_skills = {}
        for job_id, skill_id in job_skills:
            if job_id not in job_to_skills:
                job_to_skills[job_id] = []
            job_to_skills[job_id].append(skill_id)

        # 4. Count pairwise co-occurrences
        print("[SynergyAnalyzer] Calculating pairwise co-occurrences...")
        cooccurrence_counts = {}
        
        for job_id, s_ids in job_to_skills.items():
            s_ids_sorted = sorted(list(set(s_ids)))
            # Compute combinations of pairs
            for i in range(len(s_ids_sorted)):
                s_a = s_ids_sorted[i]
                for j in range(i + 1, len(s_ids_sorted)):
                    s_b = s_ids_sorted[j]
                    pair = (s_a, s_b)
                    cooccurrence_counts[pair] = cooccurrence_counts.get(pair, 0) + 1

        print(f"[SynergyAnalyzer] Found {len(cooccurrence_counts)} unique skill pairs. Filtering by min_cooccurrence >= {min_cooccurrence}...")
        
        # Filter pairs
        filtered_pairs = {
            pair: count for pair, count in cooccurrence_counts.items()
            if count >= min_cooccurrence
        }
        print(f"[SynergyAnalyzer] {len(filtered_pairs)} pairs passed the threshold.")

        # Clear existing co-occurrences to avoid primary/unique key crashes
        print("[SynergyAnalyzer] Clearing existing co-occurrences...")
        self.db.query(SkillCooccurrence).delete()
        self.db.commit()

        # 5. Compute association metrics and save in batch
        print("[SynergyAnalyzer] Calculating Support, Confidence, Lift, and PMI...")
        
        cooccurrences_to_insert = []
        count = 0
        
        for (s_a, s_b), c_count in filtered_pairs.items():
            freq_a = skill_counts.get(s_a, 0)
            freq_b = skill_counts.get(s_b, 0)
            
            if freq_a == 0 or freq_b == 0:
                continue

            # Support: P(A ∩ B)
            support = float(c_count) / float(N)
            
            # Confidence A -> B: P(B | A)
            confidence_a_b = float(c_count) / float(freq_a)
            
            # Confidence B -> A: P(A | B)
            confidence_b_a = float(c_count) / float(freq_b)
            
            # Lift: P(A ∩ B) / (P(A) * P(B)) = (c_count / N) / ((freq_a / N) * (freq_b / N))
            lift = (float(c_count) * float(N)) / (float(freq_a) * float(freq_b))
            
            # PMI: log2(Lift)
            pmi = math.log2(lift) if lift > 0 else 0.0

            # Store both A->B and B->A in separate entries or represent symmetrically in the table?
            # To maintain unique pairs and keep table size small, we save once with skill_a_id < skill_b_id.
            # Confidence A -> B is P(B | A) and Confidence B -> A is P(A | B).
            # This is exactly what the schema cooccurrences columns represent!
            # - confidence_a_b = P(b | a)
            # - confidence_b_a = P(a | b)
            
            sc = SkillCooccurrence(
                skill_a_id=s_a,
                skill_b_id=s_b,
                cooccurrence_count=c_count,
                support=support,
                confidence_a_b=confidence_a_b,
                confidence_b_a=confidence_b_a,
                lift=lift,
                pmi=pmi
            )
            self.db.add(sc)
            count += 1
            
            if count % 2000 == 0:
                self.db.flush()

        self.db.commit()
        print(f"[SynergyAnalyzer] SUCCESSFULLY calculated and saved {count} skill co-occurrence records.")
        return count
