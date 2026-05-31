# Data Dictionary Document
## Skill Genome Platform

---

## 1. Overview
This Data Dictionary provides an exhaustive schema definition for all tables, columns, data types, constraints, and structural storage formats utilized within the **Skill Genome Platform**. 

It serves as a reference for database administration, data engineering pipelines, and API integrations, illustrating production-grade data modeling standards.

---

## 2. Table Schemas & Column Definitions

### Table 1: `skill_categories`
Organizes canonical skills into high-level professional sectors.

| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| **id** | INT | PRIMARY KEY, AUTO_INCREMENT | Unique surrogate identifier for each category. |
| **name** | VARCHAR(100) | NOT NULL, UNIQUE | Standard sector name (e.g., `"Programming Languages"`, `"Cloud & DevOps"`). |
| **description** | TEXT | NULLABLE | Detailed description of what skills fall into this category. |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when the category was registered. |

---

### Table 2: `skills`
The core entity representing canonical, normalized skills in the genome.

| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| **id** | INT | PRIMARY KEY, AUTO_INCREMENT | Unique surrogate identifier for each skill. |
| **canonical_name** | VARCHAR(150) | NOT NULL, UNIQUE | Resolved, standardized skill name (e.g., `"Machine Learning"`, `"React"`). |
| **category_id** | INT | FK $\to$ `skill_categories(id)`, ON DELETE SET NULL | Sector classification of the skill. |
| **aliases** | JSON | NULLABLE | JSON Array of equivalent term variations (e.g. `["ml", "machine-learning", "Machine_Learning"]`). |
| **first_seen_at** | DATE | NULLABLE | The date of the oldest job posting containing this skill. Used to analyze technology emergence. |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when the skill was registered. |

---

### Table 3: `skill_embeddings`
Stores dense vector representations of skills for semantic proximity and recommendation metrics.

| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| **id** | INT | PRIMARY KEY, AUTO_INCREMENT | Unique surrogate identifier for each embedding. |
| **skill_id** | INT | FK $\to$ `skills(id)`, ON DELETE CASCADE, UNIQUE | Links directly to the canonical skill. |
| **vector** | BLOB | NOT NULL | Binary serialization (byte string) of a raw float32 NumPy array containing the skill's embedding. |
| **model_version** | VARCHAR(50) | NOT NULL | Version tag of the model that generated the vector (e.g., `"sbert_v1"`). |
| **dimension** | INT | NOT NULL | Dimension size of the vector (e.g., `384` for S-BERT). |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when the embedding was generated. |

---

### Table 4: `job_postings`
Stores raw text and metadata extracted from LinkedIn and Indeed datasets.

| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| **id** | INT | PRIMARY KEY, AUTO_INCREMENT | Unique surrogate identifier for each posting. |
| **external_id** | VARCHAR(100) | NULLABLE | Original identifier from the source Kaggle dataset (e.g., `"lk-100021"`). |
| **title** | VARCHAR(300) | NOT NULL | Full role title (e.g., `"Senior Machine Learning Engineer"`). Indexed (Prefix index: 100 chars). |
| **company_name** | VARCHAR(200) | NULLABLE | Name of the hiring organization. |
| **description** | TEXT | NULLABLE | Complete, unstructured job description text containing required skills. |
| **location** | VARCHAR(200) | NULLABLE | Job location (e.g., `"San Francisco, CA"`, `"Remote"`). |
| **work_type** | VARCHAR(50) | NULLABLE | Employment type (e.g., `"Remote"`, `"Hybrid"`, `"On-site"`). |
| **seniority_level**| VARCHAR(50) | NULLABLE | Experience tier (e.g., `"Entry-level"`, `"Mid-level"`, `"Senior-level"`, `"Lead"`). |
| **posted_date** | DATE | NULLABLE | Date the job was published. Indexed. |
| **source** | VARCHAR(50) | NULLABLE | Origin portal (e.g., `"linkedin"`, `"indeed"`). |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when the job posting was ingested. |

---

### Table 5: `job_skills`
Junction table resolving the many-to-many relationship between job postings and normalized skills.

| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| **id** | INT | PRIMARY KEY, AUTO_INCREMENT | Unique surrogate identifier. |
| **job_id** | INT | FK $\to$ `job_postings(id)`, ON DELETE CASCADE | Links to the specific job posting. |
| **skill_id** | INT | FK $\to$ `skills(id)`, ON DELETE CASCADE | Links to the canonical skill. |
| **is_required** | BOOLEAN | DEFAULT TRUE | Indicates if the skill is mandatory or optional. |
| **confidence** | FLOAT | DEFAULT 1.0 | NLP extraction confidence score (1.0 for exact dictionary matches; lower for NER inferences). |

