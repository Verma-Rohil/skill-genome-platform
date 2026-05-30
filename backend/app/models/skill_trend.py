"""
Skill Trend Model
==================
Monthly snapshots of skill mention counts for time-series analysis.

WHY monthly granularity:
- Daily is too noisy (job postings vary by day of week)
- Quarterly is too coarse (misses short-term trends)
- Monthly balances signal vs noise — standard in labor analytics

growth_rate:
- Month-over-month percentage change
- Positive = growing skill, Negative = declining
- Used to identify "emerging" vs "declining" skills in the API
"""

from sqlalchemy import Column, Integer, Float, Date, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.database import Base


class SkillTrend(Base):
    __tablename__ = "skill_trends"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    period = Column(Date, nullable=False)              # Monthly: YYYY-MM-01
    mention_count = Column(Integer, nullable=False)
    growth_rate = Column(Float, nullable=True)          # MoM % change

    # Relationships
    skill = relationship("Skill", back_populates="trends")

    __table_args__ = (
        UniqueConstraint("skill_id", "period", name="uk_skill_period"),
        Index("idx_period", "period"),
    )

    def __repr__(self):
        return f"<SkillTrend(skill='{self.skill_id}', period={self.period}, count={self.mention_count})>"
