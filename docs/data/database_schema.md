# Database Schema Document
## Skill Genome Platform

---

## 1. SQL DDL Declarations

The following are the exact schema declarations executed on the MySQL instance (defined in [schema.sql](file:///c:/Project_2/skill-genome-platform/backend/data/scripts/schema.sql)).

```sql
-- ----- Skill Taxonomy -----
CREATE TABLE IF NOT EXISTS skill_categories (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS skills (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    canonical_name  VARCHAR(150) NOT NULL UNIQUE,
    category_id     INT,
    aliases         JSON,
    first_seen_at   DATE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES skill_categories(id)
        ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----- Embeddings -----
CREATE TABLE IF NOT EXISTS skill_embeddings (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    skill_id        INT NOT NULL UNIQUE,
    vector          BLOB NOT NULL,
    model_version   VARCHAR(50) NOT NULL,
    dimension       INT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (skill_id) REFERENCES skills(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----- Job Postings -----
CREATE TABLE IF NOT EXISTS job_postings (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    external_id     VARCHAR(100),
    title           VARCHAR(300) NOT NULL,
    company_name    VARCHAR(200),
    description     TEXT,
    location        VARCHAR(200),
    work_type       VARCHAR(50),
    seniority_level VARCHAR(50),
    posted_date     DATE,
    source          VARCHAR(50),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_posted_date (posted_date),
    INDEX idx_title (title(100))
) ENGINE=InnoDB;

-- ----- Job-Skill Mapping -----
CREATE TABLE IF NOT EXISTS job_skills (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    job_id      INT NOT NULL,
    skill_id    INT NOT NULL,
    is_required BOOLEAN DEFAULT TRUE,
    confidence  FLOAT DEFAULT 1.0,
    FOREIGN KEY (job_id) REFERENCES job_postings(id)
        ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id)
        ON DELETE CASCADE,
    UNIQUE KEY uk_job_skill (job_id, skill_id),
    INDEX idx_skill_id (skill_id)
) ENGINE=InnoDB;

-- ----- Career Archetypes -----
CREATE TABLE IF NOT EXISTS career_archetypes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    description     TEXT,
    centroid_vector  BLOB,
    model_version   VARCHAR(50) NOT NULL,
    num_jobs        INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS archetype_skills (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    archetype_id    INT NOT NULL,
    skill_id        INT NOT NULL,
    importance_score FLOAT NOT NULL,
    FOREIGN KEY (archetype_id) REFERENCES career_archetypes(id)
        ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

-- ----- Skill Co-occurrences -----
CREATE TABLE IF NOT EXISTS skill_cooccurrences (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    skill_a_id          INT NOT NULL,
    skill_b_id          INT NOT NULL,
    cooccurrence_count  INT NOT NULL,
    support             FLOAT NOT NULL,
    confidence_a_b      FLOAT NOT NULL,
    confidence_b_a      FLOAT NOT NULL,
    lift                FLOAT NOT NULL,
    pmi                 FLOAT NOT NULL,
    FOREIGN KEY (skill_a_id) REFERENCES skills(id)
        ON DELETE CASCADE,
    FOREIGN KEY (skill_b_id) REFERENCES skills(id)
        ON DELETE CASCADE,
    UNIQUE KEY uk_skills_pair (skill_a_id, skill_b_id),
    INDEX idx_lift (lift),
    INDEX idx_cooccurrence (cooccurrence_count)
) ENGINE=InnoDB;

-- ----- ML Experiments -----
CREATE TABLE IF NOT EXISTS ml_experiments (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    experiment_name VARCHAR(200) NOT NULL,
    model_type      VARCHAR(100),
    parameters      JSON,
    metrics         JSON,
    artifact_path   VARCHAR(500),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
```

---

## 2. Table & Column Dictionary

### Table: `skills`
Stores the curated, normalized taxonomy vocabulary.
*   `canonical_name`: The resolved standard name (e.g., `"Machine Learning"`).
*   `aliases`: JSON array containing pre-mapped extraction variations (e.g. `["ml", "machine-learning"]`).
*   `first_seen_at`: Dates the earliest job posting requiring this skill, helping track novelty.

### Table: `skill_embeddings`
Stores S-BERT model embeddings for semantic proximity checks.
*   `vector`: Serialized raw 384-dimension numpy float32 array stored as a binary BLOB.

### Table: `job_skills`
Junction table resolving many-to-many job postings and extracted skill connections.
*   `confidence`: Represents the extraction score (1.0 for dictionary taxonomy matches; variable for NER predictions).

### Table: `skill_cooccurrences`
Maintains structural correlation metrics between skills.
*   `lift`: Measures the synergy factor. A lift of $2.5$ means skills co-occur $2.5$ times more often than random chance.
*   `pmi`: Pointwise Mutual Information, used as a statistical semantic distance proxy in network graphs.

---

## 3. Query Indexing Optimizations

To guarantee low latency ($<500\text{ms}$ p95) under production load, we implemented targeted indexing constraints:

1.  **Composite Unique Keys (`uk_job_skill`, `uk_skills_pair`):**
    *   Prevents duplicate job-skill associations and duplicate skill-synergy rows.
    *   Implicitly builds a composite index, enabling fast lookups on pairs (e.g. checking if Python and PyTorch co-occur).
2.  **Partial Prefix Index (`idx_title` on `title(100)`):**
    *   Indexes only the first 100 characters of job titles. This avoids storing massive text prefixes in the index, keeping index footprints compact while maintaining $O(\log N)$ query speed for dashboard search queries.
3.  **Numerical Metrics Indices (`idx_lift`, `idx_cooccurrence`):**
    *   Allows the FastAPI service to perform extremely fast descending queries when returning top-synergy skills in real-time.
