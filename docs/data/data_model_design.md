# Data Model Design Document

## Skill Genome Platform

---

## 1. Entity-Relationship Design (ERD)

The Skill Genome Platform uses a relational database schema designed to model the professional skill ecosystem, capture co-occurrence network metrics, map career archetypes, and log user-facing simulations.

The following **Mermaid diagram** illustrates the entities, columns, types, and their relationships:

```mermaid
graph TD
    CATEGORIES["<b>SKILL_CATEGORIES</b><br/>───────────<br/>id INT PK<br/>name VARCHAR<br/>description TEXT<br/>created_at TIMESTAMP"]
  
    SKILLS["<b>SKILLS</b><br/>───────────<br/>id INT PK<br/>canonical_name VARCHAR<br/>category_id INT FK<br/>aliases JSON<br/>first_seen_at DATE<br/>created_at TIMESTAMP"]
  
    EMBEDDINGS["<b>SKILL_EMBEDDINGS</b><br/>───────────<br/>id INT PK<br/>skill_id INT FK<br/>vector BLOB<br/>model_version VARCHAR<br/>dimension INT<br/>created_at TIMESTAMP"]
  
    JOBS["<b>JOB_POSTINGS</b><br/>───────────<br/>id INT PK<br/>external_id VARCHAR<br/>title VARCHAR<br/>company_name VARCHAR<br/>description TEXT<br/>location VARCHAR<br/>work_type VARCHAR<br/>seniority_level VARCHAR<br/>posted_date DATE<br/>source VARCHAR<br/>created_at TIMESTAMP"]
  
    JOB_SKILL["<b>JOB_SKILLS</b><br/>───────────<br/>id INT PK<br/>job_id INT FK<br/>skill_id INT FK<br/>is_required BOOLEAN<br/>confidence FLOAT"]
  
    ARCHETYPES["<b>CAREER_ARCHETYPES</b><br/>───────────<br/>id INT PK<br/>name VARCHAR<br/>description TEXT<br/>centroid_vector BLOB<br/>model_version VARCHAR<br/>num_jobs INT<br/>created_at TIMESTAMP"]
  
    ARCH_SKILLS["<b>ARCHETYPE_SKILLS</b><br/>───────────<br/>id INT PK<br/>archetype_id INT FK<br/>skill_id INT FK<br/>importance_score FLOAT"]
  
    COOCCUR["<b>SKILL_COOCCURRENCES</b><br/>───────────<br/>id INT PK<br/>skill_a_id INT FK<br/>skill_b_id INT FK<br/>cooccurrence_count INT<br/>support FLOAT<br/>confidence_a_b FLOAT<br/>confidence_b_a FLOAT<br/>lift FLOAT<br/>pmi FLOAT"]

    CATEGORIES -->|contains| SKILLS
    SKILLS -->|mapped in| JOB_SKILL
    JOBS -->|contains| JOB_SKILL
    SKILLS -->|represented by| EMBEDDINGS
    ARCHETYPES -->|defines| ARCH_SKILLS
    SKILLS -->|required in| ARCH_SKILLS
    SKILLS -->|skill a source| COOCCUR
    SKILLS -->|skill b target| COOCCUR

    style CATEGORIES fill:#7C3AED,color:#fff,stroke:#7C3AED
    style SKILLS fill:#3B82F6,color:#fff,stroke:#3B82F6
    style EMBEDDINGS fill:#10B981,color:#fff,stroke:#10B981
    style JOBS fill:#F59E0B,color:#fff,stroke:#F59E0B
    style JOB_SKILL fill:#F59E0B,color:#fff,stroke:#F59E0B
    style ARCHETYPES fill:#EF4444,color:#fff,stroke:#EF4444
    style ARCH_SKILLS fill:#EF4444,color:#fff,stroke:#EF4444
    style COOCCUR fill:#3B82F6,color:#fff,stroke:#3B82F6
```

---

## 2. Key Architecture Design Tradeoffs

### A. MySQL vs. Dedicated Vector Database (e.g., Pinecone/FAISS)

* **Our Decision:** Store skill and centroid vectors as serialized byte strings (**BLOBs**) in MySQL and load them into a flat NumPy memory matrix at application startup.
* **Why?** In a skill taxonomy, the vocabulary is relatively compact (typically ~800 to 2,000 canonical skills). Loading 1,000 vectors of size 384 (S-BERT) into memory takes less than 3 MB of RAM.
* **Tradeoff:** A dedicated Vector Database adds significant operational complexity, networking hops, and financial cost without providing any latency benefit at this scale. By using in-memory matrix operations (via NumPy) at runtime, we achieve sub-millisecond similarity searches ($<1\text{ms}$) while keeping the database stack simple and portable.

### B. Many-to-Many Job-Skill Mapping

* **Our Decision:** Implement a junction table `job_skills` with unique constraints on the pair `(job_id, skill_id)` and a foreign key delete cascade.
* **Why?** Normalizing skills out of job descriptions prevents massive data redundancy. Storing an extraction confidence score on this junction table allows us to filter out weak entity matches at runtime.

### C. Co-occurrence Network over Extrapolated Trends

* **Our Decision:** Pivot from temporal trend snapshot tables to a structural pairwise synergy table (`skill_cooccurrences`).
* **Why?** Future forecasting using Prophet on static 2024 data is logically flawed. The new design models structural co-occurrences (Support, Confidence, Lift, and Pointwise Mutual Information). This enables graph representation of skill dependencies and a **workforce disruption simulation engine** built on conditional probabilities $P(\text{Skill B} | \text{Skill A})$.

---

## 3. Data Integrity & Normalization Rules

1. **First Normal Form (1NF):** All tables have a designated single-column Primary Key (`id`), and all column values are atomic (JSON column `aliases` acts as a controlled dictionary).
2. **Second & Third Normal Form (2NF & 3NF):** Skills and job descriptions are fully isolated. Skill categories are normalized to a separate table `skill_categories` instead of duplicating strings.
3. **Referential Integrity Constraints:** All foreign keys utilize `ON DELETE CASCADE` strategies (e.g., deleting a job description automatically purges its junction matches in `job_skills`), except for `skills.category_id` which utilizes `ON DELETE SET NULL` to preserve canonical skills even if their category is deleted.
