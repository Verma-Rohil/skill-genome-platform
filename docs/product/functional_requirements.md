# Functional Requirements Document (FRD)

## Skill Genome & Career Intelligence Platform

---

## 1. Introduction

### 1.1 Purpose

This document specifies the complete functional requirements for the **Skill Genome Platform** (v1.0). It outlines what the system must do to enable job seekers, career changers, and workforce planners to analyze skill taxonomies, explore career archetypes, map skill synergies, and run technology disruption simulations.

### 1.2 Target Audience

This document is designed for the product management, engineering, data science, and QA teams, and serves as an industry-grade portfolio artifact demonstrating systematic product design.

---

## 2. Functional Architecture & System Modules

The platform is divided into 6 core functional modules, orchestrated via a layered backend (FastAPI) and a visual interface (React):

```
┌────────────────────────────────────────────────────────┐
│                   React Dashboard (UI)                 │
└───────────▲────────────────────────────────▲───────────┘
            │ API (REST JSON)                │
┌───────────▼────────────────────────────────▼───────────┐
│                    FastAPI Gateway                     │
└───────────▲────────────────────────────────▲───────────┘
            │ Function calls                 │
┌───────────▼────────────────────────────────▼───────────┐
│                    SERVICE LAYER (ML)                  │
│                                                        │
│  [Skill Extractor]   ──▶   [Skill Normalizer]          │
│         │                         │                    │
│         ▼                         ▼                    │
│  [Embedding Engine]  ──▶   [Clustering Engine]         │
│         │                         │                    │
│         ▼                         ▼                    │
│  [Synergy & Simulator] ──▶ [Recommendation Engine]     │
└───────────▲────────────────────────────────▲───────────┘
            │ SQLAlchemy ORM                 │
┌───────────▼────────────────────────────────▼───────────┐
│                   MySQL Data Persistence               │
└────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Functional Requirements

### Module 1: Skill Extraction (NLP)

* **FR-1.1: Trie-Based Dictionary Extraction**
  * The system MUST extract professional skills from unstructured job description text using a high-performance Trie-based word-level Prefix Tree matcher.
  * The extraction lookup time MUST scale at $O(W \times L)$ (linear in text length), independent of the dictionary vocabulary size.
* **FR-1.2: Greedy Longest-Match Resolution**
  * The Trie matcher MUST perform longest-match lookahead to prioritize multi-word skills over single-word components (e.g., extracting "Machine Learning" rather than splitting it into "Machine" and "Learning").
* **FR-1.3: Specialized Alphanumeric Preservation**
  * The tokenization engine MUST retain punctuation for technical terms (e.g., `C++`, `C#`, `.js`, `Next.js`, `.NET`) and prevent standard NLP cleaning from stripping them.
* **FR-1.4: Multi-Tier Taxonomy Fallback**
  * The extractor MUST load taxonomy terms and aliases from the MySQL database if active; if the database is unreachable, it MUST automatically fall back to loading from a local `skills_taxonomy.csv` file.

### Module 2: Skill Normalization

* **FR-2.1: Exact & Alias Matching**
  * The system MUST resolve raw extracted terms to their canonical names using pre-compiled alias mappings (e.g., resolving `py`, `python-lang` -> `Python`).
* **FR-2.2: Levenshtein Fuzzy Normalization**
  * If no exact match is found, the system MUST compute Levenshtein distance similarity. If the similarity score is $\ge 0.85$, it MUST resolve the term to the high-match canonical skill.
* **FR-2.3: Semantic Cosine Normalization**
  * If Levenshtein similarity falls below $0.85$, the system MUST calculate the Sentence-BERT cosine similarity between the term and canonical skills. If cosine similarity is $\ge 0.90$, it MUST normalize the term.

### Module 3: Career Archetype Clustering

* **FR-3.1: Job Representation Vectorization**
  * The system MUST represent each job posting as a dense vector calculated by averaging the Sentence-BERT embeddings of its constituent skills.
* **FR-3.2: Archetype Discovery via KMeans**
  * The system MUST cluster job vectors using the KMeans algorithm to discover natural career profiles (e.g., "ML Engineer", "Data Analyst").
  * The system MUST evaluate optimal clusters ($k$) using Silhouette Analysis and the Elbow Method.
* **FR-3.3: Skill Centroid Importance Ranking**
  * For each career archetype, the system MUST calculate the importance score of each skill based on its distance to the cluster centroid and frequency in the cluster.

### Module 4: Skill Synergy Network & Market Simulator

* **FR-4.1: Pairwise Skill Association Mining**
  * The system MUST scan all job postings to calculate co-occurrence statistics between skill pairs, including:
    * **Support:** $P(A \cap B)$
    * **Confidence:** $P(B | A)$ and $P(A | B)$
    * **Lift:** $\frac{P(A \cap B)}{P(A) \cdot P(B)}$
    * **Pointwise Mutual Information (PMI):** $\log\left(\frac{P(A \cap B)}{P(A) \cdot P(B)}\right)$
* **FR-4.2: Tech-Disruption Propagation Simulator**
  * The system MUST simulate localized technology shocks (e.g., a $+50\%$ spike in "Generative AI" adoption).
  * The system MUST calculate how this shock propagates through the skill network using conditional probabilities $P(\text{Skill B} | \text{Skill A})$ to compute secondary demand shocks on adjacent skills.
* **FR-4.3: Archetype Disruption Sensitivity**
  * The system MUST calculate a **Vulnerability Score** for each career archetype under active simulated shocks, ranking which profiles are most disrupted.

### Module 5: Recommendation Engine

* **FR-5.1: Skill Gap Prioritization**
  * The system MUST analyze the gap between a user's current skill profile and their target career archetype centroid.
  * Missing skills MUST be ranked based on their centroid importance score.
* **FR-5.2: Multi-Signal Score Blending**
  * The recommendation engine MUST suggest adjacent skills by blending three normalized signals:
    1. **Embedding Proximity (0.4 weight):** Semantic similarity of candidates to current skills.
    2. **Skill Synergy Index (0.3 weight):** Graph lift and PMI co-occurrence scores.
    3. **Centroid Gap Priority (0.3 weight):** High-importance missing skills for the target archetype.
* **FR-5.3: Recommendation Explainability**
  * Every recommended skill MUST include structured logic reasons (e.g., "Highly co-occurs with your skill: React (+40% lift)", "Crucial gap for target: ML Engineer").

### Module 6: API Gateway & User Interface

* **FR-6.1: REST API Layer**
  * The system MUST expose all services via FastAPI routers, validated with Pydantic request/response schemas.
* **FR-6.2: Interactive React Dashboard**
  * The frontend MUST deliver 4 responsive visual pages:
    1. **Dashboard:** Core overview stats and highest vulnerability indexes.
    2. **Explorer:** Text-extraction playground, exact searches, and interactive D3.js/vis-network skill relationship graphs.
    3. **Career Intel:** Target profile selectors, radar charts for skill gaps, and explainable recommendations.
    4. **Disruption Simulator:** Multi-skill shock sliders, propagated impact heatmaps, and archetype sensitivity tables.
