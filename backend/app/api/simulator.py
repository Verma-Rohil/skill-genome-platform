"""
Simulator Router
================
FastAPI router for running tech shock simulations and analyzing career archetype vulnerability.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.simulator import (
    DisruptionRequest,
    DisruptionResponse,
    PropagatedShockItem,
    ArchetypeVulnerabilityItem,
)
from app.services.disruption_simulator import DisruptionSimulator

router = APIRouter()


@router.post("/simulate", response_model=DisruptionResponse)
def simulate_shocks(payload: DisruptionRequest, db: Session = Depends(get_db)):
    """Simulates tech shocks propagation across skills and updates archetype vulnerability levels."""
    try:
        simulator = DisruptionSimulator(db)
        results = simulator.simulate_shocks(
            skill_shocks=payload.skill_shocks,
            decay_factor=payload.decay_factor
        )
        
        shocks = [
            PropagatedShockItem(
                skill_id=s["skill_id"],
                canonical_name=s["canonical_name"],
                initial_shock=s["initial_shock"],
                propagated_shock=s["propagated_shock"]
            )
            for s in results["skill_shocks"]
        ]
        
        vulnerabilities = [
            ArchetypeVulnerabilityItem(
                archetype_id=v["archetype_id"],
                archetype_name=v["archetype_name"],
                disruption_score=v["disruption_score"],
                num_jobs=v["num_jobs"]
            )
            for v in results["archetype_vulnerabilities"]
        ]
        
        return DisruptionResponse(
            skill_shocks=shocks,
            archetype_vulnerabilities=vulnerabilities
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shock simulation failed: {str(e)}")


@router.get("/vulnerability", response_model=DisruptionResponse)
def get_baseline_vulnerability(db: Session = Depends(get_db)):
    """Retrieves baseline vulnerability for all archetypes with zero initial shocks."""
    try:
        simulator = DisruptionSimulator(db)
        results = simulator.simulate_shocks(skill_shocks={})
        
        shocks = [
            PropagatedShockItem(
                skill_id=s["skill_id"],
                canonical_name=s["canonical_name"],
                initial_shock=s["initial_shock"],
                propagated_shock=s["propagated_shock"]
            )
            for s in results["skill_shocks"]
        ]
        
        vulnerabilities = [
            ArchetypeVulnerabilityItem(
                archetype_id=v["archetype_id"],
                archetype_name=v["archetype_name"],
                disruption_score=v["disruption_score"],
                num_jobs=v["num_jobs"]
            )
            for v in results["archetype_vulnerabilities"]
        ]
        
        return DisruptionResponse(
            skill_shocks=shocks,
            archetype_vulnerabilities=vulnerabilities
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch baseline vulnerability: {str(e)}")
