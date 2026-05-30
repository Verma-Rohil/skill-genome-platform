# ML System Design
## Skill Genome Platform

---

## 1. System Overview

The ML layer is the intelligence core of the platform. It transforms raw job posting data into actionable career intelligence through 5 sequential stages:

```
Job Descriptions → [Extract] → [Normalize] → [Embed] → [Cluster] → [Recommend]
                     NLP         Fuzzy Match   S-BERT    KMeans      Multi-signal
                                               Embeddings HDBSCAN    Ranking
```

---

## 2. ML Pipeline Architecture

### Stage 1: Skill Extraction (NLP)

| Aspect | Detail |
|:---|:---|
| **Input** | Raw job description text |
| **Output** | List of extracted skill strings |
| **Method** | Dictionary matching + spaCy NER |
| **Offline/Online** | Both — batch for training data, online for API |
| **Key Metric** | Precision, Recall vs pre-extracted skills column |

### Stage 2: Skill Normalization

| Aspect | Detail |
|:---|:---|
| **Input** | Raw extracted skill strings |
| **Output** | Canonical skill IDs |
| **Method** | Exact match → Fuzzy match (rapidfuzz, threshold 0.85) → S-BERT cosine (threshold 0.90) |
| **Key Metric** | < 5% duplicate entities in skills table |

### Stage 3: Embedding Generation

| Aspect | Detail |
|:---|:---|
| **Input** | Canonical skill names + co-occurrence context |
| **Output** | Dense vectors (384-dim for S-BERT) |
| **Method** | **Sentence-BERT (all-MiniLM-L6-v2)** |
| **Why S-BERT** | Pre-trained on massive text corpus; captures semantic meaning; no training required; 384-dim embeddings are compact yet expressive |
| **Alternative** | Word2Vec trained on skill co-occurrence — more educational but lower quality for small vocabularies |
| **Storage** | MySQL BLOB (serialized numpy) + in-memory numpy matrix at runtime |
| **Key Metric** | Nearest-neighbor sanity: Python→Pandas ✅, Docker→Kubernetes ✅ |

> **INTERVIEW NOTE:** "I chose S-BERT because with ~1000 skills, training Word2Vec from scratch doesn't have enough co-occurrence data to learn meaningful embeddings. S-BERT gives us high-quality semantic vectors out of the box. However, I also computed co-occurrence-weighted adjustments to capture domain-specific relationships that S-BERT alone might miss."

### Stage 4: Clustering (Career Archetypes)

| Aspect | Detail |
|:---|:---|
| **Input** | Job posting vectors (average of constituent skill embeddings) |
| **Output** | Cluster labels + centroids + archetype names |
| **Method** | KMeans (baseline) + HDBSCAN (comparison) |
| **k Selection** | Elbow method + Silhouette analysis, expect 6-12 archetypes |
| **Labeling** | Manual inspection of top-10 skills per cluster → assign name |
| **Key Metric** | Silhouette score > 0.3, interpretable archetype names |

### Stage 5: Recommendation

| Aspect | Detail |
|:---|:---|
| **Input** | User's current skill set |
| **Output** | Ranked list of recommended next skills |
| **Method** | Multi-signal scoring: embedding proximity (0.4) + trend growth (0.3) + gap importance (0.3) |
| **Key Metric** | Recommendation relevance (qualitative review) |

---

## 3. Training vs Serving

| Concern | Training (Offline) | Serving (Online) |
|:---|:---|:---|
| **When** | Before deployment; re-run on new data | Per API request |
| **Compute** | Local CPU (no GPU needed) | In-process inference |
| **Latency** | Minutes to hours | < 200ms per request |
| **Artifacts** | S-BERT model (pre-trained), KMeans/HDBSCAN pickle, Prophet models | Loaded into memory at FastAPI startup |
| **Tracking** | MLflow logs all experiments | MLflow not involved at serving time |

---

## 4. Model Versioning Strategy

```
skill_embeddings.model_version = "sbert_v1"
career_archetypes.model_version = "kmeans_v1"
ml_experiments.experiment_name = "embedding_sbert_2026-06"
```

Every model artifact is:
1. **Logged in MLflow** — parameters, metrics, artifact files
2. **Tagged with version** — in the database tables that store results
3. **Reproducible** — training scripts are deterministic (fixed seeds)

---

## 5. Evaluation Strategy Overview

| Stage | Metric | Method |
|:---|:---|:---|
| Extraction | Precision, Recall | Compare vs Kaggle's pre-extracted skills |
| Normalization | Duplicate rate | Count unique vs total skills after normalization |
| Embeddings | Nearest-neighbor quality | Manual inspection of top-5 neighbors per skill |
| Clustering | Silhouette, Davies-Bouldin | scikit-learn metrics + human archetype labeling |
| Trends | Forecast MAPE | Back-test: train on months 1-9, predict months 10-12 |
| Recommendations | Relevance | Qualitative review ("Does Python→Pandas make sense?") |

---

## 6. Key Tradeoffs

| Tradeoff | Our Choice | Why |
|:---|:---|:---|
| S-BERT vs Word2Vec | S-BERT | Small vocabulary (~1K skills) → insufficient co-occurrence for Word2Vec |
| KMeans vs HDBSCAN | Both (compare) | KMeans = interpretable; HDBSCAN = handles noise. Show comparison in interview |
| MySQL vs Vector DB | MySQL + in-memory | ~1K skills fit in RAM. Vector DB adds unnecessary infra |
| Online vs Batch recommendations | Online (per-request) | Low latency; user experience priority |
| Prophet vs ARIMA | Prophet | Handles missing dates, automatic changepoints, uncertainty intervals |