*   *Composite Index:* Unique constraint `uk_job_skill (job_id, skill_id)`.

---

### Table 6: `career_archetypes`
Discovered career profiles representing natural skill clusters in the job market.

| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| **id** | INT | PRIMARY KEY, AUTO_INCREMENT | Unique surrogate identifier. |
| **name** | VARCHAR(150) | NOT NULL | Discovered profile label assigned during evaluation (e.g., `"ML Engineer"`). |
| **description** | TEXT | NULLABLE | Comprehensive summary describing the scope of this career archetype. |
| **centroid_vector**| BLOB | NULLABLE | Centroid coordinates representing the average skill vector of this cluster. Serialized numpy BLOB. |
| **model_version** | VARCHAR(50) | NOT NULL | Version of the clustering engine that generated the archetype (e.g., `"kmeans_v1"`). |
| **num_jobs** | INT | NULLABLE | Total job postings assigned to this cluster. |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when the archetype was calculated. |

---

### Table 7: `archetype_skills`
High-importance skills that structurally define each career archetype.

| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| **id** | INT | PRIMARY KEY, AUTO_INCREMENT | Unique surrogate identifier. |
| **archetype_id** | INT | FK $\to$ `career_archetypes(id)`, ON DELETE CASCADE | Links to the archetype. |
| **skill_id** | INT | FK $\to$ `skills(id)`, ON DELETE CASCADE | Links to the canonical skill. |
| **importance_score**| FLOAT | NOT NULL | Importance metric representing the TF-IDF weight or distance to cluster centroid of the skill in this cluster. |

---

### Table 8: `skill_cooccurrences`
Maintains structural co-occurrence correlation metrics between skills, powering the **Simulator**.

| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| **id** | INT | PRIMARY KEY, AUTO_INCREMENT | Unique surrogate identifier. |
| **skill_a_id** | INT | FK $\to$ `skills(id)`, ON DELETE CASCADE | First skill in the pairing. |
| **skill_b_id** | INT | FK $\to$ `skills(id)`, ON DELETE CASCADE | Second skill in the pairing. |
| **cooccurrence_count**| INT | NOT NULL | Absolute count of job postings containing both skills. |
| **support** | FLOAT | NOT NULL | Proportion of total job postings that contain both skills: $P(A \cap B)$. |
| **confidence_a_b** | FLOAT | NOT NULL | Conditional probability of skill B given skill A: $P(B \| A)$. |
| **confidence_b_a** | FLOAT | NOT NULL | Conditional probability of skill A given skill B: $P(A \| B)$. |
| **lift** | FLOAT | NOT NULL | Co-occurrence multiplier relative to random chance. Lift $> 1.0$ indicates positive synergy. |
| **pmi** | FLOAT | NOT NULL | Pointwise Mutual Information, representing mathematical semantic distance. |

*   *Composite Index:* Unique constraint `uk_skills_pair (skill_a_id, skill_b_id)`.

---

### Table 9: `ml_experiments`
Logs metadata and metrics from off-line ML training jobs to supplement MLflow audit traces.

| Column | Type | Constraints | Description |
|:---|:---|:---|:---|
| **id** | INT | PRIMARY KEY, AUTO_INCREMENT | Unique surrogate identifier. |
| **experiment_name**| VARCHAR(200) | NOT NULL | Unique audit run name (e.g., `"kmeans_clustering_2026-06"`). |
| **model_type** | VARCHAR(100) | NULLABLE | Engine class (e.g., `"sbert"`, `"kmeans"`, `"synergy_simulation"`). |
| **parameters** | JSON | NULLABLE | JSON Object mapping model parameters (e.g. `{"k": 8, "init": "k-means++"}`). |
| **metrics** | JSON | NULLABLE | JSON Object logging validation performance metrics (e.g. `{"silhouette": 0.45}`). |
| **artifact_path** | VARCHAR(500) | NULLABLE | Filepath to the logged model serialization pickle or matrix on disk. |
| **created_at** | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp when the training execution finished. |

---

## 3. Serialization Protocol (BLOB Schema)

Vector columns (`skill_embeddings.vector` and `career_archetypes.centroid_vector`) utilize binary serialization for fast standard ingestion.
- **Python Serialization:**
  ```python
  import numpy as np
  # Save to DB
  vector_bytes = np.array(embedding, dtype=np.float32).tobytes()
  # Load from DB
  vector = np.frombuffer(vector_bytes, dtype=np.float32)
  ```
- **Structure:** A continuous stream of raw float32 decimals (4 bytes per dimension). S-BERT dimension 384 corresponds to a BLOB of exactly $384 \times 4 = 1,536$ bytes.
