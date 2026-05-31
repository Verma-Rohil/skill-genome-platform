# Data Model Design Document
## Skill Genome Platform

---

## 1. Entity-Relationship Design (ERD)

The Skill Genome Platform uses a relational database schema designed to model the professional skill ecosystem, capture co-occurrence network metrics, map career archetypes, and log user-facing simulations.

The following **Mermaid diagram** illustrates the entities, columns, types, and their relationships:

```mermaid
erDiagram
    SKILL_CATEGORIES ||--o{ SKILLS : contains
    SKILLS ||--o{ JOB_SKILLS : mapped_in
    JOB_POSTINGS ||--o{ JOB_SKILLS : contains
    SKILLS ||--o{ SKILL_EMBEDDINGS : represented_by
    CAREER_ARCHETYPES ||--o{ ARCHETYPE_SKILLS : defines
    SKILLS ||--o{ ARCHETYPE_SKILLS : required_in
    SKILLS ||--o{ SKILL_COOCCURRENCES : "skill_a (source)"
    SKILLS ||--o{ SKILL_COOCCURRENCES : "skill_b (target)"

    SKILL_CATEGORIES {
        int id PK
        varchar name "unique"
        text description
        timestamp created_at
    }

    SKILLS {
        int id PK
        varchar canonical_name "unique"
        int category_id FK
        json aliases
        date first_seen_at
        timestamp created_at
    }

    SKILL_EMBEDDINGS {
        int id PK
        int skill_id FK "unique"
        blob vector "serialized numpy array"
        varchar model_version
        int dimension
        timestamp created_at
    }

    JOB_POSTINGS {
        int id PK
        varchar external_id
        varchar title
        varchar company_name
        text description
        varchar location
        varchar work_type
        varchar seniority_level
        date posted_date
        varchar source
        timestamp created_at
    }

    JOB_SKILLS {
        int id PK
        int job_id FK
        int skill_id FK
        boolean is_required
        float confidence
    }

    CAREER_ARCHETYPES {
        int id PK
        varchar name
        text description
        blob centroid_vector
        varchar model_version
        int num_jobs
        timestamp created_at
    }

    ARCHETYPE_SKILLS {
        int id PK
        int archetype_id FK
        int skill_id FK
        float importance_score
    }

    SKILL_COOCCURRENCES {
        int id PK
        int skill_a_id FK
        int skill_b_id FK
        int cooccurrence_count
        float support
        float confidence_a_b
        float confidence_b_a
        float lift
        float pmi
    }
```

---

## 2. Key Architecture Design Tradeoffs

### A. MySQL vs. Dedicated Vector Database (e.g., Pinecone/FAISS)
*   **Our Decision:** Store skill and centroid vectors as serialized byte strings (**BLOBs**) in MySQL and load them into a flat NumPy memory matrix at application startup.
*   **Why?** In a skill taxonomy, the vocabulary is relatively compact (typically ~800 to 2,000 canonical skills). Loading 1,000 vectors of size 384 (S-BERT) into memory takes less than 3 MB of RAM. 
*   **Tradeoff:** A dedicated Vector Database adds significant operational complexity, networking hops, and financial cost without providing any latency benefit at this scale. By using in-memory matrix operations (via NumPy) at runtime, we achieve sub-millisecond similarity searches ($<1\text{ms}$) while keeping the database stack simple and portable.

### B. Many-to-Many Job-Skill Mapping
*   **Our Decision:** Implement a junction table `job_skills` with unique constraints on the pair `(job_id, skill_id)` and a foreign key delete cascade.
*   **Why?** Normalizing skills out of job descriptions prevents massive data redundancy. Storing an extraction confidence score on this junction table allows us to filter out weak entity matches at runtime.

### C. Co-occurrence Network over Extrapolated Trends
*   **Our Decision:** Pivot from temporal trend snapshot tables to a structural pairwise synergy table (`skill_cooccurrences`).
*   **Why?** Future forecasting using Prophet on static 2024 data is logically flawed. The new design models structural co-occurrences (Support, Confidence, Lift, and Pointwise Mutual Information). This enables graph representation of skill dependencies and a **workforce disruption simulation engine** built on conditional probabilities $P(\text{Skill B} | \text{Skill A})$.

---

## 3. Data Integrity & Normalization Rules

1.  **First Normal Form (1NF):** All tables have a designated single-column Primary Key (`id`), and all column values are atomic (JSON column `aliases` acts as a controlled dictionary).
2.  **Second & Third Normal Form (2NF & 3NF):** Skills and job descriptions are fully isolated. Skill categories are normalized to a separate table `skill_categories` instead of duplicating strings.
3.  **Referential Integrity Constraints:** All foreign keys utilize `ON DELETE CASCADE` strategies (e.g., deleting a job description automatically purges its junction matches in `job_skills`), except for `skills.category_id` which utilizes `ON DELETE SET NULL` to preserve canonical skills even if their category is deleted.
