"""
Integration Tests for API Layer
=============================
Verifies routing, input validation, serialization, and business logic execution across all endpoints.
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.database import get_db
from app.models.skill import Skill
from app.models.skill_embedding import SkillEmbedding
from app.models.career_archetype import CareerArchetype
from app.models.archetype_skill import ArchetypeSkill
from app.models.skill_cooccurrence import SkillCooccurrence

# Define Mock Data
mock_skills = [
    Skill(id=1, canonical_name="Python", category_id=1, aliases=["python"]),
    Skill(id=2, canonical_name="PyTorch", category_id=1, aliases=["pytorch"]),
    Skill(id=3, canonical_name="React", category_id=2, aliases=["react"]),
]

v1 = np.zeros(384, dtype=np.float32)
v1[0] = 1.0
v2 = np.zeros(384, dtype=np.float32)
v2[0] = 0.8
v2[1] = 0.6
v2 = v2 / np.linalg.norm(v2)
v3 = np.zeros(384, dtype=np.float32)
v3[2] = 1.0

mock_embeddings = [
    SkillEmbedding(skill_id=1, vector=v1.tobytes(), model_version="sbert", dimension=384),
    SkillEmbedding(skill_id=2, vector=v2.tobytes(), model_version="sbert", dimension=384),
    SkillEmbedding(skill_id=3, vector=v3.tobytes(), model_version="sbert", dimension=384),
]

mock_archetypes = [
    CareerArchetype(id=1, name="AI Engineer", description="AI and Machine Learning cluster", num_jobs=100, model_version="kmeans_8_v1"),
    CareerArchetype(id=2, name="Frontend Engineer", description="Web UI development cluster", num_jobs=200, model_version="kmeans_8_v1"),
]

mock_archetype_skills = [
    ArchetypeSkill(id=1, archetype_id=1, skill_id=1, importance_score=0.9),
    ArchetypeSkill(id=2, archetype_id=1, skill_id=2, importance_score=0.8),
    ArchetypeSkill(id=3, archetype_id=2, skill_id=3, importance_score=0.95),
]

mock_cooccurrences = [
    SkillCooccurrence(
        id=1,
        skill_a_id=1,
        skill_b_id=2,
        cooccurrence_count=50,
        support=0.05,
        confidence_a_b=0.8,
        confidence_b_a=0.9,
        lift=4.0,
        pmi=2.0,
    )
]


class MockQuery:
    def __init__(self, model_class):
        self.model_class = model_class
        self.filters = {}

    def filter(self, *args, **kwargs):
        for arg in args:
            left = getattr(arg, "left", None)
            right = getattr(arg, "right", None)
            if left is not None and right is not None:
                key = getattr(left, "key", None) or getattr(left, "name", None)
                val = getattr(right, "value", None)
                if val is None:
                    val = right
                if key:
                    self.filters[key] = val
        return self

    def filter_by(self, **kwargs):
        self.filters.update(kwargs)
        return self

    def order_by(self, *args):
        return self

    def offset(self, val):
        return self

    def limit(self, val):
        return self

    def all(self):
        if self.model_class == Skill:
            return mock_skills
        elif self.model_class == SkillEmbedding:
            return mock_embeddings
        elif self.model_class == CareerArchetype:
            return mock_archetypes
        elif self.model_class == ArchetypeSkill:
            if "archetype_id" in self.filters:
                arch_id = self.filters["archetype_id"]
                return [s for s in mock_archetype_skills if s.archetype_id == arch_id]
            return mock_archetype_skills
        elif self.model_class == SkillCooccurrence:
            return mock_cooccurrences
        return []

    def first(self):
        if self.model_class == Skill:
            if "id" in self.filters:
                s_id = self.filters["id"]
                for s in mock_skills:
                    if s.id == s_id:
                        return s
            return mock_skills[0]
        elif self.model_class == SkillEmbedding:
            return mock_embeddings[0]
        elif self.model_class == CareerArchetype:
            if "id" in self.filters:
                a_id = self.filters["id"]
                for a in mock_archetypes:
                    if a.id == a_id:
                        return a
            return mock_archetypes[0]
        elif self.model_class == ArchetypeSkill:
            return mock_archetype_skills[0]
        elif self.model_class == SkillCooccurrence:
            return mock_cooccurrences[0]
        return None

    def count(self):
        if self.model_class == Skill:
            return len(mock_skills)
        return 0


@pytest.fixture
def client_override():
    db_mock = MagicMock()
    db_mock.query.side_effect = lambda model_class: MockQuery(model_class)
    
    app.dependency_overrides[get_db] = lambda: db_mock
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_endpoint(client_override):
    response = client_override.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_skills(client_override):
    response = client_override.get("/api/skills?limit=2")
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data) == 3
    assert json_data[0]["canonical_name"] == "Python"


def test_get_skill_details(client_override):
    response = client_override.get("/api/skills/1")
    assert response.status_code == 200
    assert response.json()["canonical_name"] == "Python"


def test_get_similar_skills(client_override):
    response = client_override.get("/api/skills/1/similar?top_n=2")
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data) > 0
    assert json_data[0]["canonical_name"] == "PyTorch"


def test_get_synergy_skills(client_override):
    response = client_override.get("/api/skills/1/synergy")
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data) == 1
    assert json_data[0]["canonical_name"] == "PyTorch"
    assert json_data[0]["lift"] == 4.0


def test_extract_skills(client_override):
    payload = {"text": "I am a developer coding in python and using pytorch for deep learning."}
    response = client_override.post("/api/skills/extract", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert "extracted_skills" in json_data
    # "Python" and "PyTorch" should be extracted because they are matched in Trie
    assert "Python" in json_data["extracted_skills"]
    assert "PyTorch" in json_data["extracted_skills"]


def test_list_archetypes(client_override):
    response = client_override.get("/api/careers/archetypes")
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data) == 2
    assert json_data[0]["name"] == "AI Engineer"


def test_get_archetype_details(client_override):
    response = client_override.get("/api/careers/archetypes/1")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["name"] == "AI Engineer"
    assert len(json_data["top_skills"]) == 2
    assert json_data["top_skills"][0]["canonical_name"] == "Python"


def test_career_gap_analysis(client_override):
    payload = {
        "current_skills": ["Python"],
        "target_archetype_id": 1
    }
    response = client_override.post("/api/careers/gap", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["archetype_name"] == "AI Engineer"
    assert json_data["match_score"] > 0.0
    # Matching skills should contain Python
    matching_names = [m["canonical_name"] for m in json_data["matching_skills"]]
    assert "Python" in matching_names
    # Missing skills should contain PyTorch
    missing_names = [m["canonical_name"] for m in json_data["missing_skills"]]
    assert "PyTorch" in missing_names


def test_get_recommendations(client_override):
    payload = {
        "current_skills": ["Python"],
        "target_archetype_id": 1,
        "top_k": 2
    }
    response = client_override.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert "recommendations" in json_data
    assert len(json_data["recommendations"]) > 0
    assert json_data["recommendations"][0]["canonical_name"] == "PyTorch"


def test_shock_propagation_simulation(client_override):
    payload = {
        "skill_shocks": {"Python": 0.8},
        "decay_factor": 0.5
    }
    response = client_override.post("/api/simulator/simulate", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert "skill_shocks" in json_data
    assert "archetype_vulnerabilities" in json_data
    # Python is shocked, which co-occurs with PyTorch, so PyTorch should have a propagated shock
    shocks_dict = {s["canonical_name"]: s["propagated_shock"] for s in json_data["skill_shocks"]}
    assert "Python" in shocks_dict
    assert "PyTorch" in shocks_dict
    assert shocks_dict["PyTorch"] > 0.0


def test_baseline_vulnerability(client_override):
    response = client_override.get("/api/simulator/vulnerability")
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data["archetype_vulnerabilities"]) == 2
    # Baseline vulnerability should have 0.0 scores
    assert json_data["archetype_vulnerabilities"][0]["disruption_score"] == 0.0
