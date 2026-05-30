"""
Models Package — All SQLAlchemy ORM models.
Import all models here so that Base.metadata knows about them
(required for create_all and migrations).
"""

from app.models.skill_category import SkillCategory
from app.models.skill import Skill
from app.models.skill_embedding import SkillEmbedding
from app.models.job_posting import JobPosting
from app.models.job_skill import JobSkill
from app.models.career_archetype import CareerArchetype
from app.models.archetype_skill import ArchetypeSkill
from app.models.skill_trend import SkillTrend
from app.models.ml_experiment import MLExperiment

__all__ = [
    "SkillCategory",
    "Skill",
    "SkillEmbedding",
    "JobPosting",
    "JobSkill",
    "CareerArchetype",
    "ArchetypeSkill",
    "SkillTrend",
    "MLExperiment",
]
