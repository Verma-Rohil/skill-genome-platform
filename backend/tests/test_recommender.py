"""
Unit Tests for Skill Recommender Engine
======================================
Verifies multi-signal recommendations and explanation mappings.
"""

import pytest
from unittest.mock import MagicMock
from app.models.skill import Skill
from app.models.skill_cooccurrence import SkillCooccurrence
from app.models.skill_embedding import SkillEmbedding
import numpy as np
from app.services.recommender import Recommender


@pytest.fixture
def mock_db():
    db = MagicMock()
    
    # 1. Dummy skills
    s1 = Skill(id=1, canonical_name="Python")
    s2 = Skill(id=2, canonical_name="PyTorch")
    s3 = Skill(id=3, canonical_name="Docker")
    s4 = Skill(id=4, canonical_name="Kubernetes")
    
    # Dummy embeddings
    v = np.zeros(384, dtype=np.float32)
    emb1 = SkillEmbedding(skill_id=1, vector=v.tobytes(), model_version="sbert", dimension=384)
    emb2 = SkillEmbedding(skill_id=2, vector=v.tobytes(), model_version="sbert", dimension=384)
    emb3 = SkillEmbedding(skill_id=3, vector=v.tobytes(), model_version="sbert", dimension=384)
    emb4 = SkillEmbedding(skill_id=4, vector=v.tobytes(), model_version="sbert", dimension=384)
    
    # 2. Co-occurrences (e.g. Docker co-occurs with Kubernetes)
    # Python -> PyTorch co-occurrence
    co1 = SkillCooccurrence(
        skill_a_id=1,
        skill_b_id=2,
        cooccurrence_count=50,
        support=0.05,
        confidence_a_b=0.50,  # P(PyTorch | Python) = 0.5
        confidence_b_a=0.70,  # P(Python | PyTorch)
        lift=3.0,
        pmi=1.58
    )
    
    # Docker -> Kubernetes co-occurrence
    co2 = SkillCooccurrence(
        skill_a_id=3,
        skill_b_id=4,
        cooccurrence_count=80,
        support=0.08,
        confidence_a_b=0.80,  # P(Kubernetes | Docker) = 0.80
        confidence_b_a=0.90,  # P(Docker | Kubernetes)
        lift=4.0,
        pmi=2.0
    )
    
    def query_side_effect(model_class):
        q_mock = MagicMock()
        if model_class == Skill:
            q_mock.all.return_value = [s1, s2, s3, s4]
        elif model_class == SkillCooccurrence:
            # Return co-occurrences matching user skills (Python, Docker)
            q_mock.filter.return_value.all.return_value = [co1, co2]
        elif model_class == SkillEmbedding:
            q_mock.all.return_value = [emb1, emb2, emb3, emb4]
        return q_mock
        
    db.query.side_effect = query_side_effect
    return db


def test_recommendations_no_archetype(mock_db, monkeypatch):
    # Mock SimilarityEngine
    mock_sim_engine = MagicMock()
    
    # Python is ID 1, Docker is ID 3
    # Return similarities
    def find_sim_side_effect(name_or_id, top_n=10):
        if name_or_id == "Python" or name_or_id == 1:
            return [(1, "Python", 1.0), (2, "PyTorch", 0.60)]
        elif name_or_id == "Docker" or name_or_id == 3:
            return [(3, "Docker", 1.0), (4, "Kubernetes", 0.70)]
        elif name_or_id == 4:
            return [(3, "Docker", 0.70)]
        return []
        
    mock_sim_engine.find_similar_skills.side_effect = find_sim_side_effect
    
    monkeypatch.setattr("app.services.recommender.SimilarityEngine", lambda db: mock_sim_engine)
    
    # Mock GapAnalyzer (not used when no archetype is set)
    
    recommender = Recommender(mock_db)
    
    # User has Python and Docker
    recs = recommender.recommend_skills(user_skills=["Python", "Docker"], target_archetype_id=None, top_k=5)
    
    assert len(recs) > 0
    # Kubernetes should be recommended because it has high synergy with Docker (P(K8s | Docker) = 0.80)
    # and is semantically similar to Docker (0.70 similarity)
    k8s_rec = [r for r in recs if r["canonical_name"] == "Kubernetes"][0]
    assert k8s_rec["score"] > 0.0
    assert any("Frequently paired with Docker" in reason for reason in k8s_rec["reasons"])
    assert any("Similar to Docker" in reason for reason in k8s_rec["reasons"])
