# High-Level Architecture
## Skill Genome & Career Intelligence Platform

---

## 1. Architecture Overview

The Skill Genome Platform follows a **layered architecture** with clear separation of concerns. Each layer has a single responsibility and communicates only with adjacent layers.

```
┌──────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                           │
│                                                                  │
│   React (Vite)  ─────  D3.js / vis-network  ─────  Recharts     │
│   Dashboard            Skill Network Viz          Trend Charts   │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP (REST JSON)
┌──────────────────────────▼───────────────────────────────────────┐
│                       API LAYER                                  │
│                                                                  │
│   FastAPI  ─────  Pydantic Schemas  ─────  CORS Middleware       │
│   Routers         Request/Response         Auth (future)         │
│                   Validation                                     │
└──────────────────────────┬───────────────────────────────────────┘
                           │ Function calls
┌──────────────────────────▼───────────────────────────────────────┐
│                     SERVICE LAYER                                │
│                                                                  │
│   Skill Extractor ──── Normalizer ──── Embedding Engine          │
│   Similarity Engine ── Clustering ──── Gap Analyzer              │
│   Trend Analyzer ───── Recommender                               │
└──────────┬───────────────────────────────────────┬───────────────┘
           │ SQLAlchemy ORM                        │ File I/O
┌──────────▼───────────┐                ┌──────────▼───────────────┐
│    DATA LAYER        │                │    ML ARTIFACT LAYER     │
│                      │                │                          │
│   MySQL 8.x          │                │   Word2Vec models        │
│   - Skills           │                │   KMeans/HDBSCAN models  │
│   - Job Postings     │                │   Prophet models         │
│   - Embeddings       │                │   MLflow tracking        │
│   - Archetypes       │                │                          │
│   - Trends           │                │                          │
└──────────────────────┘                └──────────────────────────┘
```

---

## 2. Component Diagram

```
┌─ Frontend (React + Vite) ─────────────────────────────────────┐
│                                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │Dashboard │  │ Explorer │  │ Career   │  │ Trends   │      │
│  │  Page    │  │  Page    │  │ Intel    │  │  Page    │      │
│  └──────────┘  └──────────┘  │  Page    │  └──────────┘      │
│                               └──────────┘                     │
│  Shared: Navbar, SearchBar, Card, SkillNetwork (D3.js)        │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                     Axios / fetch
                           │
┌──────────────────────────▼─────────────────────────────────────┐
│  FastAPI Backend                                                │
│                                                                 │
│  ┌─ Routers ──────────────────────────────────────────────┐    │
│  │ /api/skills    /api/careers    /api/trends              │    │
│  │ /api/recommendations          /api/health               │    │
│  └────────────────────┬───────────────────────────────────┘    │
│                       │                                         │
│  ┌─ Services ─────────▼───────────────────────────────────┐    │
│  │                                                         │    │
│  │  SkillExtractor  ──▶  SkillNormalizer                   │    │
│  │       │                     │                           │    │
│  │       ▼                     ▼                           │    │
│  │  EmbeddingEngine ──▶  SimilarityEngine                  │    │
│  │       │                     │                           │    │
│  │       ▼                     ▼                           │    │
│  │  ClusteringEngine ──▶  GapAnalyzer                      │    │
│  │       │                     │                           │    │
│  │       ▼                     ▼                           │    │
│  │  TrendAnalyzer   ──▶  Recommender                       │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                       │                                         │
│  ┌─ Data ─────────────▼───────────────────────────────────┐    │
│  │ SQLAlchemy Models ──▶ MySQL                             │    │
│  │ ML Artifacts      ──▶ Disk / MLflow                     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow — End to End

```
Raw Job Posting (text)
    │
    ▼
[Skill Extractor] ─── spaCy NER + Dictionary ──▶ Raw skill list
    │
    ▼
[Skill Normalizer] ── Fuzzy match + Embedding similarity ──▶ Canonical skill IDs
    │
    ▼
[MySQL: job_skills] ── Persist mapping ──▶ job_id ↔ skill_id
    │
    ▼
