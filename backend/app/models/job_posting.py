"""
Job Posting Model
==================
Represents a job posting from the dataset.

WHY we store raw descriptions:
- Enables re-extraction with improved NLP models later
- Supports full-text search in the API
- Allows EDA notebooks to analyze raw text

INDEX STRATEGY:
- posted_date: Most queries filter or group by time period
- title: Enables prefix search for job title filtering
"""

from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(100), nullable=True)
    title = Column(String(300), nullable=False)
    company_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)
    work_type = Column(String(50), nullable=True)          # Remote, Hybrid, On-site
    seniority_level = Column(String(50), nullable=True)     # Entry, Mid, Senior
    posted_date = Column(Date, nullable=True)
    source = Column(String(50), nullable=True)              # linkedin, indeed
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    job_skills = relationship("JobSkill", back_populates="job_posting")

    # Indexes
    __table_args__ = (
        Index("idx_posted_date", "posted_date"),
        Index("idx_title", "title", mysql_length=100),
    )

    def __repr__(self):
        return f"<JobPosting(id={self.id}, title='{self.title[:50]}')>"
