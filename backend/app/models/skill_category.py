"""
Skill Category Model
=====================
Broad groupings of skills (e.g., "Programming", "Cloud", "Soft Skills").

WHY CATEGORIES:
- Enables roll-up analytics: "How many Cloud skills does this job need?"
- Better visualization grouping in the dashboard
- Helps with skill taxonomy organization

INTERVIEW NOTE:
"I used a hierarchical taxonomy — categories group individual skills.
This allows me to analyze demand at both granular (Python) and aggregate
(Programming Languages) levels."
"""

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SkillCategory(Base):
    __tablename__ = "skill_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationship: one category has many skills
    skills = relationship("Skill", back_populates="category")

    def __repr__(self):
        return f"<SkillCategory(id={self.id}, name='{self.name}')>"
