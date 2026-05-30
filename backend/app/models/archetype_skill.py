"""
Archetype-Skill Association Model
===================================
Links career archetypes to their defining skills with importance scores.

importance_score:
- Measures how central a skill is to this archetype
- Computed as: frequency of skill in cluster / total jobs in cluster
- Higher score = more defining skill for this career path
- Used by gap analyzer to prioritize which skills to recommend first
"""

from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ArchetypeSkill(Base):
    __tablename__ = "archetype_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    archetype_id = Column(Integer, ForeignKey("career_archetypes.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    importance_score = Column(Float, nullable=False)

    # Relationships
    archetype = relationship("CareerArchetype", back_populates="archetype_skills")
    skill = relationship("Skill", back_populates="archetype_skills")

    def __repr__(self):
        return (
            f"<ArchetypeSkill(archetype_id={self.archetype_id}, "
            f"skill_id={self.skill_id}, importance={self.importance_score:.2f})>"
        )
