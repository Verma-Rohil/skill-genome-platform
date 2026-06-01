"""
Unit Tests for Skill Gap Analyzer
=================================
Verifies skill gap matching, substitute credit calculation, and missing skills rankings.
"""

import pytest
from unittest.mock import MagicMock
from app.models.career_archetype import CareerArchetype
from app.models.archetype_skill import ArchetypeSkill
from app.models.skill import Skill
from app.services.gap_analyzer import GapAnalyzer


@pytest.fixture
def mock_db():
    db = MagicMock()
    
    # 1. Target Archetype
    archetype = CareerArchetype(id=1, name="Machine Learning Engineer", num_jobs=239)
    
    # 2. Archetype skills
    s1 = Skill(id=10, canonical_name="Python")
    s2 = Skill(id=20, canonical_name="TensorFlow")
    s3 = Skill(id=30, canonical_name="SQL")
    
    arch_s1 = ArchetypeSkill(archetype_id=1, skill_id=10, importance_score=0.8)
    arch_s2 = ArchetypeSkill(archetype_id=1, skill_id=20, importance_score=0.6)
    arch_s3 = ArchetypeSkill(archetype_id=1, skill_id=30, importance_score=0.4)
    
    def query_side_effect(model_class):
        q_mock = MagicMock()
        if model_class == CareerArchetype:
            q_mock.filter_by.return_value.first.return_value = archetype
        elif model_class == ArchetypeSkill:
            q_mock.filter_by.return_value.order_by.return_value.all.return_value = [arch_s1, arch_s2, arch_s3]
        elif model_class == Skill:
            def filter_side_effect(**kwargs):
                s_id = kwargs.get("id")
                s_mock = MagicMock()
                if s_id == 10:
                    s_mock.id = 10
                    s_mock.canonical_name = "Python"
                elif s_id == 20:
                    s_mock.id = 20
                    s_mock.canonical_name = "TensorFlow"
                elif s_id == 30:
                    s_mock.id = 30
                    s_mock.canonical_name = "SQL"
                
                query_res = MagicMock()
                query_res.first.return_value = s_mock
                return query_res
            q_mock.filter_by.side_effect = filter_side_effect
        return q_mock
        
    db.query.side_effect = query_side_effect
    return db


def test_gap_analysis_perfect_match(mock_db, monkeypatch):
    # Mock SimilarityEngine
    mock_sim_engine = MagicMock()
    # If looking up input skill, return itself
    def find_sim_side_effect(name_or_id, top_n=10):
        if name_or_id == "Python":
            return [(10, "Python", 1.0)]
        elif name_or_id == "TensorFlow":
            return [(20, "TensorFlow", 1.0)]
        elif name_or_id == "SQL":
            return [(30, "SQL", 1.0)]
        return []
    mock_sim_engine.find_similar_skills.side_effect = find_sim_side_effect
    
    monkeypatch.setattr("app.services.gap_analyzer.SimilarityEngine", lambda db: mock_sim_engine)
    
    analyzer = GapAnalyzer(mock_db)
    result = analyzer.analyze_gaps(user_skills=["Python", "TensorFlow", "SQL"], target_archetype_id=1)
    assert result["match_score"] == pytest.approx(1.0)
    assert len(result["matching_skills"]) == 3
    assert len(result["missing_skills"]) == 0


def test_gap_analysis_with_substitute(mock_db, monkeypatch):
    # Mock SimilarityEngine
    mock_sim_engine = MagicMock()
    # User has "PyTorch" instead of "TensorFlow". They are similar (score = 0.8)
    def find_sim_side_effect(name_or_id, top_n=10):
        if name_or_id == "PyTorch":
            return [(22, "PyTorch", 1.0)]
        elif name_or_id == "Python":
            return [(10, "Python", 1.0)]
        elif name_or_id == "TensorFlow":
            # PyTorch is close to TensorFlow
            return [(22, "PyTorch", 0.8)]
        return []
    mock_sim_engine.find_similar_skills.side_effect = find_sim_side_effect
    
    monkeypatch.setattr("app.services.gap_analyzer.SimilarityEngine", lambda db: mock_sim_engine)
    
    analyzer = GapAnalyzer(mock_db)
    # User has Python and PyTorch. Missing SQL (no similarity) and TensorFlow (but has PyTorch substitute)
    result = analyzer.analyze_gaps(user_skills=["Python", "PyTorch"], target_archetype_id=1)
    
    # Total importance = 0.8 (Python) + 0.6 (TensorFlow) + 0.4 (SQL) = 1.8
    # Earned importance = 0.8 (Python exact) + 0.6 * (0.8^2) (TensorFlow substitute credit) = 0.8 + 0.384 = 1.184
    # Match score = 1.184 / 1.8 = ~0.6577
    assert abs(result["match_score"] - 0.6577) < 0.001
    assert len(result["matching_skills"]) == 1  # Only Python matches exactly
    assert len(result["missing_skills"]) == 2  # TensorFlow and SQL are missing
    
    # Check that TensorFlow has substitute credit and PyTorch mapped as substitute
    tf_gap = [m for m in result["missing_skills"] if m["canonical_name"] == "TensorFlow"][0]
    assert tf_gap["closest_substitute"] == "PyTorch"
    assert tf_gap["substitute_similarity"] == 0.8
    assert tf_gap["substitute_credit"] > 0.3
