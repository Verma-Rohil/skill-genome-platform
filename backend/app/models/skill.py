"""
Skill Model
============
The core entity of the Skill Genome — represents a canonical skill.

KEY DESIGN DECISIONS:
1. canonical_name is UNIQUE — this is the "ground truth" name after normalization
2. aliases stored as JSON — allows flexible matching without a separate table
3. first_seen_at — enables temporal analysis ("when did 'LLMOps' first appear?")

WHY JSON for aliases (not a separate alias table):
- Aliases are read-heavy, write-rare (set once during normalization)
- JSON avoids an extra JOIN on every skill lookup
- MySQL 8.x has good JSON query support (JSON_CONTAINS)
- For a production system at scale, a separate table would be better
  (this is a conscious tradeoff we document in lessons_learned.md)
"""

from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    canonical_name = Column(String(150), nullable=False, unique=True)
    category_id = Column(Integer, ForeignKey("skill_categories.id"), nullable=True)
    aliases = Column(JSON, nullable=True)            # ["ML", "machine-learning"]
    first_seen_at = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    category = relationship("SkillCategory", back_populates="skills")
    job_skills = relationship("JobSkill", back_populates="skill")
    embedding = relationship("SkillEmbedding", back_populates="skill", uselist=False)
    archetype_skills = relationship("ArchetypeSkill", back_populates="skill")
    trends = relationship("SkillTrend", back_populates="skill")

    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.canonical_name}')>"
