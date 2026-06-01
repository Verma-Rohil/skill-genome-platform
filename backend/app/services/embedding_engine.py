"""
Skill Embedding Engine
======================
Generates dense vector embeddings for skills using Sentence-BERT.

WHY THIS ENGINE:
- Translates semantic concepts into vector representations.
- Enables downstream clustering and semantic similarity search.
- Uses `all-MiniLM-L6-v2` S-BERT model to construct high-quality 384-dimensional embeddings.
"""

import numpy as np
from typing import List, Optional
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
from app.config import get_settings
from app.models.skill import Skill
from app.models.skill_embedding import SkillEmbedding


class EmbeddingEngine:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load S-BERT model to save startup time if not needed immediately."""
        if self._model is None:
            print(f"[EmbeddingEngine] Loading S-BERT model: {self.settings.EMBEDDING_MODEL_NAME}...")
            self._model = SentenceTransformer(self.settings.EMBEDDING_MODEL_NAME)
        return self._model

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generates a raw numpy embedding vector for the given text string."""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)

    def update_all_skill_embeddings(self) -> int:
        """
        Finds all skills in the database that do not have an embedding cached,
        generates the S-BERT vectors, and stores them in bulk.
        Returns the number of skills updated.
        """
        # Fetch all skills
        skills = self.db.query(Skill).all()
        if not skills:
            print("[EmbeddingEngine] No skills found in the database.")
            return 0

        # Fetch existing embeddings to check who is missing
        existing_embeddings = self.db.query(SkillEmbedding).all()
        embedded_skill_ids = {emb.skill_id for emb in existing_embeddings}

        skills_to_embed = [s for s in skills if s.id not in embedded_skill_ids]
        if not skills_to_embed:
            print("[EmbeddingEngine] All skills already have embeddings in the database.")
            return 0

        print(f"[EmbeddingEngine] Found {len(skills_to_embed)} skills missing embeddings. Generating...")

        count = 0
        for skill in skills_to_embed:
            try:
                # Use canonical name as the text to embed
                vector = self.generate_embedding(skill.canonical_name)
                
                # Check if an embedding somehow already exists to prevent duplicate key
                existing = self.db.query(SkillEmbedding).filter_by(skill_id=skill.id).first()
                if existing:
                    existing.vector = vector.tobytes()
                    existing.dimension = len(vector)
                    existing.model_version = self.settings.EMBEDDING_MODEL_NAME
                else:
                    db_emb = SkillEmbedding(
                        skill_id=skill.id,
                        vector=vector.tobytes(),
                        model_version=self.settings.EMBEDDING_MODEL_NAME,
                        dimension=len(vector)
                    )
                    self.db.add(db_emb)
                
                count += 1
                if count % 100 == 0:
                    self.db.flush()
                    print(f"[EmbeddingEngine] Generated embeddings for {count}/{len(skills_to_embed)} skills...")
            except Exception as e:
                print(f"[EmbeddingEngine] Error generating embedding for skill '{skill.canonical_name}': {e}")
                self.db.rollback()
                raise e

        self.db.commit()
        print(f"[EmbeddingEngine] Persisted {count} skill embeddings to the database.")
        return count
