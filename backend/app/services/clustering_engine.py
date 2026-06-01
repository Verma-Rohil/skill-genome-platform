"""
Clusters job postings into distinct career archetypes based on their skill profiles.
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sklearn.cluster import KMeans
from app.config import get_settings
from app.models.job_posting import JobPosting
from app.models.job_skill import JobSkill
from app.models.skill import Skill
from app.models.skill_embedding import SkillEmbedding
from app.models.career_archetype import CareerArchetype
from app.models.archetype_skill import ArchetypeSkill


class ClusteringEngine:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def train_archetypes(self) -> int:
        """
        Runs KMeans clustering on the ingested job postings.
        Saves the resulting career archetypes and archetype-skill mappings.
        Returns the number of archetypes created.
        """
        print("[ClusteringEngine] Loading job postings and skill embeddings from database...")
        
        # 1. Load all skills and their S-BERT embeddings
        embeddings = self.db.query(SkillEmbedding).all()
        if not embeddings:
            print("[ClusteringEngine] Error: No skill embeddings found. Cannot cluster jobs.")
            return 0
            
        skill_embeddings = {}
        for emb in embeddings:
            skill_embeddings[emb.skill_id] = np.frombuffer(emb.vector, dtype=np.float32)

        # 2. Load job postings and their skills
        jobs = self.db.query(JobPosting).all()
        if not jobs:
            print("[ClusteringEngine] Error: No job postings found. Cannot cluster.")
            return 0

        # Fetch job-skill relations in bulk
        job_skills = self.db.query(JobSkill).all()
        job_to_skills = {}
        for js in job_skills:
            if js.job_id not in job_to_skills:
                job_to_skills[js.job_id] = []
            job_to_skills[js.job_id].append(js.skill_id)

        print(f"[ClusteringEngine] Processing {len(jobs)} jobs...")
        
        # 3. Create vector representation for each job posting by averaging its skill embeddings
        job_vectors = []
        job_ids = []
        
        for job in jobs:
            s_ids = job_to_skills.get(job.id, [])
            if not s_ids:
                continue
                
            # Average the S-BERT embeddings of the skills required for this job
            vectors = [skill_embeddings[s_id] for s_id in s_ids if s_id in skill_embeddings]
            if not vectors:
                continue
                
            job_vector = np.mean(vectors, axis=0)
            job_vectors.append(job_vector)
            job_ids.append(job.id)

        if not job_vectors:
            print("[ClusteringEngine] Error: No jobs with valid skill embeddings found.")
            return 0

        X = np.vstack(job_vectors)
        print(f"[ClusteringEngine] Clustering matrix shape: {X.shape}")

        # 4. Fit KMeans
        n_clusters = self.settings.CLUSTER_N
        print(f"[ClusteringEngine] Fitting KMeans with {n_clusters} clusters...")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        cluster_labels = kmeans.fit_predict(X)
        centroids = kmeans.cluster_centers_

        # Clear existing career archetypes and mappings to prevent primary/foreign key clashes
        print("[ClusteringEngine] Clearing existing archetypes from DB...")
        self.db.query(ArchetypeSkill).delete()
        self.db.query(CareerArchetype).delete()
        self.db.commit()

        # 5. Populate and save each Career Archetype
        skills_list = self.db.query(Skill).all()
        skills_map = {s.id: s for s in skills_list}
        
        print("[ClusteringEngine] Analysis and saving of archetypes...")
        for cluster_id in range(n_clusters):
            centroid = centroids[cluster_id]
            
            # Find jobs belonging to this cluster
            in_cluster_mask = (cluster_labels == cluster_id)
            in_cluster_job_ids = [job_ids[i] for i, in_cluster in enumerate(in_cluster_mask) if in_cluster]
            num_jobs = len(in_cluster_job_ids)
            
            # Compute skill frequencies within this cluster
            cluster_skill_counter = {}
            for j_id in in_cluster_job_ids:
                for s_id in job_to_skills.get(j_id, []):
                    cluster_skill_counter[s_id] = cluster_skill_counter.get(s_id, 0) + 1
                    
            # Calculate importance score as percentage of jobs in this cluster that contain the skill
            skill_importance = []
            for s_id, count in cluster_skill_counter.items():
                importance = float(count) / float(num_jobs)
                skill_importance.append((s_id, importance))
                
            # Sort skills by importance score descending and pick top 10 to auto-name the cluster
            skill_importance.sort(key=lambda x: x[1], reverse=True)
            top_skills = skill_importance[:10]
            
            # Generate a descriptive name based on the top 3 skills
            top_names = [skills_map[s_id].canonical_name for s_id, _ in top_skills[:3] if s_id in skills_map]
            name = f"Archetype {cluster_id + 1}: " + ", ".join(top_names)
            description = (
                f"A career archetype characterized by high demand for: "
                f"{', '.join([skills_map[s_id].canonical_name for s_id, _ in top_skills[:5] if s_id in skills_map])}."
            )

            # Insert CareerArchetype
            archetype = CareerArchetype(
                name=name,
                description=description,
                centroid_vector=centroid.tobytes(),
                model_version=f"kmeans_{self.settings.CLUSTER_N}_v1",
                num_jobs=num_jobs
            )
            self.db.add(archetype)
            self.db.flush()  # Retrieve archetype.id

            # Save top archetype-skills mapping
            for s_id, importance in skill_importance:
                # Store all skills or just those appearing in at least 5% of postings in cluster
                if importance >= 0.02:
                    arch_skill = ArchetypeSkill(
                        archetype_id=archetype.id,
                        skill_id=s_id,
                        importance_score=importance
                    )
                    self.db.add(arch_skill)

            print(f"[ClusteringEngine] Created {name} with {num_jobs} jobs.")

        self.db.commit()
        print("[ClusteringEngine] Career Archetype Clustering complete and persisted.")
        return n_clusters
