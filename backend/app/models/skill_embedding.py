"""
Skill Embedding Model
======================
Stores vector representations of skills for similarity search.

WHY store in MySQL (not a vector DB like Pinecone):
- For our scale (~500-2000 skills), MySQL is sufficient
- No additional infrastructure complexity
- Embeddings loaded into memory at startup for fast cosine similarity
- In production at scale (1M+ vectors), we'd use FAISS or Pinecone

TRADEOFF (interview discussion point):
- MySQL BLOB is not optimized for vector operations
- We compensate by loading all vectors into a numpy matrix at startup
- This works because our vocabulary is small (thousands, not millions)
"""

from sqlalchemy import Column, Integer, String, LargeBinary, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SkillEmbedding(Base):
    __tablename__ = "skill_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, unique=True)
    vector = Column(LargeBinary, nullable=False)       # Serialized numpy array
    model_version = Column(String(50), nullable=False)  # e.g., "word2vec_v1"
    dimension = Column(Integer, nullable=False)          # e.g., 100
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    skill = relationship("Skill", back_populates="embedding")

    def __repr__(self):
        return f"<SkillEmbedding(skill_id={self.skill_id}, model='{self.model_version}')>"
