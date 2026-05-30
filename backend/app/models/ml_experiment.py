"""
ML Experiment Model
====================
Tracks ML experiments (supplements MLflow for DB-level querying).

WHY both MLflow AND this table:
- MLflow stores detailed artifacts (model files, plots, logs)
- This table enables SQL queries across experiments:
  "Which embedding model had the best silhouette score?"
- Dashboard can query this table directly via API
- In production, this would be replaced by MLflow's REST API

This is a SUPPLEMENTARY tracking table, not a replacement for MLflow.
"""

from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base


class MLExperiment(Base):
    __tablename__ = "ml_experiments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_name = Column(String(200), nullable=False)
    model_type = Column(String(100), nullable=True)     # word2vec, kmeans, prophet
    parameters = Column(JSON, nullable=True)             # {"dim": 100, "window": 5}
    metrics = Column(JSON, nullable=True)                # {"silhouette": 0.45}
    artifact_path = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
        return f"<MLExperiment(id={self.id}, name='{self.experiment_name}')>"
