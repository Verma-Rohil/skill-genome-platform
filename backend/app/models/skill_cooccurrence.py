"""
Skill Co-occurrence Model
==========================
Represents pairwise co-occurrence counts and association metrics between canonical skills.
These metrics are the foundation for the Skill Synergy Network and the Workforce Disruption Simulator.

Association Metrics:
- cooccurrence_count: Number of job postings containing both skills.
- support: P(A ∩ B) - Proportion of all jobs that contain both.
- confidence_a_b: P(B | A) - Conditional probability of B given A (if you have A, how likely is it the job requires B?).
- confidence_b_a: P(A | B) - Conditional probability of A given B.
- lift: P(A ∩ B) / (P(A) * P(B)) - Measure of how much more often A and B co-occur than expected by chance.
- pmi: Pointwise Mutual Information - log(P(A ∩ B) / (P(A)*P(B))) - measures semantic relatedness.
"""

from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base


class SkillCooccurrence(Base):
    __tablename__ = "skill_cooccurrences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_a_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    skill_b_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    cooccurrence_count = Column(Integer, nullable=False)
    support = Column(Float, nullable=False)
    confidence_a_b = Column(Float, nullable=False)
    confidence_b_a = Column(Float, nullable=False)
    lift = Column(Float, nullable=False)
    pmi = Column(Float, nullable=False)

    # Relationships
    skill_a = relationship("Skill", foreign_keys=[skill_a_id], back_populates="cooccurrences_a")
    skill_b = relationship("Skill", foreign_keys=[skill_b_id], back_populates="cooccurrences_b")

    __table_args__ = (
        UniqueConstraint("skill_a_id", "skill_b_id", name="uk_skills_pair"),
        Index("idx_lift", "lift"),
        Index("idx_cooccurrence", "cooccurrence_count"),
    )

    def __repr__(self):
        return f"<SkillCooccurrence(a={self.skill_a_id}, b={self.skill_b_id}, count={self.cooccurrence_count}, lift={self.lift:.2f})>"
