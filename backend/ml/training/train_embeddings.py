"""
Generate/Train Skill Embeddings Script
======================================
This script loads all canonical skills from the database, generates their
Sentence-BERT embeddings, and stores them in the skill_embeddings table.

WHY RUN THIS AS A BATCH JOB:
- S-BERT model load and inference takes compute resources.
- Pre-computing and saving to MySQL avoids running S-BERT inside live API requests.
- Promotes fast startup and quick similarity lookups.
"""

import os
import sys

# Add backend folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.database import SessionLocal
from app.services.embedding_engine import EmbeddingEngine


def run_embedding_generation():
    db = SessionLocal()
    try:
        print("[Train Embeddings] Initializing Embedding Engine...")
        engine = EmbeddingEngine(db)
        print("[Train Embeddings] Starting batch embedding generation...")
        updated_count = engine.update_all_skill_embeddings()
        print(f"[Train Embeddings] Complete. Generated and saved {updated_count} skill embeddings.")
    except Exception as e:
        print(f"[Train Embeddings] Ingestion/Generation failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run_embedding_generation()
