"""
Workforce Disruption Simulator Schemas
======================================
Pydantic models for technology shock propagation simulation and career archetype vulnerability analysis.
"""

from typing import List, Dict
from pydantic import BaseModel, Field


class DisruptionRequest(BaseModel):
    skill_shocks: Dict[str, float] = Field(
        ..., 
        description="Map of skill canonical name or ID to initial shock level in [0.0, 1.0]"
    )
    decay_factor: float = Field(
        0.5, 
        description="Decay factor at hop 2 propagation"
    )


class PropagatedShockItem(BaseModel):
    skill_id: int
    canonical_name: str
    initial_shock: float
    propagated_shock: float


class ArchetypeVulnerabilityItem(BaseModel):
    archetype_id: int
    archetype_name: str
    disruption_score: float = Field(..., description="Vulnerability or disruption index in [0.0, 1.0]")
    num_jobs: int


class DisruptionResponse(BaseModel):
    skill_shocks: List[PropagatedShockItem]
    archetype_vulnerabilities: List[ArchetypeVulnerabilityItem]
