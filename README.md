# 🧬 Skill Genome & Career Intelligence Platform

> A data-driven career intelligence system that models the professional skill ecosystem using NLP, embeddings, and clustering — revealing hidden relationships between skills, discovering career archetypes, and delivering personalized upskilling recommendations.

---

## 🎯 What This Does

| Feature | Description |
|:---|:---|
| **Skill Extraction** | NLP pipeline extracts skills from 100K+ job descriptions |
| **Skill Embeddings** | Word2Vec learns skill relationships from co-occurrence patterns |
| **Career Archetypes** | Clustering discovers natural career profiles (ML Engineer, Data Analyst, etc.) |
| **Skill Gap Analysis** | Compares your skills to career archetypes and identifies what's missing |
| **Trend Forecasting** | Prophet models track rising and declining skills over time |
| **Recommendations** | Multi-signal engine suggests the best next skills to learn |
| **Interactive Dashboard** | React UI with skill explorer, career pathways, and trend charts |

---

## 🏗️ Architecture

```
React Dashboard ──── FastAPI ──── Services Layer ──── MySQL + ML Artifacts
    (Vite)           (REST)       (NLP, Embeddings,    (Persistence)
                                   Clustering, etc.)
```

> **Design Philosophy:** Embedding-native intelligence with graph visualization only for exploration. No graph algorithms power the core logic — all intelligence comes from vector similarity, clustering, and time-series analysis.

---

## 🛠️ Tech Stack

| Layer | Technology |
|:---|:---|
| Frontend | React 18 + Vite, D3.js, vis-network |
| Backend | Python, FastAPI |
| NLP | spaCy, Sentence Transformers |
| ML | scikit-learn, HDBSCAN, gensim (Word2Vec), Prophet |
| Database | MySQL 8.x |
| MLOps | MLflow, Docker, GitHub Actions |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/skill-genome-platform.git
cd skill-genome-platform

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# 3. Database
mysql -u root -p < data/scripts/schema.sql

# 4. Environment
cp .env.example .env
# Edit .env with your MySQL credentials

# 5. Run API
uvicorn app.main:app --reload --port 8000

# 6. Frontend (separate terminal)
cd ../frontend
npm install
npm run dev
```

---

## 📊 Project Structure

```
skill-genome-platform/
├── docs/              # 30+ design & learning documents
├── backend/           # FastAPI + ML pipeline
│   ├── app/           # Application code (models, services, API)
│   ├── data/          # Data ingestion & processing
│   ├── ml/            # Training scripts & model artifacts
│   └── tests/         # Automated tests
├── frontend/          # React + Vite dashboard
├── mlops/             # Docker, CI/CD, MLflow config
└── notebooks/         # Exploration & prototyping
```

---

## 📈 Results

> _Results will be populated as each phase is completed._

| Metric | Value |
|:---|:---|
| Skills Extracted | _TBD_ |
| Embedding Quality (nearest-neighbor accuracy) | _TBD_ |
| Career Archetypes Discovered | _TBD_ |
| Trend Forecast MAPE | _TBD_ |

---

## 📚 Documentation

This project includes comprehensive documentation across 5 domains:

- **Product:** PRD, User Stories, Success Metrics
- **Architecture:** System Design, Data Flow, Component Interaction
- **Data:** Schema, Data Dictionary, Feature Store
- **ML:** Embedding Design, Clustering Design, Evaluation Strategy
- **Learning:** Concept Notes, Tradeoff Analysis, Interview Prep

See the [docs/](docs/) directory for all documents.

---

## 🎓 Built As

A production-inspired portfolio project for a **Data Science (DS1) fresher role**, demonstrating:
- End-to-end ML pipeline (data → model → API → dashboard)
- NLP, embeddings, clustering, time-series analysis
- Feature engineering & statistical thinking
- System design & architecture
- MLOps (experiment tracking, containerization, CI/CD)
- Product thinking & interview readiness

---

## 📄 License

MIT
