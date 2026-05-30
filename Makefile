# ============================================================
# Skill Genome Platform — Makefile
# ============================================================
# Usage: make <target>

.PHONY: help install dev test lint serve train-embeddings train-clusters train-trends seed-db docker-up docker-down

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# --- Setup ---
install:  ## Install Python dependencies
	pip install -r backend/requirements.txt
	python -m spacy download en_core_web_sm

# --- Development ---
dev:  ## Start FastAPI dev server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

serve: dev  ## Alias for dev

test:  ## Run all tests
	cd backend && python -m pytest tests/ -v

lint:  ## Lint Python code
	cd backend && python -m flake8 app/ --max-line-length 120

# --- Data ---
seed-db:  ## Seed MySQL database with processed data
	cd backend && python data/scripts/seed_db.py

# --- ML Training ---
train-embeddings:  ## Train skill embeddings (Word2Vec)
	cd backend && python ml/training/train_embeddings.py

train-clusters:  ## Train career archetype clusters
	cd backend && python ml/training/train_clusters.py

train-trends:  ## Train trend forecasting models
	cd backend && python ml/training/train_trend_model.py

train-all: train-embeddings train-clusters train-trends  ## Train all models

# --- Docker ---
docker-up:  ## Start all services via Docker Compose
	cd mlops && docker-compose up -d

docker-down:  ## Stop all Docker services
	cd mlops && docker-compose down

# --- MLflow ---
mlflow-ui:  ## Start MLflow tracking UI
	mlflow ui --host 0.0.0.0 --port 5000

# --- Frontend ---
frontend-install:  ## Install frontend dependencies
	cd frontend && npm install

frontend-dev:  ## Start React dev server
	cd frontend && npm run dev
