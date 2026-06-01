"""
Compute Skill Synergies Script
==============================
This script runs the association rule mining on our database to populate the
skill_cooccurrences table, establishing the Skill Synergy Network weights.
"""

import os
import sys

# Add backend folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database import SessionLocal
from app.services.synergy_analyzer import SynergyAnalyzer


def run_synergies():
    db = SessionLocal()
    try:
        print("[Compute Synergies] Initializing Synergy Analyzer...")
        analyzer = SynergyAnalyzer(db)
        print("[Compute Synergies] Starting co-occurrence calculations...")
        count = analyzer.compute_and_save_synergies(min_cooccurrence=2)  # Set min_cooccurrence=2 for stability
        print(f"[Compute Synergies] Complete. Persisted {count} skill co-occurrence pairs.")
    except Exception as e:
        print(f"[Compute Synergies] Synergy calculation run failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run_synergies()
