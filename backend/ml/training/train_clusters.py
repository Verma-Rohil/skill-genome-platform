"""
Train Career Archetypes Script
===============================
This script executes the job posting clustering pipeline using the ClusteringEngine,
organizing our job postings into distinct career archetypes.
"""

import os
import sys

# Add backend folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database import SessionLocal
from app.services.clustering_engine import ClusteringEngine


def run_clustering():
    db = SessionLocal()
    try:
        print("[Train Clusters] Initializing Clustering Engine...")
        engine = ClusteringEngine(db)
        print("[Train Clusters] Starting job clustering process...")
        n_clusters = engine.train_archetypes()
        print(f"[Train Clusters] Complete. Generated and saved {n_clusters} career archetypes.")
    except Exception as e:
        print(f"[Train Clusters] Clustering run failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run_clustering()
