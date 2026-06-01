"""
Unit Tests for Workforce Disruption Simulator
=============================================
Verifies 2-hop shock propagation and archetype vulnerability scoring.
"""

import pytest
from unittest.mock import MagicMock
from app.models.skill import Skill
from app.models.skill_cooccurrence import SkillCooccurrence
from app.models.career_archetype import CareerArchetype
from app.models.archetype_skill import ArchetypeSkill
from app.services.disruption_simulator import DisruptionSimulator


@pytest.fixture
def mock_db():
    db = MagicMock()
    
    # 1. Dummy skills
    s1 = Skill(id=1, canonical_name="Python")
    s2 = Skill(id=2, canonical_name="PyTorch")
    s3 = Skill(id=3, canonical_name="Docker")
    
    # 2. Co-occurrences (PyTorch and Python co-occur frequently)
    # PyTorch -> Python confidence_a_b (P(Python | PyTorch)) = 0.90
    # Python -> PyTorch confidence_b_a (P(PyTorch | Python)) = 0.20
    # Python -> Docker confidence_a_b (P(Docker | Python)) = 0.30
    co1 = SkillCooccurrence(
        skill_a_id=2,  # PyTorch
        skill_b_id=1,  # Python
        cooccurrence_count=90,
        support=0.09,
        confidence_a_b=0.90,  # P(Python | PyTorch)
        confidence_b_a=0.20,  # P(PyTorch | Python)
        lift=4.5,
        pmi=2.17
    )
    
    co2 = SkillCooccurrence(
        skill_a_id=1,  # Python
        skill_b_id=3,  # Docker
        cooccurrence_count=30,
        support=0.03,
        confidence_a_b=0.30,  # P(Docker | Python)
        confidence_b_a=0.50,  # P(Python | Docker)
        lift=2.0,
        pmi=1.0
    )

    # 3. Career Archetypes
    archetype = CareerArchetype(id=1, name="ML Engineer", num_jobs=100)

    # Archetype skills: Python (importance = 0.8), PyTorch (importance = 0.6)
    arch_s1 = ArchetypeSkill(archetype_id=1, skill_id=1, importance_score=0.8)
    arch_s2 = ArchetypeSkill(archetype_id=1, skill_id=2, importance_score=0.6)
    
    def query_side_effect(model_class):
        q_mock = MagicMock()
        if model_class == Skill:
            q_mock.all.return_value = [s1, s2, s3]
        elif model_class == SkillCooccurrence:
            q_mock.all.return_value = [co1, co2]
        elif model_class == CareerArchetype:
            q_mock.all.return_value = [archetype]
        elif model_class == ArchetypeSkill:
            q_mock.filter_by.return_value.all.return_value = [arch_s1, arch_s2]
        return q_mock
        
    db.query.side_effect = query_side_effect
    return db


def test_shock_propagation(mock_db):
    simulator = DisruptionSimulator(mock_db)
    
    # Shock PyTorch (ID 2) by 1.0
    results = simulator.simulate_shocks(skill_shocks={"PyTorch": 1.0}, decay_factor=0.5)
    
    shocks_by_name = {s["canonical_name"]: s["propagated_shock"] for s in results["skill_shocks"]}
    
    # 1. Initial shock is preserved
    assert shocks_by_name["PyTorch"] == 1.0
    
    # 2. Hop 1: Python should receive shock from PyTorch:
    # s1[Python] = PyTorch_shock (1.0) * P(Python | PyTorch) (0.90) = 0.90
    assert shocks_by_name["Python"] == pytest.approx(0.90)
    
    # 3. Hop 2: Docker should receive shock from Python in second hop with decay:
    # s2[Docker] = s1[Python] (0.90) * P(Docker | Python) (0.30) * decay (0.5) = 0.135
    assert shocks_by_name["Docker"] == pytest.approx(0.135)


def test_archetype_vulnerability(mock_db):
    simulator = DisruptionSimulator(mock_db)
    
    # Shock PyTorch by 1.0
    results = simulator.simulate_shocks(skill_shocks={"PyTorch": 1.0}, decay_factor=0.5)
    
    # ML Engineer archetype has Python (importance 0.8) and PyTorch (importance 0.6)
    # final shock values: PyTorch = 1.0, Python = 0.90
    # Disruption = (0.8 * 0.90 + 0.6 * 1.0) / (0.8 + 0.6) = (0.72 + 0.60) / 1.4 = 1.32 / 1.4 = 0.9428
    vulnerabilities = results["archetype_vulnerabilities"]
    assert len(vulnerabilities) == 1
    assert vulnerabilities[0]["archetype_name"] == "ML Engineer"
    assert vulnerabilities[0]["disruption_score"] == pytest.approx(0.9428, abs=0.001)
