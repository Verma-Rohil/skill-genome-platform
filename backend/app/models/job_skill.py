"""
Job-Skill Junction Model
==========================
Many-to-many relationship between job postings and skills.

WHY a junction table (not JSON array on job_postings):
- Enables efficient queries: "Find all jobs requiring Python"
- Supports aggregate analysis: "How many jobs mention Docker?"
- Allows additional metadata per association (confidence, is_required)

DESIGN NOTES:
- confidence: Extraction confidence score (1.0 for dictionary match,
  0.7-0.9 for NER-based extraction). Useful for filtering low-quality matches.
- is_required: Differentiates "must have" vs "nice to have" skills.
  Critical for accurate skill gap analysis.
"""

from sqlalchemy import Column, Integer, Boolean, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    is_required = Column(Boolean, default=True)
    confidence = Column(Float, default=1.0)

    # Relationships
    job_posting = relationship("JobPosting", back_populates="job_skills")
    skill = relationship("Skill", back_populates="job_skills")

    __table_args__ = (
        UniqueConstraint("job_id", "skill_id", name="uk_job_skill"),
        Index("idx_skill_id", "skill_id"),
    )

    def __repr__(self):
        return f"<JobSkill(job_id={self.job_id}, skill_id={self.skill_id})>"