[Embedding Engine] ── Word2Vec on skill co-occurrence ──▶ Skill vectors (100-dim)
    │
    ├──▶ [Similarity Engine] ── Cosine similarity ──▶ "Python is similar to Pandas"
    │
    ├──▶ [Clustering Engine] ── KMeans/HDBSCAN ──▶ Career archetypes
    │        │
    │        └──▶ [Gap Analyzer] ── User skills vs archetype ──▶ Skill gaps
    │
    ├──▶ [Trend Analyzer] ── Prophet on monthly counts ──▶ Emerging/declining skills
    │
    └──▶ [Recommender] ── Embedding proximity + trend + gap ──▶ "Learn MLOps next"
              │
              ▼
         [FastAPI] ──▶ [React Dashboard]
```

---

## 4. Key Architecture Decisions

| Decision | Choice | Why | Alternative | Why Not |
|:---|:---|:---|:---|:---|
| **Architecture Style** | Layered (Router → Service → Data) | Clear separation, testable, swappable layers | Microservices | Overkill for single-team project |
| **Communication** | REST API (JSON) | Universal, cacheable, well-tooled | GraphQL | Added complexity; REST sufficient for our query patterns |
| **Database** | MySQL 8.x | Widely used, JSON support, relational integrity | PostgreSQL | Either works; MySQL chosen per user requirement |
| **Embedding Storage** | MySQL BLOB + in-memory numpy | Simple; our scale (~2K skills) fits in RAM | Pinecone/FAISS | Unnecessary infra for small vocabulary |
| **ML Serving** | In-process (loaded at startup) | Low latency; no network hop for inference | Separate model server (TFServing) | Extra infra for simple cosine similarity |
| **Frontend-Backend** | Separate services (Vite :5173, FastAPI :8000) | Independent development, standard industry setup | Server-side rendering | React is richer for interactive dashboards |

---

## 5. Non-Functional Requirements

| Requirement | Target | Rationale |
|:---|:---|:---|
| **Latency** | API response < 500ms (p95) | Interactive dashboard feel |
| **Throughput** | 50 concurrent users | Sufficient for demo/portfolio |
| **Availability** | Not critical (portfolio project) | Local deployment acceptable |
| **Security** | CORS configured; no auth in v1 | Out of scope for v1 |
| **Scalability** | Vertical (bigger machine) | Horizontal scaling unnecessary at this scale |
| **Observability** | MLflow for ML; FastAPI logs for API | Sufficient for debugging |

---

## 6. Technology Stack Summary

| Layer | Technology | Version |
|:---|:---|:---|
| Frontend | React + Vite | React 18, Vite 5 |
| Visualization | D3.js, vis-network, Recharts | Latest |
| API | FastAPI | 0.115+ |
| Validation | Pydantic | 2.x |
| ORM | SQLAlchemy | 2.0+ |
| Database | MySQL | 8.x |
| NLP | spaCy | 3.x |
| Embeddings | gensim (Word2Vec) | 4.x |
| Clustering | scikit-learn, HDBSCAN | Latest |
| Forecasting | Prophet | 1.x |
| Experiment Tracking | MLflow | 2.x |
| Containerization | Docker + Docker Compose | Latest |
| CI/CD | GitHub Actions | N/A |

---

## 7. Interview Talking Points

### "Describe the architecture"
> "The platform uses a layered architecture — presentation (React), API (FastAPI), service (ML logic), and data (MySQL). Each service component (extractor, normalizer, embedding engine, etc.) is a standalone Python class injected into FastAPI routes. This means I can test the clustering engine independently of the API, or swap MySQL for PostgreSQL without changing business logic."

### "Why not microservices?"
> "For a single-developer project processing static data, microservices add complexity without benefit. The service layer already achieves separation of concerns. If this scaled to multiple teams, I'd split the embedding service and trend analyzer into separate deployable units."

### "How do you handle model updates?"
> "ML models are trained offline, logged to MLflow, and loaded at FastAPI startup. The `model_version` column in `skill_embeddings` and `career_archetypes` tracks which model produced each result. In production, I'd add A/B testing between model versions."
