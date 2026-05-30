"""
Career Archetype Model
=======================
Represents a discovered career cluster (e.g., "ML Engineer", "Data Analyst").

HOW ARCHETYPES ARE CREATED:
1. Each job posting is represented as a vector (average of its skill embeddings)
2. KMeans/HDBSCAN clusters similar job vectors together
3. Each cluster becomes an "archetype" — a prototypical career profile
4. The archetype's top skills are stored in archetype_skills

WHY "archetype" not "cluster":
- Product thinking: Users understand "ML Engineer archetype" not "Cluster 3"
- We manually label clusters with meaningful names during training
- This is how data science meets product design
"""

from sqlalchemy import Column, Integer, String, Text, LargeBinary, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CareerArchetype(Base):
    __tablename__ = "career_archetypes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    centroid_vector = Column(LargeBinary, nullable=True)    # Cluster centroid
    model_version = Column(String(50), nullable=False)
    num_jobs = Column(Integer, nullable=True)                 # Size of cluster
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    archetype_skills = relationship("ArchetypeSkill", back_populates="archetype")

    def __repr__(self):
        return f"<CareerArchetype(id={self.id}, name='{self.name}')>"
