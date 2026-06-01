"""
Unit Tests — Skill Normalization Service
=========================================
Tests the cascading normalizer (Exact -> Fuzzy Levenshtein -> S-BERT Cosine).
Uses a mock database session for fast, isolated test execution.
"""

import pytest
import json
from unittest.mock import MagicMock
from app.models.skill import Skill
from app.models.skill_embedding import SkillEmbedding
from app.services.skill_normalizer import SkillNormalizer

# Sample skills database mock
MOCK_SKILLS_DATA = [
    {"id": 1, "canonical_name": "Python", "aliases": ["python", "py", "python-lang"]},
    {"id": 2, "canonical_name": "Machine Learning", "aliases": ["ml", "machine-learning", "statistical-learning"]},
    {"id": 3, "canonical_name": "Docker", "aliases": ["docker", "containers"]},
    {"id": 4, "canonical_name": "React", "aliases": ["react", "reactjs", "react.js"]}
]

@pytest.fixture
def mock_db_session():
    """Mocks a SQLAlchemy Session returning our sample skills data."""
    session = MagicMock()
    
    mock_skills = []
    for item in MOCK_SKILLS_DATA:
        skill = MagicMock(spec=Skill)
        skill.id = item["id"]
        skill.canonical_name = item["canonical_name"]
        skill.aliases = item["aliases"]
        mock_skills.append(skill)
        
    session.query.return_value.all.return_value = mock_skills
    return session


def test_normalizer_tier_1_exact(mock_db_session):
    """Tests exact matching of canonical name and pre-registered aliases."""
    normalizer = SkillNormalizer(mock_db_session)
    
    # Exact canonical name
    assert normalizer.normalize("Python") == "Python"
    # Case insensitivity
    assert normalizer.normalize("python") == "Python"
    # Exact registered alias
    assert normalizer.normalize("py") == "Python"
    assert normalizer.normalize("reactjs") == "React"
    assert normalizer.normalize("ml") == "Machine Learning"


def test_normalizer_tier_2_fuzzy(mock_db_session):
    """Tests Levenshtein fuzzy edit-distance matching for spelling errors or space changes."""
    normalizer = SkillNormalizer(mock_db_session, similarity_threshold=0.80)
    
    # Small typo / suffix addition
    assert normalizer.normalize("python3") == "Python"
    # Spacing and hyphens
    assert normalizer.normalize("machinelearning") == "Machine Learning"
    # Spelling typo
    assert normalizer.normalize("dockerr") == "Docker"
    # Case and spacing
    assert normalizer.normalize("react js") == "React"


def test_normalizer_unmatched_returns_none(mock_db_session):
    """Tests that completely unrelated skills return None (avoiding false matches)."""
    normalizer = SkillNormalizer(mock_db_session, similarity_threshold=0.85)
    
    # Unrelated term
    assert normalizer.normalize("marketing") is None
    assert normalizer.normalize("accounting") is None
    # Empty strings
    assert normalizer.normalize("") is None
    assert normalizer.normalize(None) is None
