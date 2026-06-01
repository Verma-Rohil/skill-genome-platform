"""
Skill Similarity Engine
=======================
Computes cosine similarity between skill vector representations to find similar skills.

WHY THIS ENGINE:
- Allows recommendation of alternate or related skills.
- Helps identify complementary skill pairings.
- Seamlessly handles both in-vocabulary skills (cached DB embeddings) and
  out-of-vocabulary terms (encoded on-the-fly via S-BERT).
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from sqlalchemy.orm import Session
from app.models.skill import Skill
from app.models.skill_embedding import SkillEmbedding
from app.services.embedding_engine import EmbeddingEngine


class SimilarityEngine:
    def __init__(self, db: Session):
        self.db = db
        self.embedding_engine = EmbeddingEngine(db)
        
        # Cache for in-memory matrix lookup
        self.skill_ids: List[int] = []
        self.id_to_canonical: Dict[int, str] = {}
        self.embeddings_matrix: Optional[np.ndarray] = None
        
        self.load_embeddings_cache()

    def load_embeddings_cache(self):
        """Loads all database-cached skill embeddings into an in-memory matrix for fast calculations."""
        try:
            embeddings = self.db.query(SkillEmbedding).all()
            if not embeddings:
                return

            vectors = []
            skill_ids = []
            id_to_canonical = {}
            
            # Fetch all skills to resolve IDs to names
            skills = self.db.query(Skill).all()
            skill_id_map = {s.id: s.canonical_name for s in skills}

            for emb in embeddings:
                # Deserialize from binary BLOB
                vec = np.frombuffer(emb.vector, dtype=np.float32)
                # Normalize vector to make cosine similarity a simple dot product
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = vec / norm
                
                vectors.append(vec)
                skill_ids.append(emb.skill_id)
                id_to_canonical[emb.skill_id] = skill_id_map.get(emb.skill_id, f"Skill {emb.skill_id}")

            self.embeddings_matrix = np.vstack(vectors)
            self.skill_ids = skill_ids
            self.id_to_canonical = id_to_canonical
            print(f"[SimilarityEngine] Cached {len(self.skill_ids)} skill embeddings in-memory.")
        except Exception as e:
            print(f"[SimilarityEngine] Error loading embeddings cache: {e}")

    def find_similar_skills_by_vector(self, query_vector: np.ndarray, top_n: int = 10) -> List[Tuple[int, str, float]]:
        """Given a query vector, calculates cosine similarity against all cached skill embeddings."""
        if self.embeddings_matrix is None or len(self.skill_ids) == 0:
            # Re-attempt cache load if empty
            self.load_embeddings_cache()
            if self.embeddings_matrix is None:
                print("[SimilarityEngine] No embeddings available for similarity search.")
                return []

        # Normalize query vector
        norm = np.linalg.norm(query_vector)
        if norm == 0:
            return []
        query_vector = query_vector / norm

        # Compute dot products (cosine similarity)
        similarities = np.dot(self.embeddings_matrix, query_vector)
        
        # Get top indices sorted descending
        top_indices = np.argsort(similarities)[::-1][:top_n]
        
        results = []
        for idx in top_indices:
            skill_id = self.skill_ids[idx]
            score = float(similarities[idx])
            results.append((skill_id, self.id_to_canonical.get(skill_id, f"Skill {skill_id}"), score))
            
        return results

    def find_similar_skills(self, skill_name_or_id, top_n: int = 10) -> List[Tuple[int, str, float]]:
        """
        Main interface to search similar skills.
        Supports:
        - skill_id (int)
        - skill name (str)
        """
        # Case 1: ID search (in-vocabulary lookup)
        if isinstance(skill_name_or_id, int):
            skill_id = skill_name_or_id
            if skill_id in self.skill_ids:
                idx = self.skill_ids.index(skill_id)
                vector = self.embeddings_matrix[idx]
                # Filter out the query skill itself from results
                results = self.find_similar_skills_by_vector(vector, top_n + 1)
                return [r for r in results if r[0] != skill_id][:top_n]
            else:
                # Skill ID not found
                return []

        # Case 2: String search
        query_str = str(skill_name_or_id).strip()
        query_lower = query_str.lower()
        
        # Check if the query string matches a canonical skill in our cached lookup
        matched_id = None
        for s_id, name in self.id_to_canonical.items():
            if name.lower() == query_lower:
                matched_id = s_id
                break

        if matched_id is not None:
            # In-vocabulary: use the cached database vector
            idx = self.skill_ids.index(matched_id)
            vector = self.embeddings_matrix[idx]
            results = self.find_similar_skills_by_vector(vector, top_n + 1)
            return [r for r in results if r[0] != matched_id][:top_n]
        else:
            # Out-of-vocabulary: generate new vector on-the-fly
            print(f"[SimilarityEngine] Query '{query_str}' not in canonical taxonomy. Generating vector...")
            vector = self.embedding_engine.generate_embedding(query_str)
            return self.find_similar_skills_by_vector(vector, top_n)
