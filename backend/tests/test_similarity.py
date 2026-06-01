"""
Unit Tests for Skill Similarity Engine
======================================
Verifies cosine similarity, cached in-memory lookups, and out-of-vocabulary S-BERT matches.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock
from app.models.skill import Skill
from app.models.skill_embedding import SkillEmbedding
from app.services.similarity_engine import SimilarityEngine


@pytest.fixture
def mock_db():
    db = MagicMock()
    
    # Create two dummy skills
    skill1 = Skill(id=1, canonical_name="Python", category_id=1, aliases=["python"])
    skill2 = Skill(id=2, canonical_name="Java", category_id=1, aliases=["java"])
    skill3 = Skill(id=3, canonical_name="Machine Learning", category_id=2, aliases=["ml"])
    
    # Create dummy embeddings
    # SBERT dimension is 384
    v1 = np.zeros(384, dtype=np.float32)
    v1[0] = 1.0  # Python vector
    
    v2 = np.zeros(384, dtype=np.float32)
    v2[1] = 1.0  # Java vector (orthogonal to Python)
    
    v3 = np.zeros(384, dtype=np.float32)
    v3[0] = 0.8
    v3[2] = 0.6  # Machine learning vector (high overlap with Python, normalized)
    
    # Normalize v3
    v3 = v3 / np.linalg.norm(v3)
    
    emb1 = SkillEmbedding(skill_id=1, vector=v1.tobytes(), model_version="sbert", dimension=384)
    emb2 = SkillEmbedding(skill_id=2, vector=v2.tobytes(), model_version="sbert", dimension=384)
    emb3 = SkillEmbedding(skill_id=3, vector=v3.tobytes(), model_version="sbert", dimension=384)
    
    def query_side_effect(model_class):
        q_mock = MagicMock()
        if model_class == Skill:
            q_mock.all.return_value = [skill1, skill2, skill3]
        elif model_class == SkillEmbedding:
            q_mock.all.return_value = [emb1, emb2, emb3]
        return q_mock
        
    db.query.side_effect = query_side_effect
    return db


def test_load_cache(mock_db):
    engine = SimilarityEngine(mock_db)
    assert len(engine.skill_ids) == 3
    assert engine.id_to_canonical[1] == "Python"
    assert engine.id_to_canonical[2] == "Java"
    assert engine.id_to_canonical[3] == "Machine Learning"


def test_similarity_in_vocabulary(mock_db):
    engine = SimilarityEngine(mock_db)
    
    # Query similar to Python (should return Machine Learning and Java)
    results = engine.find_similar_skills("Python", top_n=2)
    assert len(results) == 2
    
    # Machine Learning has v3[0]=0.8 (overlap with Python) and Java is orthogonal (score=0.0)
    # So Machine Learning should be first
    assert results[0][1] == "Machine Learning"
    assert results[0][2] > 0.7  # Cosine similarity should be ~0.8
    assert results[1][1] == "Java"
    assert results[1][2] == 0.0


def test_similarity_by_id(mock_db):
    engine = SimilarityEngine(mock_db)
    
    # Query similar to skill_id 1 (Python)
    results = engine.find_similar_skills(1, top_n=2)
    assert len(results) == 2
    assert results[0][1] == "Machine Learning"


def test_out_of_vocabulary(mock_db):
    engine = SimilarityEngine(mock_db)
    
    # Mock embedding_engine.generate_embedding to return a vector similar to Python
    v_query = np.zeros(384, dtype=np.float32)
    v_query[0] = 0.95
    v_query[1] = 0.05
    engine.embedding_engine.generate_embedding = MagicMock(return_value=v_query)
    
    results = engine.find_similar_skills("Python scripting", top_n=1)
    
    # The query is very similar to Python (dimension 0 is high)
    assert len(results) == 1
    assert results[0][1] == "Python"
    # Verify the mock was called
    engine.embedding_engine.generate_embedding.assert_called_once_with("Python scripting")
